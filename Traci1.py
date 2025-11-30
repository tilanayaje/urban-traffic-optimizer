import os # Module provides functions to handle file paths, directories, environment variables
import sys # Module provides access to Python-specific system parameters and functions
#Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci # Static network information (such as reading and analyzing network files)

## No need to change anything above this. 
# Define Sumo configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'Traci.sumocfg', # file to read
    '--step-length', '0.05',
    '--delay', '200',
    '--lateral-resolution', '0.1'
]

#Open connection between SUMO and Traci
traci.start(Sumo_config)

#IMPORTANT: Define Variables 
vehicle_speed = 0
vehicle_position = (0, 0)
total_speed = 0

#IMPORTANT: Define Functions
def update_speed_and_position():
    """Fetches and prints speed and position for the first vehicle found."""
    global vehicle_speed, vehicle_position # Declare variables as global to modify them
    current_vehicles = traci.vehicle.getIDList()
    
    if current_vehicles:
        first_veh_id = current_vehicles[0]
        
        # Get Speed, Position (x, y) coordinates
        vehicle_speed = traci.vehicle.getSpeed(first_veh_id)
        vehicle_position = traci.vehicle.getPosition(first_veh_id)
        
        # Print combined information for demonstration
        print(f"Vehicle ID: {first_veh_id}")
        print(f"  Speed: {vehicle_speed:.2f} m/s")
        print(f"  Position (x, y): ({vehicle_position[0]:.2f}, {vehicle_position[1]:.2f})")
    else:
        # print("No vehicles currently in the network.")
        pass

# Step 8: Take simulation steps until there are no more vehicles in the network
# While Loop until no cars left
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() # Move simulation forward 1 step

    # use simulation data at each step
    # Free to change code beloe this line
    update_speed_and_position()
    # total_speed = total_speed + vehicle_speed # NOTE: If you use the global total_speed, 
                                            # this calculation should be moved inside the function.
                                            # For now, it is commented out for simplicity.
    # step_count = step_count + 1

# Step 9: Close connection between SUMO and Traci
traci.close()