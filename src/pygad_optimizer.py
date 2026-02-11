import os
import csv
import pygad
import random
from eval_timings import evaluate   # <-- existing function


# ============================================================
# LOGGING FUNCTION (Added for Dashboard)
# ============================================================
def on_generation(ga_instance):
    """
    Runs after every generation to save data for the Dashboard.
    """
    generation = ga_instance.generations_completed
    
    # 1. Get the best solution from this generation
    best_solution, best_fitness, _ = ga_instance.best_solution()
    gA = int(best_solution[0])
    gB = int(best_solution[1])

    # 2. Re-run evaluate() briefly to get the specific "Throughput" and "Wait" numbers.
    #    (The 'fitness' variable bundles them together, but the dashboard needs them separate).
    metrics = evaluate(gA, gB, gui=False, verbose=False)
    
    throughput = metrics["arrived_total"]
    total_wait = metrics["total_wait"]
    
    # Calculate Average Wait (Total Wait / Cars Arrived)
    avg_wait = total_wait / throughput if throughput > 0 else 0

    print(f" >> [Log] Gen {generation}: Saved to CSV (Fit: {best_fitness:.2f})")

    # 3. Write to CSV
    filename = "ga_history.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        # Write headers if it's a new file
        if not file_exists:
            writer.writerow(["generation", "fitness", "avg_waiting_time", "throughput", "green_north", "green_east"])
            
        writer.writerow([generation, best_fitness, avg_wait, throughput, gA, gB])

# ============================================================
# GLOBAL CONFIG (USE THESE) 
# ============================================================

TL_ID = "0"      # from your Traci.net.xml

GREEN_MIN = 10
GREEN_MAX = 80

POP_SIZE = 10
GENERATIONS = 8

ALPHA = 0.01  # wait penalty weight

# ============================================================
# FITNESS FUNCTION
# ============================================================

def fitness_func(ga_instance, solution, solution_idx):
    """
    solution = [gA, gB]
    """
    gA, gB = int(solution[0]), int(solution[1])

    metrics = evaluate(gA, gB, gui=False, verbose=False)

    arrived = metrics["arrived_total"]
    wait = metrics["total_wait"]

    fitness = arrived - ALPHA * wait

    print(
        f"[GA] gA={gA} gB={gB} "
        f"arr={arrived} wait={wait:.1f} "
        f"fitness={fitness:.2f}"
    )

    return fitness


# ============================================================
# GENE SPACE
# ============================================================

gene_space = [
    {"low": GREEN_MIN, "high": GREEN_MAX},  # gA
    {"low": GREEN_MIN, "high": GREEN_MAX},  # gB
]


# ============================================================
# GA INSTANCE
# ============================================================

ga_instance = pygad.GA(
    num_generations=GENERATIONS,
    num_parents_mating=4,
    sol_per_pop=POP_SIZE,
    num_genes=2,

    fitness_func=fitness_func,
    gene_space=gene_space,

    mutation_percent_genes=50,
    mutation_type="random",
    crossover_type="single_point",

    save_best_solutions=True,
    suppress_warnings=True,

    on_generation=on_generation
)


# ============================================================
# RUN
# ============================================================

def run_ga():
    ga_instance.run()

    best_solution, best_fitness, _ = ga_instance.best_solution()

    gA, gB = int(best_solution[0]), int(best_solution[1])

    print("\n========== FINAL BEST ==========")
    print("gA:", gA)
    print("gB:", gB)
    print("fitness:", best_fitness)

    print("\nRe-running best solution with GUI...")
    evaluate(gA, gB, gui=True, verbose=True)


if __name__ == "__main__":
    run_ga()
