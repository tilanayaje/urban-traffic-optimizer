"""
pygad_optimizer.py
Runs the Genetic Algorithm using PyGAD to optimize traffic signal
timings across the SUMO network defined in config.py.

Key architecture decisions:
  - fitness_func defined at module top level (required for Windows
    multiprocessing pickling — closures cannot be pickled)
  - 12 parallel SUMO workers evaluate the full population simultaneously,
    reducing per-generation time from ~120min to ~10-15min
  - File-based worker cache (worker_cache/) for inter-process results
  - best_result.json tracks best fitness so on_generation needs no
    extra re-simulation
  - Checkpoint/resume: saves population state after each generation
    so interrupted runs can continue from where they left off
"""

import os
import csv
import json
import multiprocessing
from pathlib import Path

import pygad
from eval_timings import evaluate, evaluate_worker, fitness, TL_IDS, N_INTERSECTIONS

# Import all constants from central config 
from config import (
    GREEN_MIN, GREEN_MAX,
    POP_SIZE, GENERATIONS, ALPHA,
    CACHE_DIR, CHECKPOINT_DIR, CHECKPOINT_FILE, GA_HISTORY_CSV,
)

# Derived constants 
# Total genes = 2 per intersection (phase A + phase B)
N_GENES    = N_INTERSECTIONS * 2

# Gene space: each gene is a continuous value in [GREEN_MIN, GREEN_MAX]
gene_space = [{"low": GREEN_MIN, "high": GREEN_MAX}] * N_GENES


# ============================================================
# CHECKPOINT HELPERS
# Saves/loads population state as plain JSON. 
# If theres an interruption at gen 13, 
# it restarts at where it left off and runs 7 more simulations.
# ============================================================

def save_checkpoint(generation: int, population: list, best_fitness: float):
    """
    Save current population state to checkpoints/checkpoint.json.

    Called at the end of every generation so any interruption
    loses at most one generation of work.

    Args:
        generation:   generations completed so far
        population:   list of 12 chromosomes (each a list of ints)
        best_fitness: best fitness score seen so far
    """
    CHECKPOINT_DIR.mkdir(exist_ok=True)
    checkpoint = {
        "generation":   generation,
        "population":   [list(map(int, chrom)) for chrom in population],
        "best_fitness": best_fitness,
    }
    CHECKPOINT_FILE.write_text(json.dumps(checkpoint, indent=2))
    print(f"[Checkpoint] Saved at generation {generation}")


def load_checkpoint() -> dict | None:
    """
    Load checkpoint from disk if one exists.

    Returns:
        dict with keys: generation, population, best_fitness
        None if no checkpoint exists
    """
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        checkpoint = json.loads(CHECKPOINT_FILE.read_text())
        print(f"[Checkpoint] Resuming from generation {checkpoint['generation']} "
              f"(best fitness so far: {checkpoint['best_fitness']:.2f})")
        return checkpoint
    except Exception as e:
        print(f"[Checkpoint] Failed to load checkpoint: {e}. Starting fresh.")
        return None


def clear_checkpoint():
    """
    Delete the checkpoint file after a successful run completes.
    This ensures the next run starts fresh rather than resuming.
    """
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print("[Checkpoint] Cleared — next run will start fresh.")


# ============================================================
# FITNESS FUNCTION
# Must be defined at module top level (not inside run_ga or any
# other function) so Python's multiprocessing can pickle it for
# dispatch to worker processes on Windows.
# ============================================================

def fitness_func(ga_instance, solution, solution_idx):
    """
    Evaluate one candidate timing plan by running a SUMO simulation.

    Called by PyGAD for every member of the population each generation.
    With parallel_processing=["process", 12], all 12 calls happen
    simultaneously in separate processes.

    Args:
        ga_instance:  PyGAD GA instance (provided by framework, not used directly)
        solution:     numpy array of gene values for this candidate
        solution_idx: index of this candidate in the population (0-11)

    Returns:
        float: fitness score (higher = better timing plan)
    """
    if solution_idx is None:
        solution_idx = 0

    genes = [int(x) for x in solution]
    args  = (solution_idx % POP_SIZE, genes, None)
    m     = evaluate_worker(args)
    f     = fitness(m, alpha=ALPHA)

    # Track best result seen this run:
    # best_result.json stores the metrics of the best simulation
    # so on_generation() can log without re-running anything.
    best_file = CACHE_DIR / "best_result.json"
    try:
        existing     = json.loads(best_file.read_text()) if best_file.exists() else None
        existing_fit = existing.get("_fitness", -1e18) if existing else -1e18
        if f > existing_fit:
            m["_fitness"] = f
            best_file.write_text(json.dumps(m))
    except Exception:
        # Non-fatal: logging failure should never crash the GA
        pass

    # Print compact summary showing first 3 intersections
    g = genes
    print(
        f"[GA] J_0_0=({g[0]},{g[1]}) J_1_0=({g[2]},{g[3]}) J_2_0=({g[4]},{g[5]}) ... | "
        f"arr={m['arrived_total']} wait={m['total_wait']:.0f} fit={f:.2f}"
    )
    return f

# ============================================================
# GENERATION CALLBACK
# Called by PyGAD after every generation completes.
# Logs results to ga_history.csv and saves a checkpoint.
# Does NOT re-run any simulation; reads from best_result.json.
# ============================================================

