"""
build_network_20.py
Generates a 4-column x 5-row grid of 20 traffic light intersections.
Spacing: 300m between intersections.
Entry/exit nodes on all 4 edges of the grid.
"""
import os
import subprocess
from pathlib import Path
from sumolib import checkBinary

ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "sumo_data" / "grid20"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COLS    = 4
ROWS    = 5
SPACING = 300   # metres between intersections
SPEED   = 13.89 # m/s (~50 km/h)
LANES   = 2

print(f"Generating {COLS}x{ROWS} grid ({COLS*ROWS} intersections), spacing={SPACING}m...")


# ── Helper ────────────────────────────────────────────────────────────
def jid(col, row):
    """Intersection node id: J_col_row"""
    return f"J_{col}_{row}"


# ══════════════════════════════════════════════════════════════════════
# 1. NODES
# ══════════════════════════════════════════════════════════════════════
node_lines = []

# 20 internal intersections
for row in range(ROWS):
    for col in range(COLS):
        x = col * SPACING
        y = row * SPACING
        node_lines.append(
            f'    <node id="{jid(col,row)}" x="{x:.1f}" y="{y:.1f}" type="traffic_light"/>'
        )

# Entry/exit nodes on each edge (one per intersection on that edge)
# West edge (col=-1)
for row in range(ROWS):
    node_lines.append(
        f'    <node id="W_{row}" x="{-SPACING:.1f}" y="{row*SPACING:.1f}" type="priority"/>'
    )
# East edge (col=COLS)
for row in range(ROWS):
    node_lines.append(
        f'    <node id="E_{row}" x="{COLS*SPACING:.1f}" y="{row*SPACING:.1f}" type="priority"/>'
    )
# South edge (row=-1)
for col in range(COLS):
    node_lines.append(
        f'    <node id="S_{col}" x="{col*SPACING:.1f}" y="{-SPACING:.1f}" type="priority"/>'
    )
# North edge (row=ROWS)
for col in range(COLS):
    node_lines.append(
        f'    <node id="N_{col}" x="{col*SPACING:.1f}" y="{ROWS*SPACING:.1f}" type="priority"/>'
    )

nodes_xml = "<nodes>\n" + "\n".join(node_lines) + "\n</nodes>"
with open(DATA_DIR / "nodes.nod.xml", "w") as f:
    f.write(nodes_xml)


# ══════════════════════════════════════════════════════════════════════
# 2. EDGES
# ══════════════════════════════════════════════════════════════════════
edge_lines = []

def edge(eid, src, dst, priority=1):
    return (f'    <edge id="{eid}" from="{src}" to="{dst}" '
            f'priority="{priority}" numLanes="{LANES}" speed="{SPEED}"/>')

# Horizontal internal links (East-West corridor per row)
for row in range(ROWS):
    for col in range(COLS - 1):
        a, b = jid(col, row), jid(col+1, row)
        edge_lines.append(edge(f"{a}_to_{b}", a, b, priority=2))
        edge_lines.append(edge(f"{b}_to_{a}", b, a, priority=2))

# Vertical internal links (North-South per column)
for col in range(COLS):
    for row in range(ROWS - 1):
        a, b = jid(col, row), jid(col, row+1)
        edge_lines.append(edge(f"{a}_to_{b}", a, b, priority=2))
        edge_lines.append(edge(f"{b}_to_{a}", b, a, priority=2))

# West entry/exit edges
for row in range(ROWS):
    j = jid(0, row)
    w = f"W_{row}"
    edge_lines.append(edge(f"{w}_to_{j}", w, j))
    edge_lines.append(edge(f"{j}_to_{w}", j, w))

# East entry/exit edges
for row in range(ROWS):
    j = jid(COLS-1, row)
    e = f"E_{row}"
    edge_lines.append(edge(f"{e}_to_{j}", e, j))
    edge_lines.append(edge(f"{j}_to_{e}", j, e))

# South entry/exit edges
for col in range(COLS):
    j = jid(col, 0)
    s = f"S_{col}"
    edge_lines.append(edge(f"{s}_to_{j}", s, j))
    edge_lines.append(edge(f"{j}_to_{s}", j, s))

# North entry/exit edges
for col in range(COLS):
    j = jid(col, ROWS-1)
    n = f"N_{col}"
    edge_lines.append(edge(f"{n}_to_{j}", n, j))
    edge_lines.append(edge(f"{j}_to_{n}", j, n))

