# Urban Traffic Optimizer
**Full Title:** Real-Time Big Data Analytics and Visualization for Urban Traffic Flow Optimization
### Description:
This project uses **SUMO** (Simulation of Urban MObility) to simulate traffic, which is then fed into a genetic algorithm implemented in Python via the **PyGAD** library to optimize traffic light timings across complex 
intersection networks. 
The goal is to **reduce congestion**, **improve throughput**, and **enable real-time visualization** of evolving traffic patterns.

# current functionality
### note: subject to regular updates.

## folders
###  sumo_data
Contains SUMO files:
- Traci.net.xml
    Defines the geometry of the network (edges, junctions, connections, traffic lights).
- Traci.netecfg
    Configures the behaviour and routing properties of the network
- Traci.rou.xml
    Defines the flow (from-to-edges, provides vehicles that cause congestion, which the GA (genetic algorithm) solves. Fitness function metrics are calculated by tracking the behaviour of the vehicles defined in this file).
- Traci.sumocfg
    Main config file that links the network and the routes (Traci.net.xml & Traci.rou.xml).

### src
Contains Traci1.py
- Executes SUMO simulation to completion and collects data from Traci.sumocfg.

- Future goal: genetic algorithm implementation.

### Summary
- Data is first generated with SUMO simulations (Traci.net.xml, Traci.rou.xml, Traci.netecfg, Traci.sumocfg, )
- Data is then manipulated and read to our liking with Traci1.py 

### Todolist
-- Import pyGAD and make genetic algorithm for Traci1.py, build fitness function.
