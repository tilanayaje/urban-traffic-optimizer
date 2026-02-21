import os
import subprocess
from sumolib import checkBinary

# 1. Setup the data directory
data_dir = os.path.join(os.path.dirname(__file__), "..", "sumo_data")
os.makedirs(data_dir, exist_ok=True)

print("Generating Custom SUMO Network for J11...")

# 2. Create the Nodes (The intersections and endpoints)
nodes_xml = """<nodes>
    <node id="J11" x="0.0" y="0.0" type="traffic_light"/>
    <node id="North" x="0.0" y="200.0" type="priority"/>
    <node id="South" x="0.0" y="-200.0" type="priority"/>
    <node id="East" x="200.0" y="0.0" type="priority"/>
    <node id="West" x="-200.0" y="0.0" type="priority"/>
</nodes>"""

with open(os.path.join(data_dir, "nodes.nod.xml"), "w") as f:
    f.write(nodes_xml)

# 3. Create the Edges (The roads connecting the nodes)
edges_xml = """<edges>
    <edge id="N2J" from="North" to="J11" priority="1" numLanes="2" speed="13.89"/>
    <edge id="J2S" from="J11" to="South" priority="1" numLanes="2" speed="13.89"/>
    <edge id="S2J" from="South" to="J11" priority="1" numLanes="2" speed="13.89"/>
    <edge id="J2N" from="J11" to="North" priority="1" numLanes="2" speed="13.89"/>
    <edge id="E2J" from="East" to="J11" priority="1" numLanes="2" speed="13.89"/>
    <edge id="J2W" from="J11" to="West" priority="1" numLanes="2" speed="13.89"/>
    <edge id="W2J" from="West" to="J11" priority="1" numLanes="2" speed="13.89"/>
    <edge id="J2E" from="J11" to="East" priority="1" numLanes="2" speed="13.89"/>
</edges>"""

with open(os.path.join(data_dir, "edges.edg.xml"), "w") as f:
    f.write(edges_xml)

# 4. Compile the map into Traci.net.xml using SUMO's netconvert
netconvert_binary = checkBinary('netconvert')
subprocess.run([
    netconvert_binary, 
    "--node-files", os.path.join(data_dir, "nodes.nod.xml"),
    "--edge-files", os.path.join(data_dir, "edges.edg.xml"),
    "--output-file", os.path.join(data_dir, "Traci.net.xml")
], check=True)

# 5. Generate the Traffic Routes (Cars driving through)
routes_xml = """<routes>
    <vType id="car" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2" maxSpeed="15"/>
    <route id="route_NS" edges="N2J J2S"/>
    <route id="route_SN" edges="S2J J2N"/>
    <route id="route_EW" edges="E2J J2W"/>
    <route id="route_WE" edges="W2J J2E"/>
    
    <flow id="flow_NS" type="car" route="route_NS" begin="0" end="1000" probability="0.1"/>
    <flow id="flow_SN" type="car" route="route_SN" begin="0" end="1000" probability="0.1"/>
    <flow id="flow_EW" type="car" route="route_EW" begin="0" end="1000" probability="0.15"/>
    <flow id="flow_WE" type="car" route="route_WE" begin="0" end="1000" probability="0.15"/>
</routes>"""

with open(os.path.join(data_dir, "Traci.rou.xml"), "w") as f:
    f.write(routes_xml)

# 6. Generate the Config File
config_xml = """<configuration>
    <input>
        <net-file value="Traci.net.xml"/>
        <route-files value="Traci.rou.xml"/>
    </input>
</configuration>"""

with open(os.path.join(data_dir, "Traci.sumocfg"), "w") as f:
    f.write(config_xml)

print(" Success! The 'J11' network and traffic data have been generated in the sumo_data folder.")