edges_xml = "<edges>\n" + "\n".join(edge_lines) + "\n</edges>"
with open(DATA_DIR / "edges.edg.xml", "w") as f:
    f.write(edges_xml)


# ══════════════════════════════════════════════════════════════════════
# 3. NETCONVERT
# ══════════════════════════════════════════════════════════════════════
netconvert = checkBinary("netconvert")
subprocess.run([
    netconvert,
    "--node-files", str(DATA_DIR / "nodes.nod.xml"),
    "--edge-files", str(DATA_DIR / "edges.edg.xml"),
    "--output-file", str(DATA_DIR / "Traci.net.xml"),
    "--no-turnarounds",
], check=True)
print("Network built.")


# ══════════════════════════════════════════════════════════════════════
# 4. ROUTES
# ══════════════════════════════════════════════════════════════════════
route_lines = []
route_lines.append('    <vType id="car" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2" maxSpeed="15"/>')

flow_id = 0

def flow(rid, edges_str, prob):
    global flow_id
    route_lines.append(f'    <route id="r{rid}" edges="{edges_str}"/>')
    route_lines.append(
        f'    <flow id="f{flow_id}" type="car" route="r{rid}" '
        f'begin="0" end="2000" probability="{prob:.2f}"/>'
    )
    flow_id += 1

# East-West through routes (one per row, both directions)
for row in range(ROWS):
    # West → East
    path = (f"W_{row}_to_{jid(0,row)} " +
            " ".join(f"{jid(c,row)}_to_{jid(c+1,row)}" for c in range(COLS-1)) +
            f" {jid(COLS-1,row)}_to_E_{row}")
    flow(f"WE_r{row}", path, 0.15)

    # East → West
    path = (f"E_{row}_to_{jid(COLS-1,row)} " +
            " ".join(f"{jid(c+1,row)}_to_{jid(c,row)}" for c in range(COLS-2, -1, -1)) +
            f" {jid(0,row)}_to_W_{row}")
    flow(f"EW_r{row}", path, 0.15)

# North-South through routes (one per col, both directions)
for col in range(COLS):
    # South → North
    path = (f"S_{col}_to_{jid(col,0)} " +
            " ".join(f"{jid(col,r)}_to_{jid(col,r+1)}" for r in range(ROWS-1)) +
            f" {jid(col,ROWS-1)}_to_N_{col}")
    flow(f"SN_c{col}", path, 0.10)

    # North → South
    path = (f"N_{col}_to_{jid(col,ROWS-1)} " +
            " ".join(f"{jid(col,r+1)}_to_{jid(col,r)}" for r in range(ROWS-2, -1, -1)) +
            f" {jid(col,0)}_to_S_{col}")
    flow(f"NS_c{col}", path, 0.10)

# Diagonal cross routes (West entry → North exit, etc.)
for row in range(ROWS):
    for col in range(COLS):
        # West entry row → North exit col (if path exists)
        if row < ROWS - 1:
            h_path = " ".join(f"{jid(c,row)}_to_{jid(c+1,row)}" for c in range(col))
            v_path = " ".join(f"{jid(col,r)}_to_{jid(col,r+1)}" for r in range(row, ROWS-1))
            if h_path and v_path:
                path = f"W_{row}_to_{jid(0,row)} {h_path} {v_path} {jid(col,ROWS-1)}_to_N_{col}"
                flow(f"WN_r{row}_c{col}", path, 0.03)

routes_xml = "<routes>\n" + "\n".join(route_lines) + "\n</routes>"
with open(DATA_DIR / "Traci.rou.xml", "w") as f:
    f.write(routes_xml)

# ══════════════════════════════════════════════════════════════════════
# 5. CONFIG
# ══════════════════════════════════════════════════════════════════════
config_xml = """\
<configuration>
    <input>
        <net-file value="Traci.net.xml"/>
        <route-files value="Traci.rou.xml"/>
    </input>
</configuration>"""
with open(DATA_DIR / "Traci.sumocfg", "w") as f:
    f.write(config_xml)

print(f"Done. Files written to: {DATA_DIR}")
print(f"Intersections: {COLS*ROWS}  |  Chromosome size: {COLS*ROWS*2} genes")