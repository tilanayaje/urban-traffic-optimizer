# Urban Traffic Optimizer
### **Full Title:** 🚦 🚗 Real-Time Big Data Analytics and Visualization for Urban Traffic Flow Optimization 💨💨

### Description
This project uses **SUMO** (Simulation of Urban MObility) to simulate urban traffic across a scalable intersection network. A **Genetic Algorithm (PyGAD)** evolves traffic light timings across multiple coordinated intersections while a **live Streamlit dashboard** visualizes optimization progress in real time. The system procedurally generates a standardized traffic network, runs repeated SUMO simulations in **parallel across multiple CPU cores**, evaluates congestion metrics, and evolves better signal timing plans generation by generation.

**Goals:**
- Reduce average vehicle waiting time
- Improve network throughput
- Statistically validate optimization results against a baseline
- Scale to city-level infrastructure (Towns of 20 intersections; Thunder Bay: 113 intersections)
- Visualize optimization progress in real time

---

## Architecture Overview

```
SUMO Network Generation → Parallel SUMO Simulations (12 workers) → GA Fitness Evaluation → CSV Logging → Streamlit Dashboard
```

The system runs end-to-end:
1. `build_network.py` / `build_network_20.py` generates the SUMO network
2. `pygad_optimizer.py` runs the GA — evaluates 12 candidate solutions in parallel each generation
3. Results logged to `ga_history.csv` per generation; checkpoint saved after each generation
4. `baseline.py` runs a statistical comparison between default timing and GA-optimized timing
5. `dashboard.py` visualizes GA progress, baseline comparison, scalability, and heatmaps

---

## 🗂️ File Structure

