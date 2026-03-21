import os
import csv
import json
import multiprocessing
from pathlib import Path
import pygad
from eval_timings import evaluate, evaluate_worker, fitness, TL_IDS, N_INTERSECTIONS

# ============================================================
# CONFIG
# ============================================================
GREEN_MIN   = 10
GREEN_MAX   = 80
POP_SIZE    = 12
GENERATIONS = 20       # more generations for larger search space
ALPHA       = 0.001

N_GENES   = N_INTERSECTIONS * 2   # 40 genes
CACHE_DIR = Path(__file__).resolve().parent.parent / "worker_cache"

# ============================================================
# GENE SPACE — 40 genes
# ============================================================
gene_space = [{"low": GREEN_MIN, "high": GREEN_MAX}] * N_GENES

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = os.environ.get("SUMO_MAP", "generated")
CSV_PATH = ROOT / "sumo_data" / MAP / "ga_history.csv"

# deletes existing csv for clarity
if CSV_PATH.exists():
    CSV_PATH.unlink()

# ============================================================
# FITNESS FUNCTION (top-level for pickling on Windows)
# ============================================================
def fitness_func(ga_instance, solution, solution_idx):
    if solution_idx is None:
        solution_idx = 0
    genes = [int(x) for x in solution]
    args  = (solution_idx % POP_SIZE, genes, None)
    m = evaluate_worker(args)
    f = fitness(m, alpha=ALPHA)

    # Persist best result seen so far to best_result.json
    best_file = CACHE_DIR / "best_result.json"
    try:
        existing     = json.loads(best_file.read_text()) if best_file.exists() else None
        existing_fit = existing.get("_fitness", -1e18) if existing else -1e18
        if f > existing_fit:
            m["_fitness"] = f
            best_file.write_text(json.dumps(m))
    except Exception:
        pass

    # Print compact summary (first 3 intersections only to keep output readable)
    g = genes
    print(
        f"[GA] J_0_0=({g[0]},{g[1]}) J_1_0=({g[2]},{g[3]}) J_2_0=({g[4]},{g[5]}) ... | "
        f"arr={m['arrived_total']} wait={m['total_wait']:.0f} fit={f:.2f}"
    )
    return f


# ============================================================
# LOGGING
# ============================================================
def on_generation(ga_instance):
    generation = ga_instance.generations_completed
    best_solution, best_fitness, _ = ga_instance.best_solution(
        pop_fitness=ga_instance.last_generation_fitness
    )
    genes = [int(x) for x in best_solution]

    # Read from best_result.json — no extra simulation needed
    best_file = CACHE_DIR / "best_result.json"
    try:
        metrics = json.loads(best_file.read_text())
    except Exception:
        metrics = None

    if metrics is None:
        print(f"[Log] Gen {generation}: cache miss, re-evaluating...")
        metrics = evaluate(genes, gui=False, verbose=False)

    throughput = metrics["arrived_total"]
    total_wait = metrics["total_wait"]
    avg_wait   = total_wait / throughput if throughput > 0 else 0.0

    print(f" >> [Log] Gen {generation}: fit={best_fitness:.2f} "
          f"arrived={throughput} avg_wait={avg_wait:.1f}s")

    filename    = "ga_history.csv"
    file_exists = os.path.isfile(filename)

    # Build header and row dynamically for N intersections
    tl_headers = []
    for tl_id in TL_IDS:
        tl_headers += [f"green_{tl_id}_A", f"green_{tl_id}_B"]

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["generation", "fitness", "avg_waiting_time", "throughput"] + tl_headers
            )
        writer.writerow(
            [generation, best_fitness, avg_wait, throughput] + genes
        )


# ============================================================
# RUN
# ============================================================
def run_ga():
    n_workers = min(POP_SIZE, multiprocessing.cpu_count())
    print(f"[Config] Workers: {n_workers}  Population: {POP_SIZE}  "
          f"Generations: {GENERATIONS}  Genes: {N_GENES}  "
          f"Intersections: {N_INTERSECTIONS}")

    # Clear stale cache
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()

    ga_instance = pygad.GA(
        num_generations       = GENERATIONS,
        num_parents_mating    = 6,
        sol_per_pop           = POP_SIZE,
        num_genes             = N_GENES,

        fitness_func          = fitness_func,
        gene_space            = gene_space,

        parent_selection_type = "tournament",
        K_tournament          = 3,
        crossover_type        = "two_points",
        mutation_type         = "adaptive",
        mutation_percent_genes= [40, 10],
        keep_elitism          = 3,

        parallel_processing   = ["process", n_workers],

        save_best_solutions   = True,
        suppress_warnings     = True,
        on_generation         = on_generation,
    )

    ga_instance.run()

    best_solution, best_fitness, _ = ga_instance.best_solution()
    genes = [int(x) for x in best_solution]

    print("\n========== FINAL BEST ==========")
    for i, tl_id in enumerate(TL_IDS):
        print(f"  {tl_id}: gA={genes[i*2]}s  gB={genes[i*2+1]}s")
    print(f"Fitness: {best_fitness:.2f}")

    print("\nRe-running best solution with GUI...")
    evaluate(genes, gui=True, verbose=True)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_ga()