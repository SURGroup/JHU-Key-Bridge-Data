## Written by Diran Jimenez
## Based on code written by Promit Chakroborty

import os
import numpy as np
import pandas as pd

# Each time a csv file is read it gives a warning about mixed data types
import warnings
warnings.filterwarnings("ignore")

# Ensure that this script is run from the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

from probability_calculator_by_pier import probability_calculator
from helper_functions_geometry_plotting import remove_ship_teleportation, direction, triangular_projection

# Full path to folder with bridge data
data_folder = ""

# Folder to store probability calculations
all_piers = False
probabilities_folder_name = ""
min_probabilities_folder = os.path.join(curr_folder, f"Min {probabilities_folder_name}")
max_probabilities_folder = os.path.join(curr_folder, f"Max {probabilities_folder_name}")

# Ensure the folder exists
if not os.path.exists(min_probabilities_folder):
    os.makedirs(min_probabilities_folder)
if not os.path.exists(max_probabilities_folder):
    os.makedirs(max_probabilities_folder)

# Load bridge parameters from CSV file
bridge_parameters_file = "All_Piers_and_Protections.xlsx"

bridge_data = pd.read_excel(os.path.join(curr_folder, bridge_parameters_file), header=0, 
                            converters={"START_X":float, "START_Y":float, "END_X": float, "END_Y":float}).dropna(inplace=False, how="all")

# Some bridges are ignored for various reasons, thus there should not be a reason for exclusion
good_bridges = bridge_data[bridge_data["Reason for Exclusion"].isna()].drop("Reason for Exclusion", axis=1)

bridge_names = list(set(good_bridges["STRUCTURE_NAME"].values))
num_bridges = len(bridge_names)

bridge_coordinates = {}
for b in bridge_names:
    b_df = good_bridges[good_bridges["STRUCTURE_NAME"] == b]
    bridge_coordinates[b] = np.array([[b_df["START_X"].values[0], b_df["START_Y"].values[0]],
                                      [b_df["END_X"].values[0], b_df["END_Y"].values[0]]])
    
# Only need these columns from the data:
desired_cols = ["LON", "LAT", "Length", "Width", "VesselType"]

# Each bridge will get a collision risk for the TRUE and FALSE traffic directions. Similarly for annual traffic
min_collision_risk = {bridge: {} for bridge in bridge_names}
max_collision_risk = {bridge: {} for bridge in bridge_names}
annual_traffic = {bridge: {} for bridge in bridge_names}


plotting = False # Enable to see plots of geometric probability and piers 

saving_results = True # Enable to output CSV files

for bridge in bridge_names:
    bridge_start, bridge_end = (bridge_coordinates[bridge][i] for i in range(2))
    
    resolution = 1/triangular_projection(bridge_start, bridge_end)
    
    # Prepare the traffic
    bridge_traffic = remove_ship_teleportation(pd.read_csv(os.path.join(data_folder, f"{bridge} Data.csv")))
    
    num_crossings = bridge_traffic.shape[0] // 2
    if num_crossings == 0:
        annual_traffic[bridge], max_collision_risk[bridge], min_collision_risk[bridge] = 0,0,0
        continue
      
    correct_bridge = good_bridges[good_bridges["STRUCTURE_NAME"] == bridge]
    
    correct_piers = all_piers | np.array(correct_bridge["MAIN_PIER_ADJACENT_TO_SHIP_CROSSINGS"] == "Y")
    
    pier_info = correct_bridge[correct_piers][["PIER_CENTER_LAT", "PIER_CENTER_LON", 
                                               "MAX_PIER_LENGTH_m", "MIN_PIER_LENGTH_m"]].drop_duplicates()
    
    min_piers_df = pier_info.copy().drop("MAX_PIER_LENGTH_m", axis=1).rename({"MIN_PIER_LENGTH_m":"LENGTH_m"}, axis=1)
    
    max_piers_df = pier_info.copy().drop("MIN_PIER_LENGTH_m", axis=1).rename({"MAX_PIER_LENGTH_m":"LENGTH_m"}, axis=1)
    
    dolphins_df = correct_bridge[~correct_bridge["DOLPHIN_CENTER_LON"].isna()][
        ["DOLPHIN_CENTER_LON", "DOLPHIN_CENTER_LAT", "DOLPHIN_DIAMETER_m"]].drop_duplicates()
  
    for traffic_direction in [True, False]:
        # The probability calculator outputs collision probability, followed by annual traffic in the traffic direction
        risk_with_min_pier_size, directed_annual_traffic = probability_calculator(bridge, bridge_start, bridge_end, bridge_traffic, 
                                                                                  min_piers_df.copy(), dolphins_df.copy(), traffic_direction, 
                                                                                  resolution, plotting)
        
        min_collision_risk[bridge][traffic_direction] = risk_with_min_pier_size
        
        
        
        annual_traffic[bridge][traffic_direction] = directed_annual_traffic
    
        max_collision_risk[bridge][traffic_direction] = probability_calculator(bridge, bridge_start, bridge_end, bridge_traffic, 
                                                                               max_piers_df.copy(), dolphins_df.copy(), traffic_direction, 
                                                                               resolution, plotting)[0]
        
        
        
