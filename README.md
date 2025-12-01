# urban-traffic-optimizer
### **Full Title:** Real-Time Big Data Analytics and Visualization for Urban Traffic Flow Optimization

This project uses **SUMO** (Simulation of Urban MObility) to simulate traffic, which is then fed into a genetic algorithm implemented in Python via the **PyGAD** library to optimize traffic light timings across complex 
intersection networks. 

The goal is to **reduce congestion**, **improve throughput**, and **enable real-time visualization** of evolving traffic patterns.

# current functionality
### note: subject to regular updates.
- Data is first generated with SUMO simulations (Traci.net.xml, Traci.rou.xml, Traci.netecfg, Traci.sumocfg, )

- Data is then manipulated and read to our liking with Traci1.py 

### Todolist
-- Import pyGAD and make genetic algorithm for Traci1.py, build fitness function.
