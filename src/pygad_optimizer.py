import os
import csv
import json
import multiprocessing
from pathlib import Path
import pygad
from eval_timings import evaluate, evaluate_worker, fitness, port_for_index

# ============================================================
# CONFIG
# ============================================================
GREEN_MIN   = 10
GREEN_MAX   = 80
POP_SIZE    = 12
GENERATIONS = 10
ALPHA       = 0.01

CACHE_DIR = Path(__file__).resolve().parent.parent / "worker_cache"

# ============================================================
# GENE SPACE
# ============================================================
gene_space = [{"low": GREEN_MIN, "high": GREEN_MAX}] * 6


# ============================================================
# FITNESS FUNCTION (top-level so it can be pickled on Windows)
# ============================================================
def fitness_func(ga_instance, solution, solution_idx):
    if solution_idx is None:
        solution_idx = 0
    gA1, gB1, gA2, gB2, gA3, gB3 = [int(x) for x in solution]
    args = (solution_idx % POP_SIZE, gA1, gB1, gA2, gB2, gA3, gB3, None)
    m = evaluate_worker(args)
    f = fitness(m, alpha=ALPHA)
    print(
        f"[GA] J1=({gA1},{gB1}) J2=({gA2},{gB2}) J3=({gA3},{gB3}) | "
        f"arr={m['arrived_total']} wait={m['total_wait']:.1f} fit={f:.2f}"
    )
    return f


# ============================================================
# LOGGING — reads from file cache, zero extra simulation
# ============================================================
def on_generation(ga_instance):
    generation = ga_instance.generations_completed
    best_solution, best_fitness, _ = ga_instance.best_solution(
        pop_fitness=ga_instance.last_generation_fitness
    )

    gA1, gB1, gA2, gB2, gA3, gB3 = [int(x) for x in best_solution]

    # Search worker cache files for matching result
    metrics = None
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                with open(cache_file) as f:
                    m = json.load(f)
                if (m["gA1"] == gA1 and m["gB1"] == gB1 and
                    m["gA2"] == gA2 and m["gB2"] == gB2 and
                    m["gA3"] == gA3 and m["gB3"] == gB3):
                    metrics = m
                    break
            except Exception:
                continue

    if metrics is None:
        print(f"[Log] Gen {generation}: cache miss, re-evaluating best solution...")
        metrics = evaluate(gA1, gB1, gA2, gB2, gA3, gB3, gui=False, verbose=False)

    throughput = metrics["arrived_total"]
    total_wait = metrics["total_wait"]
    avg_wait   = total_wait / throughput if throughput > 0 else 0.0

    print(f" >> [Log] Gen {generation}: fit={best_fitness:.2f} "
          f"arrived={throughput} avg_wait={avg_wait:.1f}s")

    filename    = "ga_history.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "generation", "fitness",
                "avg_waiting_time", "throughput",
                "green_J1_A", "green_J1_B",
                "green_J2_A", "green_J2_B",
                "green_J3_A", "green_J3_B",
            ])
        writer.writerow([
            generation, best_fitness,
            avg_wait, throughput,
            gA1, gB1, gA2, gB2, gA3, gB3,
        ])


# ============================================================
# RUN
# ============================================================
def run_ga():
    n_workers = min(POP_SIZE, multiprocessing.cpu_count())
    print(f"[Config] Workers: {n_workers}  Population: {POP_SIZE}  Generations: {GENERATIONS}")

    # Clear stale cache files from previous runs
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()

    ga_instance = pygad.GA(
        num_generations       = GENERATIONS,
        num_parents_mating    = 6,
        sol_per_pop           = POP_SIZE,
        num_genes             = 6,

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
    gA1, gB1, gA2, gB2, gA3, gB3 = [int(x) for x in best_solution]

    print("\n========== FINAL BEST ==========")
    print(f"J1: gA={gA1}s  gB={gB1}s")
    print(f"J2: gA={gA2}s  gB={gB2}s")
    print(f"J3: gA={gA3}s  gB={gB3}s")
    print(f"Fitness: {best_fitness:.2f}")

    print("\nRe-running best solution with GUI...")
    evaluate(gA1, gB1, gA2, gB2, gA3, gB3, gui=True, verbose=True)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_ga()