import os
import sys
import csv
import random
from pathlib import Path

# --- SUMO setup ---
if "SUMO_HOME" in os.environ:
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

from eval_timings import evaluate, fitness

# ============================================================
# BASELINE CONFIG
# These are the exact default timings SUMO assigned at runtime
# via netconvert — confirmed via TraCI inspection.
# gA=42s, gB=42s on all 3 intersections.
# ============================================================
BASELINE_GA1, BASELINE_GB1 = 42, 42  # J1
BASELINE_GA2, BASELINE_GB2 = 42, 42  # J2
BASELINE_GA3, BASELINE_GB3 = 42, 42  # J3

# GA best solution from optimization run
GA_GA1, GA_GB1 = 23, 15  # J1
GA_GA2, GA_GB2 = 24, 13  # J2
GA_GA3, GA_GB3 = 17, 20  # J3

N_RUNS = 10        # number of repeat runs per condition
ALPHA  = 0.01      # must match pygad_optimizer.py
OUTPUT = "comparison_results.csv"


def run_condition(label, gA1, gB1, gA2, gB2, gA3, gB3, n_runs):
    """
    Run the same timing plan N times and return list of metric dicts.
    Each run uses a different random seed via SUMO's --random flag.
    """
    results = []
    for i in range(n_runs):
        seed = 42 + i  # deterministic but unique per run: 42, 43, 44...
        print(f"[{label}] Run {i+1}/{n_runs} (seed={seed}) ...")
        m = evaluate(gA1, gB1, gA2, gB2, gA3, gB3, gui=False, verbose=False, seed=seed)
        f = fitness(m, alpha=ALPHA)
        avg_wait = m["total_wait"] / m["arrived_total"] if m["arrived_total"] > 0 else 0
        results.append({
            "condition":      label,
            "run":            i + 1,
            "fitness":        f,
            "avg_wait":       avg_wait,
            "throughput":     m["arrived_total"],
            "total_wait":     m["total_wait"],
            "avg_speed":      m["avg_speed"],
        })
        print(f"  -> avg_wait={avg_wait:.2f}s  throughput={m['arrived_total']}  fitness={f:.2f}")
    return results


def save_results(all_results):
    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "condition", "run", "fitness", "avg_wait",
            "throughput", "total_wait", "avg_speed"
        ])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nResults saved to {OUTPUT}")


def summarize(label, results):
    waits = [r["avg_wait"] for r in results]
    throughputs = [r["throughput"] for r in results]
    fitnesses = [r["fitness"] for r in results]

    print(f"\n--- {label} ({len(results)} runs) ---")
    print(f"  Avg Wait:     mean={sum(waits)/len(waits):.2f}s  "
          f"min={min(waits):.2f}s  max={max(waits):.2f}s")
    print(f"  Throughput:   mean={sum(throughputs)/len(throughputs):.1f}  "
          f"min={min(throughputs)}  max={max(throughputs)}")
    print(f"  Fitness:      mean={sum(fitnesses)/len(fitnesses):.2f}  "
          f"min={min(fitnesses):.2f}  max={max(fitnesses):.2f}")


def t_test(baseline_results, ga_results):
    """
    Welch's t-test on avg_wait between baseline and GA conditions.
    Does not assume equal variance — more appropriate here.
    """
    from scipy import stats

    baseline_waits = [r["avg_wait"] for r in baseline_results]
    ga_waits       = [r["avg_wait"] for r in ga_results]

    t_stat, p_value = stats.ttest_ind(baseline_waits, ga_waits, equal_var=False)

    print("\n--- Statistical Significance (Welch's t-test on Avg Wait Time) ---")
    print(f"  Baseline mean: {sum(baseline_waits)/len(baseline_waits):.2f}s")
    print(f"  GA mean:       {sum(ga_waits)/len(ga_waits):.2f}s")
    print(f"  t-statistic:   {t_stat:.4f}")
    print(f"  p-value:       {p_value:.6f}")

    if p_value < 0.05:
        print("  Result: SIGNIFICANT (p < 0.05) — the GA improvement is not due to chance.")
    else:
        print("  Result: NOT significant (p >= 0.05) — cannot rule out random variation.")

    return t_stat, p_value


if __name__ == "__main__":
    print("=" * 60)
    print("BASELINE vs GA COMPARISON")
    print(f"Baseline: gA=gB=42s on all 3 intersections (SUMO default)")
    print(f"GA:       J1({GA_GA1}/{GA_GB1}) J2({GA_GA2}/{GA_GB2}) J3({GA_GA3}/{GA_GB3})")
    print(f"Runs per condition: {N_RUNS}")
    print("=" * 60)

    # Run baseline
    baseline_results = run_condition(
        "Baseline",
        BASELINE_GA1, BASELINE_GB1,
        BASELINE_GA2, BASELINE_GB2,
        BASELINE_GA3, BASELINE_GB3,
        N_RUNS
    )

    # Run GA best solution
    ga_results = run_condition(
        "GA_Optimized",
        GA_GA1, GA_GB1,
        GA_GA2, GA_GB2,
        GA_GA3, GA_GB3,
        N_RUNS
    )

    # Save to CSV
    save_results(baseline_results + ga_results)

    # Print summaries
    summarize("Baseline", baseline_results)
    summarize("GA_Optimized", ga_results)

    # Statistical test
    t_test(baseline_results, ga_results)

    print("\nDone. Use comparison_results.csv to generate box plots.")