"""
baseline.py
Compares SUMO's default fixed-timing plan against the GA-optimized
solution across N independent simulation runs with different seeds.

Runs each condition N_RUNS times, then performs Welch's t-test on
the avg_wait distributions to confirm statistical significance.

Usage:
    py src/baseline.py

Prerequisites:
    - GA run must be complete (ga_history.csv must exist)
    - Run from the project root directory
"""

import sys
import csv
from pathlib import Path
from scipy import stats

# Add src to path 
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Import constants from central config
from config import (
    BASELINE_PHASE, N_RUNS, ALPHA,
    GA_HISTORY_CSV, COMPARISON_CSV,
)
from eval_timings import evaluate, fitness, TL_IDS, N_INTERSECTIONS


# ============================================================
# LOAD BEST GA SOLUTION
# ============================================================

def load_best_ga_genes() -> list:
    """
    Read the row with the highest fitness from ga_history.csv
    and reconstruct the gene list.

    Returns:
        list of 2*N_INTERSECTIONS ints — the best timing plan found
    """
    if not GA_HISTORY_CSV.exists():
        raise FileNotFoundError(
            f"ga_history.csv not found at {GA_HISTORY_CSV}\n"
            f"Run pygad_optimizer.py first."
        )

    best_row = None
    best_fit = -1e18

    with open(GA_HISTORY_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fit = float(row["fitness"])
            if fit > best_fit:
                best_fit = fit
                best_row = row

    if best_row is None:
        raise ValueError("ga_history.csv is empty.")

    # Reconstruct gene list from column headers
    genes = []
    for tl_id in TL_IDS:
        genes.append(int(float(best_row[f"green_{tl_id}_A"])))
        genes.append(int(float(best_row[f"green_{tl_id}_B"])))

    print(f"[Baseline] Best GA solution loaded: fitness={best_fit:.2f}")
    print(f"           First 3 intersections: "
          f"{TL_IDS[0]}=({genes[0]},{genes[1]}) "
          f"{TL_IDS[1]}=({genes[2]},{genes[3]}) "
          f"{TL_IDS[2]}=({genes[4]},{genes[5]})")
    return genes

# RUN ONE CONDITION

def run_condition(label: str, genes: list, n_runs: int) -> list:
    """
    Run the same timing plan N times with different random seeds.

    Must use multiple seeds for statistical validity.
    without seed variation, every run produces identical results,
    and the t-test has no statistical power.

    Args:
        label:  condition label ("Baseline" or "GA_Optimized")
        genes:  flat list of green phase durations
        n_runs: number of independent runs

    Returns:
        list of result dicts, one per run
    """
    results = []
    for i in range(n_runs):
        seed = 42 + i   # deterministic seeds for reproducibility
        print(f"[{label}] Run {i+1}/{n_runs} (seed={seed}) ...")

        m        = evaluate(genes, gui=False, verbose=False, seed=seed)
        f        = fitness(m, alpha=ALPHA)
        avg_wait = m["total_wait"] / m["arrived_total"] if m["arrived_total"] > 0 else 0

        results.append({
            "condition":  label,
            "run":        i + 1,
            "fitness":    f,
            "avg_wait":   avg_wait,
            "throughput": m["arrived_total"],
            "total_wait": m["total_wait"],
            "avg_speed":  m["avg_speed"],
        })
        print(f"  -> avg_wait={avg_wait:.2f}s  "
              f"throughput={m['arrived_total']}  fitness={f:.2f}")
    return results

# STATISTICAL ANALYSIS

def summarize(label: str, results: list):
    """Print summary statistics for one condition."""
    waits       = [r["avg_wait"]   for r in results]
    throughputs = [r["throughput"] for r in results]
    fitnesses   = [r["fitness"]    for r in results]

    print(f"\n--- {label} ({len(results)} runs) ---")
    print(f"  Avg Wait:   mean={sum(waits)/len(waits):.2f}s  "
          f"min={min(waits):.2f}s  max={max(waits):.2f}s")
    print(f"  Throughput: mean={sum(throughputs)/len(throughputs):.1f}  "
          f"min={min(throughputs)}  max={max(throughputs)}")
    print(f"  Fitness:    mean={sum(fitnesses)/len(fitnesses):.2f}  "
          f"min={min(fitnesses):.2f}  max={max(fitnesses):.2f}")


def t_test(baseline_results: list, ga_results: list):
    """
    Welch's t-test on avg_wait between baseline and GA conditions.
    Welch's is used because it does not assume equal variance between the two conditions.
    Null hypothesis: both conditions are drawn from the same distribution.
    Reject at p < 0.05.
    """
    bw = [r["avg_wait"] for r in baseline_results]
    gw = [r["avg_wait"] for r in ga_results]

    t_stat, p_value = stats.ttest_ind(bw, gw, equal_var=False)

    print("\n=== Statistical Significance (Welch's t-test on Avg Wait Time) ===")
    print(f"  Baseline mean: {sum(bw)/len(bw):.2f}s")
    print(f"  GA mean:       {sum(gw)/len(gw):.2f}s")
    print(f"  t-statistic:   {t_stat:.4f}")
    print(f"  p-value:       {p_value:.6f}")

    # check the p-value
    if p_value < 0.05:
        print("  Result: SIGNIFICANT (p < 0.05) — GA improvement is not due to chance.")
    else:
        print("  Result: NOT significant (p >= 0.05) — cannot rule out random variation.")

    return t_stat, p_value

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Default (42s/42s) timing plan on all intersections
    baseline_genes = [BASELINE_PHASE] * (N_INTERSECTIONS * 2)

    # Best solution found by the GA
    ga_genes = load_best_ga_genes()

    print("=" * 60)
    print(f"BASELINE vs GA — {N_INTERSECTIONS} Intersections")
    print(f"Baseline: {BASELINE_PHASE}s/{BASELINE_PHASE}s on all {N_INTERSECTIONS} intersections")
    print(f"Runs per condition: {N_RUNS}")
    print("=" * 60)

    baseline_results = run_condition("Baseline",     baseline_genes, N_RUNS)
    ga_results       = run_condition("GA_Optimized", ga_genes,       N_RUNS)

    # Save all results to CSV for dashboard visualization
    all_results = baseline_results + ga_results
    with open(COMPARISON_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "condition", "run", "fitness", "avg_wait",
            "throughput", "total_wait", "avg_speed"
        ])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nDONE. Results saved to {COMPARISON_CSV}")

    summarize("Baseline",     baseline_results)
    summarize("GA_Optimized", ga_results)
    t_test(baseline_results, ga_results)

    print("\nDone. Open the dashboard to visualize results.")