def on_generation(ga_instance):
    """
    Post-generation hook: log metrics and save checkpoint.

    PyGAD calls this after all 12 population members have been
    evaluated and the next generation's population has been selected.
    """
    generation    = ga_instance.generations_completed
    best_solution, best_fit, _ = ga_instance.best_solution(
        pop_fitness=ga_instance.last_generation_fitness
    )
    genes = [int(x) for x in best_solution]

    # ── Read metrics from cache (no extra simulation)
    best_file = CACHE_DIR / "best_result.json"
    try:
        metrics = json.loads(best_file.read_text())
    except Exception:
        # Fallback: only if cache is missing or corrupt
        print(f"[Log] Gen {generation}: cache miss, re-evaluating...")
        metrics = evaluate(genes, gui=False, verbose=False)

    throughput = metrics["arrived_total"]
    total_wait = metrics["total_wait"]
    avg_wait   = total_wait / throughput if throughput > 0 else 0.0

    print(f" >> [Log] Gen {generation}: fit={best_fit:.2f} "
          f"arrived={throughput} avg_wait={avg_wait:.1f}s")

    # Write to ga_history.csv 
    # Headers are built dynamically so this works for any network size
    tl_headers  = [f"green_{tl_id}_A" for tl_id in TL_IDS]
    tl_headers += [f"green_{tl_id}_B" for tl_id in TL_IDS]

    # Reorder genes to match headers: all A values then all B values
    genes_a = [genes[i * 2]     for i in range(N_INTERSECTIONS)]
    genes_b = [genes[i * 2 + 1] for i in range(N_INTERSECTIONS)]
    gene_row = genes_a + genes_b

    file_exists = GA_HISTORY_CSV.exists()
    with open(GA_HISTORY_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["generation", "fitness", "avg_waiting_time", "throughput"]
                + tl_headers
            )
        writer.writerow(
            [generation, best_fit, avg_wait, throughput] + gene_row
        )

    # Save checkpoint after every generation:
    # If the run is interrupted, the next run will resume from here
    # rather than restarting from generation 1.
    save_checkpoint(
        generation  = generation,
        population  = ga_instance.population.tolist(),
        best_fitness= best_fit,
    )

# MAIN RUN FUNCTION

def run_ga():
    """
    Initialize and run the GA, with checkpoint/resume support.

    On startup:
      - If a checkpoint exists: load saved population and resume
        from the next generation (remaining = GENERATIONS - completed)
      - If no checkpoint: start fresh with random initialization

    On completion:
      - Prints the final best solution
      - Clears the checkpoint (clean slate for next run)
      - Re-runs the best solution with SUMO-GUI for visualization
    """
    n_workers = min(POP_SIZE, multiprocessing.cpu_count())

    # Check for existing checkpoint 
    checkpoint = load_checkpoint()

    if checkpoint is not None:
        # Resume: use saved population as initial population
        completed          = checkpoint["generation"]
        generations_left   = GENERATIONS - completed
        initial_population = checkpoint["population"]

        if generations_left <= 0:
            print("[Checkpoint] Run already completed. Delete checkpoints/checkpoint.json to start fresh.")
            return

        print(f"[Config] Resuming from gen {completed} — "
              f"{generations_left} generations remaining")
        print(f"[Config] Workers: {n_workers}  Population: {POP_SIZE}  "
              f"Genes: {N_GENES}  Intersections: {N_INTERSECTIONS}")
    else:
        # Fresh start
        completed          = 0
        generations_left   = GENERATIONS
        initial_population = None

        print(f"[Config] Workers: {n_workers}  Population: {POP_SIZE}  "
              f"Generations: {GENERATIONS}  Genes: {N_GENES}  "
              f"Intersections: {N_INTERSECTIONS}")

        # Clear stale worker cache files from any previous run
        if CACHE_DIR.exists():
            for f in CACHE_DIR.glob("*.json"):
                f.unlink()

        # Delete old ga_history.csv so the new run starts clean
        if GA_HISTORY_CSV.exists():
            GA_HISTORY_CSV.unlink()

    # Build GA instance 
    ga_instance = pygad.GA(
        num_generations       = generations_left,
        num_parents_mating    = 6,
        sol_per_pop           = POP_SIZE,
        num_genes             = N_GENES,

        fitness_func          = fitness_func,  # must be top-level for pickling
        gene_space            = gene_space,

        # initial_population: None = random init, list = resume from checkpoint
        initial_population    = initial_population,

        parent_selection_type = "tournament",
        K_tournament          = 3,
        crossover_type        = "two_points",
        mutation_type         = "adaptive",
        mutation_percent_genes= [40, 10],   # 40% early, 10% late
        keep_elitism          = 3,           # always preserve top 3 solutions

        # parallel_processing: runs all POP_SIZE fitness evaluations
        # simultaneously using Python multiprocessing.
        # fitness_func MUST be picklable (top-level) for this to work on Windows.
        parallel_processing   = ["process", n_workers],

        save_best_solutions   = True,
        suppress_warnings     = True,
        on_generation         = on_generation,
    )

    # Run, then print final best solution
    ga_instance.run()
    best_solution, best_fit, _ = ga_instance.best_solution()
    genes = [int(x) for x in best_solution]

    print("\n========== FINAL BEST ==========")
    for i, tl_id in enumerate(TL_IDS):
        print(f"  {tl_id}: gA={genes[i*2]}s  gB={genes[i*2+1]}s")
    print(f"Fitness: {best_fit:.2f}")

    # Clear checkpoint — run completed successfully
    clear_checkpoint()

    # Visualize best solution in SUMO-GUI
    print("\nRe-running best solution with GUI...")
    evaluate(genes, gui=True, verbose=True)


# Entry point
if __name__ == "__main__":
    # freeze_support() is required on Windows when using multiprocessing.
    # Without it, each spawned worker re-executes this entire module on
    # startup, causing infinite recursive process spawning and an
    # immediate crash. Must be the first call in the if __name__ block.
    multiprocessing.freeze_support()
    run_ga()