# Urban Traffic Optimizer
### **Full Title:** 🚦 🚗 Real-Time Big Data Analytics and Visualization for Urban Traffic Flow Optimization 💨💨
### Description:
This project uses **SUMO** (Simulation of Urban MObility) to simulate urban traffic flow.
**A Genetic Algorithm (PyGAD)** evolves traffic-light timings in real time while a **live dashboard** visualizes optimization progress
The system automatically generates a standardized traffic network, runs repeated SUMO simulations, evaluates congestion metrics, and evolves better signal timings.

Goal:
- Reduce congestion
- Improve throughput
- Visualize optimization in real time
- Create a reproducible traffic optimization pipeline

# current functionality
*note: subject to regular updates.*

### 🗂️ File structure
**📁src/**

_Core logic and optimization pipeline._

🔹 **build_network.py**

_Procedurally generates a standardized SUMO intersection (J11)._
Creates:
- Traci.net.xml (network geometry)
- Traci.rou.xml (traffic flows)
- Traci.sumocfg (simulation config)
    
🔹**eval_timings.py**

_Runs SUMO simulations via TraCI._
- Collects performance metrics:
- Throughput (arrived vehicles)
- Total waiting time
- Average speed
- Returns metrics for fitness evaluation
  
🔹**pygad_optimizer.py**

_Implements the Genetic Algorithm using PyGAD._

- Each chromosome represents a signal timing plan: [gA, gB]
- Runs full SUMO simulation per candidate
- Logs per-generation metrics to CSV
- Evolves better timing strategies over generations

**🔹 Traci1.py**

_Utility script for basic SUMO simulation execution (legacy/testing tool)._    

**📁 sumo_data/**

**🔹 generated/**

_Container for generated data._
Contains:
- Network files
- Route definitions
- SUMO configuration
- ga_history.csv (GA logging output)
  
- Traci.net.xml
    Defines the geometry of the network (edges, junctions, connections, traffic lights).
- Traci.netecfg
    Configures the behaviour and routing properties of the network
- Traci.rou.xml
    Defines the flow (from-to-edges, provides vehicles that cause congestion, which the GA (genetic algorithm) solves. Fitness function metrics are calculated by tracking the behaviour of the vehicles defined in this file).
- Traci.sumocfg
    Main config file that links the network and the routes (Traci.net.xml & Traci.rou.xml).

**📁 Root folder/**

🔹 dashboard.py
_Real-time Streamlit dashboard with metrics._

### Summary and how to run
System runs end-to-end: SUMO → GA → CSV → Dashboard.
_Note: pictures here will be replaced before project is complete_
<img width="1375" height="594" alt="image" src="https://github.com/user-attachments/assets/e569fd74-0ece-487f-9e60-acb8a3061c83" />
<img width="537" height="282" alt="image" src="https://github.com/user-attachments/assets/54d39b83-7ed5-4d28-8bc4-92721fa6bd3a" />

### How to run:
1. py build_network.py
2. py pygad_optimizer.py
3. streamlit run dashboard.py (or py -m streamlit run dashboard.py)


## Optimization Model
Current optimization model: Currently optimizes one single intersection:

        [gA, gB]

gA = green duration for phase A.
gB = green duration for phase B.
Yellow phases remain fixed.

Fitness currently balances throughput and waiting time.

## Todolist

-- Improve GA convergence

-- Tune mutation + fitness weighting

-- Increase generations

-- Stabilize metrics

-- Multi-intersection chromosome

-- Larger network geometry

-- Multi-objective fitness

-- Performance optimization ?
