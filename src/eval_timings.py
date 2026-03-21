"""
eval_timings.py
Handles all SUMO simulation logic:
  - Starting/stopping SUMO via TraCI
  - Setting green phase durations on all intersections
  - Running simulations and collecting metrics
  - Parallel worker entry point (evaluate_worker)
  - File-based result cache for inter-process communication

This file has NO knowledge of the GA — it only runs simulations
and returns metric dicts. All GA logic lives in pygad_optimizer.py.
"""

import os
import sys
import json
from pathlib import Path

# Import all constants from the central config
from config import (
    ROOT, SUMO_DIR, SUMOCFG,
    COLS, ROWS,
    MAX_STEPS, YELLOW, BASE_PORT,
    POP_SIZE, CACHE_DIR,
)

# Validate SUMO config exists before importing traci
if not SUMOCFG.exists():
    raise FileNotFoundError(
        f"Missing SUMO config: {SUMOCFG}\n"
        f"Run the appropriate build_network script first, "
        f"or set the SUMO_MAP environment variable correctly."
    )

# Add SUMO tools to Python path 
if "SUMO_HOME" in os.environ:
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# Derived network constants 
# TL_IDS: ordered list of all traffic light junction IDs.
# Order defines the chromosome layout:
#   gene[0]=J_0_0 phase A, gene[1]=J_0_0 phase B,
#   gene[2]=J_0_1 phase A, gene[3]=J_0_1 phase B, ... etc.
TL_IDS          = [f"J_{col}_{row}" for col in range(COLS) for row in range(ROWS)]
N_INTERSECTIONS = len(TL_IDS)


# Port allocation 
def port_for_index(idx: int) -> int:
    """
    Returns a unique TraCI port for a given worker index.

    Without unique ports, concurrent SUMO instances collide on
    the same TCP socket and crash. BASE_PORT + sol_idx guarantees
    uniqueness within a generation (sol_idx ranges 0 to POP_SIZE-1).
    """
    return BASE_PORT + (idx % POP_SIZE)


# SUMO startup
def start_sumo(gui: bool = False, seed: int = None, port: int = None):
    """
    Launch a SUMO instance and connect via TraCI.

    Args:
        gui:  Open SUMO-GUI for visualization. Never use during
              parallel evaluation — GUI blocks the process.
        seed: Random seed for vehicle spawning. Different seeds
              produce different traffic patterns, essential for
              statistical validation across multiple runs.
        port: Unique TraCI port for this worker. If None, uses
              the default port (single-process mode only).
    """
    binary = "sumo-gui" if gui else "sumo"
    cmd = [
        binary,
        "-c", str(SUMOCFG),
        "--step-length",        "0.05",   # 50ms per step
        "--delay",              "0",       # no artificial slowdown
        "--lateral-resolution", "0.1",     # lane-change precision
        "--start",                         # begin simulation immediately
    ]
    if seed is not None:
        cmd += ["--seed", str(seed)]

    if port is not None:
        # label=str(port) lets us retrieve this specific TraCI connection
        # later with traci.getConnection(label) — required for parallel safety
        # since multiple connections exist simultaneously
        traci.start(cmd, port=port, label=str(port))
    else:
        traci.start(cmd)


# Phase setter 
def set_greens(phases_dict: dict, label: str = None):
    """
    Apply a timing plan to all intersections via TraCI.

    Each intersection has exactly 4 phases:
      [0] green phase A (north-south)
      [1] yellow (fixed)
      [2] green phase B (east-west)
      [3] yellow (fixed)

    Only the green durations are modified — yellow stays fixed
    at YELLOW seconds regardless of what the GA evolves.

    Args:
        phases_dict: { "J_0_0": (gA, gB), "J_0_1": (gA, gB), ... }
        label:       TraCI connection label. Pass str(port) when
                     running in parallel to access the correct connection.
    """
    conn = traci.getConnection(label) if label else traci

    for tl_id, (gA, gB) in phases_dict.items():
        # Enforce minimum green time — very short phases cause deadlocks
        # where vehicles cannot clear the intersection in one cycle
        gA = max(5, int(gA))
        gB = max(5, int(gB))

        prog   = conn.trafficlight.getAllProgramLogics(tl_id)[0]
        phases = prog.phases

        if len(phases) != 4:
            raise RuntimeError(
                f"Expected 4 phases for {tl_id}, got {len(phases)}. "
                f"Verify network generation."
            )

        phases[0].duration = gA       # north-south green
        phases[1].duration = YELLOW   # north-south yellow (fixed)
        phases[2].duration = gB       # east-west green
        phases[3].duration = YELLOW   # east-west yellow (fixed)

        conn.trafficlight.setProgramLogic(tl_id, prog)


