# ============================================================
# Central configuration for the Urban Traffic Optimizer.
# All scripts import from here.
# change a value once and it propagates everywhere.
# ============================================================

import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

# Network selection
# Which SUMO network to use. Looks for:
#   sumo_data/{SUMO_MAP}/Traci.sumocfg
# Options: "generated" (3-intersection), "grid20" (20-intersection)
# Override at runtime:  $env:SUMO_MAP = "generated"
SUMO_MAP = os.environ.get("SUMO_MAP", "grid20")

# SUMO paths
SUMO_DIR = ROOT / "sumo_data" / SUMO_MAP
SUMOCFG  = SUMO_DIR / "Traci.sumocfg"

# Network geometry 
# 4-column × 5-row = 20 intersections for grid20.
# Change these for different grid sizes
COLS = 4
ROWS = 5

# Simulation parameters 
# MAX_STEPS: simulation steps per evaluation.
# Each step advances the simulation clock by 0.05 simulated seconds.
# 8000 steps = 400 seconds of simulated traffic time.
MAX_STEPS = 8000

# Yellow phase duration in seconds is fixed. The yellow phase will always be 3 seconds
YELLOW = 3

# TraCI port base. Each parallel worker gets BASE_PORT + sol_idx
# to avoid socket collisions between concurrent SUMO instances.
BASE_PORT = 8813

# GA parameters 
# Gene range: minimum and maximum green phase duration in seconds.
GREEN_MIN = 10
GREEN_MAX = 80

# Population size. Should match the number of parallel workers
# so every member evaluates simultaneously in one generation.
POP_SIZE = 12

# Number of generations to run.
GENERATIONS = 20

# Fitness penalty weight for total wait time.
# Smaller alpha for larger networks where total_wait is proportionally larger.
# 3-intersection: 0.01 | 20-intersection: 0.001
ALPHA = 0.001

# Baseline parameters
# Number of independent simulation runs per condition.
N_RUNS = 20

# SUMO's default fixed green phase (seconds), confirmed via TraCI inspection.
BASELINE_PHASE = 42

# File paths 
CACHE_DIR       = ROOT / "worker_cache"
CHECKPOINT_DIR  = ROOT / "checkpoints"
GA_HISTORY_CSV  = ROOT / "ga_history.csv"
COMPARISON_CSV  = ROOT / "comparison_results.csv"
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"