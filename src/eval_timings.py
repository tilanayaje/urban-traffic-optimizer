import os, sys, json
from pathlib import Path

# --- Paths ---
ROOT      = Path(__file__).resolve().parent.parent
SUMO_DIR  = ROOT / "sumo_data" / "generated"
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
# ---------------------------------------------------------------
TL_IDS    = ["J1", "J2", "J3"]
YELLOW    = 3
MAX_STEPS = 5000

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
    gA1: int, gB1: int,
    gA2: int, gB2: int,
    gA3: int, gB3: int,
    gui:     bool = False,
    verbose: bool = False,
    seed:    int  = None,
    port:    int  = None,
) -> dict:
    label = str(port) if port is not None else None
    start_sumo(gui=gui, seed=seed, port=port)
    conn = traci.getConnection(label) if label else traci

    set_greens({
        "J1": (gA1, gB1),
        "J2": (gA2, gB2),
        "J3": (gA3, gB3),
    }, label=label)

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
        "gA1": gA1, "gB1": gB1,
        "gA2": gA2, "gB2": gB2,
        "gA3": gA3, "gB3": gB3,
        "steps_used":    step,
        "arrived_total": arrived_total,
        "total_wait":    total_wait,
        "avg_speed":     avg_speed,
    }


# ---------------------------------------------------------------
# EVALUATE_WORKER  — writes result to worker_cache/
# ---------------------------------------------------------------
def evaluate_worker(args: tuple) -> dict:
    sol_idx, gA1, gB1, gA2, gB2, gA3, gB3, _ = args
    port = port_for_index(sol_idx % 12)

    result = evaluate(gA1, gB1, gA2, gB2, gA3, gB3,
                      gui=False, verbose=False, seed=None, port=port)

    # Write to file-based cache so main process can read it
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{sol_idx}.json"
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result