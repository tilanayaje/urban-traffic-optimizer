# Urban Traffic Optimizer
### **Full Title:** 🚦 🚗 Real-Time Big Data Analytics and Visualization for Urban Traffic Flow Optimization 💨💨
### Description:
This project uses **SUMO** (Simulation of Urban MObility) to simulate traffic, which is then fed into a genetic algorithm implemented in Python via the **PyGAD** library to optimize traffic light timings across complex 
intersection networks. 
The goal is to **reduce congestion**, **improve throughput**, and **enable real-time visualization** of evolving traffic patterns.

# current functionality
*note: subject to regular updates.*

### folders
**sumo_data**
(note .route.xml and .net.xml are hidden via .gitignore)
- Traci.net.xml
    Defines the geometry of the network (edges, junctions, connections, traffic lights).
- Traci.netecfg
    Configures the behaviour and routing properties of the network
- Traci.rou.xml
    Defines the flow (from-to-edges, provides vehicles that cause congestion, which the GA (genetic algorithm) solves. Fitness function metrics are calculated by tracking the behaviour of the vehicles defined in this file).
- Traci.sumocfg
    Main config file that links the network and the routes (Traci.net.xml & Traci.rou.xml).
  
**src**
- Traci1.py: 
    Executes SUMO simulation to completion and collects data from Traci.sumocfg.
- eval_timings.py
    Runs SUMO repeatedly while modifying traffic light timings. Evaluates congestion metrics and is used by the genetic algorithm.
- pygad_optimizer.py
    Uses PyGAD to evolve traffic light phase durations.
    Each chromosome represents a timing plan, which is evaluated by running a full SUMO simulation.

- Future goal: genetic algorithm implementation.

### Summary
- Data is first generated with SUMO simulations (Traci.net.xml, Traci.rou.xml, Traci.netecfg, Traci.sumocfg).
- Data is then accessed/manipulated through Python using TraCI.
- runs automated SUMO simulations
- modifies signal timings programmatically
- evaluates congestion metrics
- evolves better timing plans via a genetic algorithm

## Optimization Model
Current optimization model: Currently optimizes one single intersection:

        [gA, gB]

gA = green duration for phase A.
gB = green duration for phase B.
yellow phases remain fixed.
Fitness currently balances throughput and waiting time.

### Todolist
-- refine PyGAD parameter tuning
-- reduce runtime per GA generation
-- expand chromosome to multiple intersections
-- add visualization of optimization progress
-- log best timing configurations
-- support real-time traffic visualization
-- coordinate multiple traffic lights
-- experiment with multi-objective optimization