# Fitness calculator 
def fitness(metrics: dict, alpha: float = 0.01) -> float:
    """
    fitness = arrived_total - alpha * total_wait

    Rewards throughput (more vehicles completing routes = better)
    while penalizing total network wait time. Alpha balances these
    two objectives — lower alpha for larger networks where total_wait
    scales with the number of intersections and vehicles.

    Args:
        metrics: dict returned by evaluate()
        alpha:   penalty weight. Import ALPHA from config rather than
                 passing a hardcoded value to ensure consistency.
    """
    return metrics["arrived_total"] - alpha * metrics["total_wait"]


# Core simulation evaluator 
def evaluate(
    genes:   list,
    gui:     bool = False,
    verbose: bool = False,
    seed:    int  = None,
    port:    int  = None,
) -> dict:
    """
    Run one complete SUMO simulation with the given timing plan.

    Args:
        genes:   Flat list of 2*N_INTERSECTIONS integers.
                 Layout: [gA_J0_0, gB_J0_0, gA_J0_1, gB_J0_1, ..., gA_J3_4, gB_J3_4]
                 Each consecutive pair (gA, gB) maps to one intersection
                 in the same order as TL_IDS.
        gui:     Open SUMO-GUI (single-process visualization only).
        verbose: Print progress every 500 steps.
        seed:    Random seed for vehicle spawning reproducibility.
        port:    Unique TraCI port (required for parallel workers).

    Returns:
        dict: {
            genes:         input genes (list)
            steps_used:    simulation steps actually run
            arrived_total: vehicles that completed their route
            total_wait:    cumulative wait time across all vehicles (seconds)
            avg_speed:     mean vehicle speed across all steps (m/s)
        }
    """
    assert len(genes) == N_INTERSECTIONS * 2, \
        f"Expected {N_INTERSECTIONS * 2} genes, got {len(genes)}"

    label = str(port) if port is not None else None
    start_sumo(gui=gui, seed=seed, port=port)
    conn = traci.getConnection(label) if label else traci

    # Build timing plan dict from flat gene array
    phases_dict = {
        tl_id: (genes[i * 2], genes[i * 2 + 1])
        for i, tl_id in enumerate(TL_IDS)
    }
    set_greens(phases_dict, label=label)

    # Simulation loop
    total_wait    = 0.0
    total_speed   = 0.0
    speed_samples = 0
    arrived_total = 0
    STEP_LEN   = 0.05   # seconds per simulation step (must match --step-length)
    STOP_SPEED = 0.1    # m/s — below this a vehicle is considered waiting

    for step in range(1, MAX_STEPS + 1):
        conn.simulationStep()

        veh_ids = conn.vehicle.getIDList()
        for vid in veh_ids:
            spd = conn.vehicle.getSpeed(vid)
            if spd < STOP_SPEED:
                total_wait += STEP_LEN   # accumulate wait in seconds
            total_speed   += spd
            speed_samples += 1

        arrived_total += conn.simulation.getArrivedNumber()

        if verbose and step % 500 == 0:
            print(f"step {step}  vehicles {len(veh_ids)}  arrived {arrived_total}")

        # Early exit: all vehicles have either arrived or are no longer expected
        if conn.simulation.getMinExpectedNumber() <= 0:
            break

    conn.close()

    avg_speed = (total_speed / speed_samples) if speed_samples else 0.0
    return {
        "genes":         list(genes),
        "steps_used":    step,
        "arrived_total": arrived_total,
        "total_wait":    total_wait,
        "avg_speed":     avg_speed,
    }


# Parallel worker entry point 
def evaluate_worker(args: tuple) -> dict:
    """
    Entry point for each parallel worker process in the GA population.

    Called by PyGAD's parallel_processing pool. Each worker:
      1. Derives a unique TraCI port from sol_idx (no socket collisions)
      2. Runs a full SUMO simulation
      3. Writes result to worker_cache/{sol_idx}.json
         (Windows multiprocessing cannot share memory directly —
          file-based cache is the reliable cross-process communication method)
      4. Returns the result dict to the GA fitness function

    Args:
        args: tuple of (sol_idx, genes, _)
              sol_idx: worker index 0 to POP_SIZE-1
              genes:   flat list of green phase durations
              _:       unused — required by PyGAD parallel format
    """
    sol_idx, genes, _ = args
    port = port_for_index(sol_idx)

    result = evaluate(genes, gui=False, verbose=False, seed=None, port=port)

    # Write to file-based cache for main process to read
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{sol_idx}.json"
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result