# Now we go back through the list, and aggregate the probabilities as follows:
    # If a bridge stands alone, its risk is the sum of its risk along both traffic directions
    # If a bridge is parallel, combine the risk of of the traffic direction it faces with its parallel counterpart 
    
length_bin_names = np.array([[f"{l} - {l + 25} m"] for l in range(150,400,25)] + [["Above 400 m"]])
    # If we choose to save results, we'll need row names
    

for bridge in bridge_names:                                               # Since each bridge has a duplicate row per pier
    current_bridge = good_bridges[good_bridges["STRUCTURE_NAME"] == bridge].head(1)
    
    additional_bridge_notes = current_bridge["Additional Notes"].astype(str).values[0]
    
    if "parallel" not in additional_bridge_notes.lower():
                                          # Elementwise-add the collision risk matrices for both directions for both min and max footprints
        
        [min_risk_matrix_t, min_risk_matrix_f], [max_risk_matrix_t, max_risk_matrix_f] = ([risk_dictionary[bridge][d] for d in [True, False]]
                                                                                        for risk_dictionary in [min_collision_risk, max_collision_risk])
        
        if saving_results:
            
            for folder, matrices in zip([min_probabilities_folder, max_probabilities_folder],
                                        [[min_risk_matrix_t, min_risk_matrix_f],[max_risk_matrix_t, max_risk_matrix_f]]):
                
                for M, d in zip(matrices, [True, False]):
                    df = pd.DataFrame(np.concatenate((length_bin_names, M), axis=1), 
                                      columns = ["Ship Length"] + [f"Pier {i+1}" for i in range(M.shape[1])]).set_index("Ship Length")
                
                    df.to_csv(os.path.join(folder, f"{bridge}_{d}_Collision_Probabilities.csv"))
                
        min_bridge_risk = np.sum(min_risk_matrix_t + min_risk_matrix_f)
        max_bridge_risk = np.sum(max_risk_matrix_t + max_risk_matrix_f)
        
        min_collision_risk[bridge], max_collision_risk[bridge] = min_bridge_risk, max_bridge_risk
        
        traffic_both_ways = sum(annual_traffic[bridge][d] for d in [True, False])
        annual_traffic[bridge] = traffic_both_ways
        continue
    
    # We must have a parallel bridge if we've reached this line
    
    # Cut out the cardinal direction from the bridge name
        # e.g. N, SW, etc.
    # This will be the name for the pair of bridges

    parallel_bridges_with_non_standard_names = {
        "VETERANS_MEMORIAL_BRIDGE_(TX)": "RAINBOW_and_VETERANS_MEMORIAL_BRIDGE_(TX)",
        "RAINBOW_BRIDGE_(TX)": "RAINBOW_and_VETERANS_MEMORIAL_BRIDGE_(TX)",
        "CARQUINEZ_BRIDGE_(CA)": "CARQUINEZ_and_ALFRED_ZAMPA_MEMORIAL_BRIDGE_(CA)",
        "ALFRED_ZAMPA_MEMORIAL_BRIDGE_(CA)": "CARQUINEZ_and_ALFRED_ZAMPA_MEMORIAL_BRIDGE_(CA)",
        "BENICIA_MARTINEZ_BRIDGE_(CA)": "BENICIA_MARTINEZ_and_GEORGE_MILLER_JR_MEMORIAL_BRIDGE_(CA)",
        "GEORGE_MILLER_JR_MEMORIAL_BRIDGE_(CA)": "BENICIA_MARTINEZ_and_GEORGE_MILLER_JR_MEMORIAL_BRIDGE_(CA)",
        }
    
    underscore_indexes = [i for i in range(bridge.find("(")) if bridge[i] == "_"]
    
    true_bridge_name = parallel_bridges_with_non_standard_names.get(bridge,
                                                                    bridge[:underscore_indexes[-2]] + bridge[underscore_indexes[-1]:])
    
    # We will see this pair twice, so check if this is the first or second time
    if true_bridge_name in min_collision_risk:
        continue
    
    parallel_bridge_ID = additional_bridge_notes.split("_")[2]
                                                    # Expecting: "Parallel_to_ID_other notes...
                                                    
    parallel_bridge_info = good_bridges[good_bridges["UNIQUE_IDENTIFIER"] == parallel_bridge_ID].head(1)
    parallel_bridge_name = parallel_bridge_info["STRUCTURE_NAME"].astype(str).values[0]
    
    parallel_start = np.array([parallel_bridge_info["START_X"], parallel_bridge_info["START_Y"]]).flatten()
    parallel_end = np.array([parallel_bridge_info["END_X"], parallel_bridge_info["END_Y"]]).flatten()
    
    current_start = np.array([current_bridge["START_X"], current_bridge["START_Y"]]).flatten()
    current_end = np.array([current_bridge["END_X"], current_bridge["END_Y"]]).flatten()
    
    middle_start = 0.5 * (current_start + parallel_start)
    middle_end = 0.5 * (current_end + parallel_end)
    
    direction_for_current_bridge = direction(middle_start, middle_end, current_start, parallel_start)
    direction_for_parallel_bridge = not direction_for_current_bridge
    
    [correct_min_risk_here, correct_min_risk_parallel], [correct_max_risk_here, correct_max_risk_parallel] = ([risk_dict[bridge][direction_for_current_bridge], risk_dict[parallel_bridge_name][direction_for_parallel_bridge]]
                                                                                                              for risk_dict in [min_collision_risk, max_collision_risk])
    
    if saving_results:
        for folder, matrices in zip([min_probabilities_folder, max_probabilities_folder],
                                    [[correct_min_risk_here, correct_min_risk_parallel],
                                     [correct_max_risk_here, correct_max_risk_parallel]]):
        
            for M, d in zip(matrices, [direction_for_current_bridge, 
                                       direction_for_parallel_bridge]):
                
                df = pd.DataFrame(np.concatenate((length_bin_names, M), axis=1), 
                                  columns = ["Ship Length"] + [f"Pier {i+1}" for i in range(M.shape[1])]).set_index("Ship Length")
                
                df.to_csv(os.path.join(folder, f"{true_bridge_name}_{d}_Collision_Probabilities.csv"))
        
        
    correct_min_risk = correct_min_risk_here.sum() + correct_min_risk_parallel.sum()
    correct_max_risk = correct_max_risk_here.sum() + correct_max_risk_parallel.sum()
                                           # Some parallel bridges have a different number of piers
                                           
    correct_annual_traffic = annual_traffic[bridge][direction_for_current_bridge] + annual_traffic[parallel_bridge_name][direction_for_parallel_bridge]
    
    min_collision_risk[true_bridge_name] = correct_min_risk
    max_collision_risk[true_bridge_name] = correct_max_risk
    annual_traffic[true_bridge_name] = correct_annual_traffic
    
    # Drop the parallels from the dicts
    for dic in [min_collision_risk, max_collision_risk, annual_traffic]:
        dic.pop(bridge)
        dic.pop(parallel_bridge_name)
        

    
ranked_by_risk = list(sorted(min_collision_risk.keys(), key = lambda x: min_collision_risk[x], reverse = True))

minimum_likelihood_of_collision = 1/1000 # AASHTO Design Code

at_risk_bridges = sorted([bridge for bridge in min_collision_risk.keys() if min_collision_risk[bridge] >= minimum_likelihood_of_collision],
                         key = lambda x: min_collision_risk[x], reverse=True)

for i, bridge in enumerate(at_risk_bridges):
    print(f"{i+1}. {bridge}: {min_collision_risk[bridge]:.4f}")
    
print(f"Number of bridges with excessive AF: {len(at_risk_bridges)}")