**📁 src/**
_Core logic and optimization pipeline._

🔹 **config.py**
Central configuration file. All constants (gene range, population size, generations, alpha, simulation steps, network paths) are defined here and imported by all other scripts. Change a value once — it propagates everywhere.

🔹 **build_network.py**
Procedurally generates the 3-intersection corridor network (J1, J2, J3).
Creates:
- `Traci.net.xml` — network geometry
- `Traci.rou.xml` — traffic flows
- `Traci.sumocfg` — simulation config

🔹 **build_network_20.py**
Generates the scaled 4×5 grid network of 20 coordinated intersections (300m spacing).
Creates the same file set under `sumo_data/grid20/`.

🔹 **eval_timings.py**
Runs SUMO simulations via TraCI. Handles:
- Parallel-safe port allocation (unique TraCI port per worker)
- Setting green phase durations across all intersections
- Collecting metrics: throughput, total wait time, average speed
- Writing results to a file-based worker cache for zero-cost logging

🔹 **pygad_optimizer.py**
Implements the Genetic Algorithm using PyGAD.
- **Chromosome:** flat list of `[gA, gB]` pairs for each intersection — 6 genes (3 intersections) or 40 genes (20 intersections)
- **Parallel evaluation:** all 12 population members evaluated simultaneously via `multiprocessing` + PyGAD's `parallel_processing`
- **Operators:** tournament selection, two-point crossover, adaptive mutation
- **Checkpoint/resume:** saves population state after every generation — interrupted runs resume from the last completed generation rather than restarting from gen 1
- Logs per-generation metrics to `ga_history.csv`

🔹 **baseline.py**
Runs the network under SUMO's default timing plan (42s/42s on all intersections) N times with different random seeds, then runs the GA-optimized plan the same number of times. Performs a **Welch's t-test** to confirm statistical significance.

🔹 **dashboard.py**
Real-time Streamlit dashboard with four tabs:
- **GA Optimization Progress** — live convergence curves, fitness score, gene evolution per intersection
- **Baseline vs GA Comparison** — box plots, t-test results, run-by-run table
- **Scalability** — parallel vs sequential runtime comparison, full theory section
- **Heatmaps** — intersection timing plan visualized as a road grid, deviation from baseline

🔹 **Traci1.py**
Legacy utility script for basic SUMO simulation execution and testing.

---

**📁 sumo_data/**

🔹 **generated/**
3-intersection corridor network files (J1, J2, J3).

🔹 **grid20/**
20-intersection 4×5 grid network files.

Each folder contains:
- `Traci.net.xml` — network geometry (edges, junctions, traffic lights)
- `Traci.rou.xml` — vehicle flow definitions
- `Traci.sumocfg` — main SUMO config linking network and routes

---

**📁 Root/**

🔹 `dashboard.py` — Streamlit dashboard entry point

🔹 `ga_history.csv` — per-generation GA logging output

🔹 `comparison_results.csv` — baseline vs GA statistical comparison output

🔹 `worker_cache/` — temporary file-based cache used by parallel workers during GA evaluation

🔹 `checkpoints/` — checkpoint files saved after each generation for run resumption

---

## Optimization Model

**Chromosome encoding:**
Each chromosome is a flat list of green phase durations:
```
[gA_J1, gB_J1, gA_J2, gB_J2, ..., gA_Jn, gB_Jn]
```
- `gA` = green duration for phase A (N-S direction)
- `gB` = green duration for phase B (E-W direction)
- Yellow phases remain fixed at 3 seconds
- Gene range: 10s – 80s

**Fitness function:**
```
fitness = arrived_total - α × total_wait
```
Where `α = 0.001` (wait time penalty weight). Fitness rewards throughput while penalizing excessive waiting.

**GA operators:**
- Selection: Tournament (K=3)
- Crossover: Two-point
- Mutation: Adaptive (40% early generations → 10% late generations)
- Elitism: Top 3 solutions preserved each generation

---

## Scalability

| Network | Intersections | Genes | Sequential (20 gens, est.) | Parallel (12 cores, 20 gens) |
|---|---|---|---|---|
| Corridor | 3 | 6 | ~2,000 min (est.) | ~160 min (measured) |
| Grid | 20 | 40 | ~2,400 min (est.) | ~300 min (measured) |
| City-Scale (theoretical) | 113 | 226 | — | — |

Parallel evaluation reduces complexity from **O(P × G × T)** to **O(G × T)**, where P = population size, G = generations, T = simulation time per evaluation. Sequential runtimes are estimated from observed per-simulation times (T × P × G). Parallel runtimes are directly measured.

---

## Results

### 3-Intersection Corridor — Baseline vs GA

| Metric | Baseline (42s/42s) | GA Optimized |
|---|---|---|
| Mean Avg Wait | 44.78s | 12.05s |
| Wait Reduction | — | **73.1%** |
| Mean Throughput | 101.8 cars | 149.0 cars |
| t-statistic | — | 22.91 |
| p-value | — | **< 0.000001** |

### 20-Intersection Grid — Baseline vs GA (20 runs each)

| Metric | Baseline (42s/42s) | GA Optimized |
|---|---|---|
| Mean Avg Wait | 85.34s | 74.53s |
| Wait Reduction | — | **12.7%** |
| Mean Throughput | 421.6 cars | 444.7 cars |
| t-statistic | — | 13.20 |
| p-value | — | **< 0.000001** |

GA convergence over 20 generations: 85.0s (gen 1) → 64.6s (gen 20), **24% improvement** from random initialization.

---

<img width="774" height="879" alt="image" src="https://github.com/user-attachments/assets/1619165d-f1b8-49bf-9f9c-1ad3a9ba5fe4" />

The "Improvement" KPI compares the current best solution to the generation 1 best — drawn from random initialization, not a controlled fixed-timing condition. For the validated improvement against the 42s/42s baseline, see the Baseline vs GA tab.

<img width="1262" height="601" alt="image" src="https://github.com/user-attachments/assets/e6a1b058-fc90-4d87-b725-cd48c4aeac90" />

The baseline condition uses SUMO's default fixed-timing plan (42s/42s on every intersection). Both conditions evaluated 20 times each with different random seeds.

<img width="1271" height="828" alt="image" src="https://github.com/user-attachments/assets/05209124-7193-4102-a1a7-417c058e5718" />

Deviation of the final GA solution from the 42s default. Green = GA increased green time above baseline. Red = GA reduced green time below baseline.

---
<img width="755" height="513" alt="image" src="https://github.com/user-attachments/assets/25005768-7f0c-43e5-bc78-cc8b99af29c8" />

Parallel Processing: 12 SUMO simulations running simultaneously during a single GA generation evaluation.

---

## How to Run

**1. Generate the network:**
```bash
py src/build_network.py        # 3-intersection corridor
py src/build_network_20.py     # 20-intersection grid
```

**2. Run the GA:**
```bash
py src/pygad_optimizer.py
```
If a previous run was interrupted, this automatically resumes from the last completed generation. To force a fresh start:
```bash
del checkpoints\checkpoint.json
py src/pygad_optimizer.py
```

**3. Run the dashboard (separate terminal):**
```bash
py -m streamlit run dashboard.py
```

**4. Run baseline comparison (after GA completes):**
```bash
py src/baseline.py
```

**5. Switch between networks:**
```bash
$env:SUMO_MAP = "generated"   # 3-intersection corridor
$env:SUMO_MAP = "grid20"      # 20-intersection grid (default)
py src/pygad_optimizer.py
```

---

## Todolist

- [ ] Record demo videos (baseline vs GA-optimized, SUMO GUI)
- [ ] Re-run 3-intersection baseline for verified std dev values