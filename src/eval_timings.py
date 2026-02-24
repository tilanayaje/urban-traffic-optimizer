import os, sys
from pathlib import Path

# --- SUMO tools setup ---
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci


# --- Paths (absolute, so cwd never matters) ---
ROOT = Path(__file__).resolve().parent.parent  # repo root

# default to generated map (everyone has the same one)
MAP = os.environ.get("SUMO_MAP", "generated")
SUMO_DIR = ROOT / "sumo_data" / MAP
SUMOCFG = ROOT / "sumo_data" / MAP / "Traci.sumocfg"

# fail fast if missing (helps teammates)
if not SUMOCFG.exists():
    raise FileNotFoundError(f"Missing SUMO config: {SUMOCFG}")

TL_ID = "J11"      # from your Traci.net.xml
YELLOW = 3         # keep fixed
MAX_STEPS = 4000   # fixed horizon so runs are comparable



def start_sumo(gui=False):
    sumo_binary = "sumo-gui" if gui else "sumo"
    cmd = [
        sumo_binary,
        "-c", str(SUMOCFG),
        "--step-length", "0.05",
        "--delay", "0",
        "--lateral-resolution", "0.1",
        "--start"
    ]
    traci.start(cmd)


def set_J11_greens(gA: int, gB: int):
    """
    J11 has 4 phases in the net:
      0: greenA
      1: yellow
      2: greenB
      3: yellow
    We only change green durations.
    """
    gA = max(5, int(gA))
    gB = max(5, int(gB))

    prog = traci.trafficlight.getAllProgramLogics(TL_ID)[0]
    phases = prog.phases

    if len(phases) != 4:
        raise RuntimeError(f"Expected 4 phases for {TL_ID}, found {len(phases)}")

    phases[0].duration = gA
    phases[1].duration = YELLOW
    phases[2].duration = gB
    phases[3].duration = YELLOW

    traci.trafficlight.setProgramLogic(TL_ID, prog)


def fitness(metrics, alpha=0.01):
    return metrics["arrived_total"] - alpha * metrics["total_wait"]


def evaluate(gA: int, gB: int, gui=False, verbose=False):
    """
    Run one simulation with a fixed timing plan and return metrics.
    Fitness later can be something like: arrived - alpha * total_wait
    """
    start_sumo(gui=gui)
    set_J11_greens(gA, gB)

    total_wait = 0.0
    total_speed = 0.0
    speed_samples = 0
    arrived_total = 0

    STEP_LEN = 0.05
    STOP_SPEED = 0.1

    for step in range(1, MAX_STEPS + 1):
        traci.simulationStep()

        veh_ids = traci.vehicle.getIDList()
        for vid in veh_ids:
            spd = traci.vehicle.getSpeed(vid)
            if spd < STOP_SPEED:
                total_wait += STEP_LEN
            total_speed += spd
            speed_samples += 1

        arrived_total += traci.simulation.getArrivedNumber()

        # gate heartbeat print with verbose
        if verbose and step % 500 == 0:
            print(f"[{gA},{gB}] step {step} vehicles {len(veh_ids)} arrived_total {arrived_total}")

        if traci.simulation.getMinExpectedNumber() <= 0:
            break

    traci.close()

    avg_speed = (total_speed / speed_samples) if speed_samples else 0.0
    return {
        "gA": gA,
        "gB": gB,
        "steps_used": step,
        "arrived_total": arrived_total,
        "total_wait": total_wait,
        "avg_speed": avg_speed,
    }

import random

GREEN_MIN = 10
GREEN_MAX = 80

POP_SIZE = 12
GENERATIONS = 10
ELITE_K = 4
MUT_STD = 6  # seconds

def clamp(x):
    return max(GREEN_MIN, min(GREEN_MAX, int(x)))

def mutate(ind):
    gA, gB = ind
    if random.random() < 0.8:
        gA = clamp(gA + random.gauss(0, MUT_STD))
    if random.random() < 0.8:
        gB = clamp(gB + random.gauss(0, MUT_STD))
    return [gA, gB]

def crossover(a, b):
    # simple: swap one gene
    if random.random() < 0.5:
        return [a[0], b[1]]
    else:
        return [b[0], a[1]]

if __name__ == "__main__":
    # 1) initial population
    pop = [[random.randint(GREEN_MIN, GREEN_MAX), random.randint(GREEN_MIN, GREEN_MAX)]
           for _ in range(POP_SIZE)]

    best_ind = None
    best_fit = -1e18

    for gen in range(GENERATIONS):
        scored = []
        for ind in pop:
            m = evaluate(ind[0], ind[1], gui=False, verbose=False)
            f = fitness(m, alpha=0.01)
            scored.append((f, ind, m))

        scored.sort(reverse=True, key=lambda x: x[0])

        gen_best_f, gen_best_ind, gen_best_m = scored[0]
        if gen_best_f > best_fit:
            best_fit = gen_best_f
            best_ind = gen_best_ind

        print(f"\nGEN {gen} BEST: {gen_best_ind} fitness={gen_best_f:.2f} "
              f"(arrived={gen_best_m['arrived_total']}, wait={gen_best_m['total_wait']:.1f}, avg_speed={gen_best_m['avg_speed']:.2f})")

        # 2) select elites
        elites = [ind for (_, ind, _) in scored[:ELITE_K]]

        # 3) make next generation
        new_pop = elites.copy()
        while len(new_pop) < POP_SIZE:
            p1, p2 = random.sample(elites, 2)
            child = crossover(p1, p2)
            child = mutate(child)
            new_pop.append(child)

        pop = new_pop

    print("\nOVERALL BEST:", best_ind, "fitness=", best_fit)
