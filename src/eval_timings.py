import os, sys, json
from pathlib import Path

# --- Paths ---
ROOT      = Path(__file__).resolve().parent.parent
SUMO_DIR  = ROOT / "sumo_data" / "grid20"
SUMOCFG   = SUMO_DIR / "Traci.sumocfg"
CACHE_DIR = ROOT / "worker_cache"

if not SUMOCFG.exists():
    raise FileNotFoundError(f"Missing SUMO config: {SUMOCFG}")

if "SUMO_HOME" in os.environ:
    sys.path.append(str(Path(os.environ["SUMO_HOME"]) / "tools"))
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# ---------------------------------------------------------------
# NETWORK CONFIG
# 4x5 grid: cols 0-3, rows 0-4
# ---------------------------------------------------------------
COLS = 4
ROWS = 5
TL_IDS = [f"J_{col}_{row}" for col in range(COLS) for row in range(ROWS)]  # 20 TLs
N_INTERSECTIONS = len(TL_IDS)  # 20
YELLOW    = 3
MAX_STEPS = 8000   # larger network needs more steps

# ---------------------------------------------------------------
# PORT ALLOCATOR
# ---------------------------------------------------------------
BASE_PORT = 8813

def port_for_index(idx: int) -> int:
    return BASE_PORT + idx


# ---------------------------------------------------------------
# SUMO HELPERS
# ---------------------------------------------------------------
def start_sumo(gui: bool = False, seed: int = None, port: int = None):
    binary = "sumo-gui" if gui else "sumo"
    cmd = [
        binary,
        "-c", str(SUMOCFG),
        "--step-length",        "0.05",
        "--delay",              "0",
        "--lateral-resolution", "0.1",
        "--start",
    ]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    if port is not None:
        traci.start(cmd, port=port, label=str(port))
    else:
        traci.start(cmd)


def set_greens(phases_dict: dict, label: str = None):
    """
    phases_dict = { "J_0_0": (gA, gB), "J_0_1": (gA, gB), ... }
    4-phase layout: greenA, yellow, greenB, yellow
    """
    conn = traci.getConnection(label) if label else traci
    for tl_id, (gA, gB) in phases_dict.items():
        gA = max(5, int(gA))
        gB = max(5, int(gB))
        prog   = conn.trafficlight.getAllProgramLogics(tl_id)[0]
        phases = prog.phases
        if len(phases) != 4:
            raise RuntimeError(f"Expected 4 phases for {tl_id}, got {len(phases)}")
        phases[0].duration = gA
        phases[1].duration = YELLOW
        phases[2].duration = gB
        phases[3].duration = YELLOW
        conn.trafficlight.setProgramLogic(tl_id, prog)


# ---------------------------------------------------------------
# FITNESS HELPER
# ---------------------------------------------------------------
def fitness(metrics: dict, alpha: float = 0.01) -> float:
    return metrics["arrived_total"] - alpha * metrics["total_wait"]


# ---------------------------------------------------------------
# EVALUATE
# ---------------------------------------------------------------
def evaluate(
    genes:   list,          # 40 values: [gA0, gB0, gA1, gB1, ..., gA19, gB19]
    gui:     bool = False,
    verbose: bool = False,
    seed:    int  = None,
    port:    int  = None,
) -> dict:
    """
    genes: flat list of 40 ints — pairs of (gA, gB) for each of the 20 intersections
    in the same order as TL_IDS.
    """
    assert len(genes) == N_INTERSECTIONS * 2, \
        f"Expected {N_INTERSECTIONS*2} genes, got {len(genes)}"

    label = str(port) if port is not None else None
    start_sumo(gui=gui, seed=seed, port=port)
    conn = traci.getConnection(label) if label else traci

    phases_dict = {}
    for i, tl_id in enumerate(TL_IDS):
        gA = genes[i * 2]
        gB = genes[i * 2 + 1]
        phases_dict[tl_id] = (gA, gB)

    set_greens(phases_dict, label=label)

    total_wait    = 0.0
    total_speed   = 0.0
    speed_samples = 0
    arrived_total = 0
    STEP_LEN   = 0.05
    STOP_SPEED = 0.1

    for step in range(1, MAX_STEPS + 1):
        conn.simulationStep()
        veh_ids = conn.vehicle.getIDList()
        for vid in veh_ids:
            spd = conn.vehicle.getSpeed(vid)
            if spd < STOP_SPEED:
                total_wait += STEP_LEN
            total_speed   += spd
            speed_samples += 1
        arrived_total += conn.simulation.getArrivedNumber()
        if verbose and step % 500 == 0:
            print(f"step {step}  vehicles {len(veh_ids)}  arrived {arrived_total}")
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


# ---------------------------------------------------------------
# EVALUATE_WORKER  — called by parallel pool
# ---------------------------------------------------------------
def evaluate_worker(args: tuple) -> dict:
    sol_idx, genes, _ = args
    port = port_for_index(sol_idx % 20)

    result = evaluate(genes, gui=False, verbose=False, seed=None, port=port)

    # Write to file-based cache
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{sol_idx}.json"
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result