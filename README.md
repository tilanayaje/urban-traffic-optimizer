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
1. `build_network.py` generates the SUMO network
2. `pygad_optimizer.py` runs the GA. For each generation, evaluates 12 candidate solutions in parallel using Python multiprocessing
3. Results are logged to `ga_history.csv` per generation
4. `baseline.py` runs a statistical comparison between default timing and GA-optimized timing
5. `dashboard.py` visualizes both the GA progress and the baseline vs GA comparison

---

## 🗂️ File Structure

**📁 src/**
_Core logic and optimization pipeline._

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
- **Chromosome:** flat list of `[gA, gB]` pairs for each intersection, 6 genes (3 intersections) or 40 genes (20 intersections)
- **Parallel evaluation:** all 12 population members evaluated simultaneously via `multiprocessing` + PyGAD's `parallel_processing`
- **Operators:** tournament selection, two-point crossover, adaptive mutation
- Logs per-generation metrics to `ga_history.csv`

🔹 **baseline.py**
Runs the network under SUMO's default timing plan (42s/42s on all intersections) N times with different random seeds, then runs the GA-optimized plan the same number of times. Performs a **Welch's t-test** to confirm statistical significance of the improvement.

🔹 **dashboard.py**
Real-time Streamlit dashboard with two tabs:
- **GA Optimization Progress** — live convergence curves, fitness score, gene evolution per intersection
- **Baseline vs GA Comparison** — box plots, t-test results, run-by-run table

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

🔹 `worker_cache/` — temporary file-based cache used by parallel workers

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

| Network | Intersections | Genes | Sequential runtime | Parallel runtime (12 cores) |
|---|---|---|---|---|
| Corridor | 3 | 6 | ~100 min | ~20 min |
| Grid | 20 | 40 | ~40 hours (estimated) | ~3–5 hours |
|  (theoretical) | 113 | 226 | — | — |
| City-Scale (theoretical) | 113 | 226 | — | — |

Parallel evaluation reduces complexity from **O(P × G × T)** to **O(G × T)**, where P = population size, G = generations, T = simulation time per evaluation.

---

## Results

_Results section will be updated upon completion of the 20-intersection GA run and baseline comparison._

---

## Parallel Processing in Action

<img width="755" height="513" alt="image" src="https://github.com/user-attachments/assets/25005768-7f0c-43e5-bc78-cc8b99af29c8" />

Sumo simulations running on different processes via task manager

_Each process independently evaluates one candidate timing solution. Generation time: ~10–15 minutes (vs ~120 minutes sequentially)._

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

**3. Run the dashboard (separate terminal):**
```bash
py -m streamlit run dashboard.py
```

**4. Run baseline comparison (after GA completes):**
```bash
py src/baseline.py
```

---

## Todolist

- [ ] Complete 20-intersection GA run (20 generations)
- [ ] Run baseline comparison on 20-intersection network
- [ ] Statistical significance validation on 20-intersection results
- [ ] Update results section with final numbers
- [ ] Record demo videos (baseline vs GA-optimized, SUMO GUI)
- [ ] Dashboard heatmap of per-intersection wait times
- [ ] Report write-up — methods, results
