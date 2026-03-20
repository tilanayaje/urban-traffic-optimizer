import os
import subprocess
from pathlib import Path
from sumolib import checkBinary

ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "sumo_data" / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Generating 3-intersection corridor network...")

# ---- Nodes ----
nodes_xml = """\
<nodes>
    <node id="J1" x="0.0"    y="0.0"    type="traffic_light"/>
    <node id="J2" x="400.0"  y="0.0"    type="traffic_light"/>
    <node id="J3" x="800.0"  y="0.0"    type="traffic_light"/>

    <node id="West" x="-200.0"  y="0.0"    type="priority"/>
    <node id="East" x="1000.0"  y="0.0"    type="priority"/>

    <node id="N1" x="0.0"    y="200.0"  type="priority"/>
    <node id="S1" x="0.0"    y="-200.0" type="priority"/>
    <node id="N2" x="400.0"  y="200.0"  type="priority"/>
    <node id="S2" x="400.0"  y="-200.0" type="priority"/>
    <node id="N3" x="800.0"  y="200.0"  type="priority"/>
    <node id="S3" x="800.0"  y="-200.0" type="priority"/>
</nodes>"""

with open(DATA_DIR / "nodes.nod.xml", "w") as f:
    f.write(nodes_xml)

# ---- Edges ----
edges_xml = """\
<edges>
    <edge id="W2J1"  from="West" to="J1"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J12J2" from="J1"   to="J2"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J22J3" from="J2"   to="J3"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J32E"  from="J3"   to="East" priority="2" numLanes="2" speed="13.89"/>

    <edge id="E2J3"  from="East" to="J3"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J32J2" from="J3"   to="J2"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J22J1" from="J2"   to="J1"   priority="2" numLanes="2" speed="13.89"/>
    <edge id="J12W"  from="J1"   to="West" priority="2" numLanes="2" speed="13.89"/>

    <edge id="N12J1" from="N1" to="J1"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J12S1" from="J1" to="S1"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="S12J1" from="S1" to="J1"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J12N1" from="J1" to="N1"   priority="1" numLanes="2" speed="13.89"/>

    <edge id="N22J2" from="N2" to="J2"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J22S2" from="J2" to="S2"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="S22J2" from="S2" to="J2"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J22N2" from="J2" to="N2"   priority="1" numLanes="2" speed="13.89"/>

    <edge id="N32J3" from="N3" to="J3"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J32S3" from="J3" to="S3"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="S32J3" from="S3" to="J3"   priority="1" numLanes="2" speed="13.89"/>
    <edge id="J32N3" from="J3" to="N3"   priority="1" numLanes="2" speed="13.89"/>
</edges>"""

with open(DATA_DIR / "edges.edg.xml", "w") as f:
    f.write(edges_xml)

# ---- netconvert ----
netconvert = checkBinary("netconvert")
subprocess.run([
    netconvert,
    "--node-files", str(DATA_DIR / "nodes.nod.xml"),
    "--edge-files", str(DATA_DIR / "edges.edg.xml"),
    "--output-file", str(DATA_DIR / "Traci.net.xml"),
], check=True)

# ---- Routes ----
routes_xml = """\
<routes>
    <vType id="car" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2" maxSpeed="15"/>

    <route id="route_WE"   edges="W2J1 J12J2 J22J3 J32E"/>
    <route id="route_EW"   edges="E2J3 J32J2 J22J1 J12W"/>
    <route id="route_N1S1" edges="N12J1 J12S1"/>
    <route id="route_S1N1" edges="S12J1 J12N1"/>
    <route id="route_N2S2" edges="N22J2 J22S2"/>
    <route id="route_S2N2" edges="S22J2 J22N2"/>
    <route id="route_N3S3" edges="N32J3 J32S3"/>
    <route id="route_S3N3" edges="S32J3 J32N3"/>
    <route id="route_W2N2" edges="W2J1 J12J2 J22N2"/>
    <route id="route_W2S3" edges="W2J1 J12J2 J22J3 J32S3"/>
    <route id="route_E2N1" edges="E2J3 J32J2 J22J1 J12N1"/>
    <route id="route_E2S2" edges="E2J3 J32J2 J22S2"/>

    <flow id="flow_WE"   type="car" route="route_WE"   begin="0" end="1500" probability="0.18"/>
    <flow id="flow_EW"   type="car" route="route_EW"   begin="0" end="1500" probability="0.18"/>
    <flow id="flow_N1S1" type="car" route="route_N1S1" begin="0" end="1500" probability="0.08"/>
    <flow id="flow_S1N1" type="car" route="route_S1N1" begin="0" end="1500" probability="0.08"/>
    <flow id="flow_N2S2" type="car" route="route_N2S2" begin="0" end="1500" probability="0.10"/>
    <flow id="flow_S2N2" type="car" route="route_S2N2" begin="0" end="1500" probability="0.10"/>
    <flow id="flow_N3S3" type="car" route="route_N3S3" begin="0" end="1500" probability="0.08"/>
    <flow id="flow_S3N3" type="car" route="route_S3N3" begin="0" end="1500" probability="0.08"/>
    <flow id="flow_W2N2" type="car" route="route_W2N2" begin="0" end="1500" probability="0.05"/>
    <flow id="flow_W2S3" type="car" route="route_W2S3" begin="0" end="1500" probability="0.05"/>
    <flow id="flow_E2N1" type="car" route="route_E2N1" begin="0" end="1500" probability="0.05"/>
    <flow id="flow_E2S2" type="car" route="route_E2S2" begin="0" end="1500" probability="0.05"/>
</routes>"""

with open(DATA_DIR / "Traci.rou.xml", "w") as f:
    f.write(routes_xml)

# ---- Config ----
config_xml = """\
<configuration>
    <input>
        <net-file value="Traci.net.xml"/>
        <route-files value="Traci.rou.xml"/>
    </input>
</configuration>"""

with open(DATA_DIR / "Traci.sumocfg", "w") as f:
    f.write(config_xml)

print("Done. Network written to:", DATA_DIR)