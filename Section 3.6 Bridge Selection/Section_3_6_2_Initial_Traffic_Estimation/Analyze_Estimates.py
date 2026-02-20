## Written by Diran Jimenez

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure the current directory is the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

vicinity_traffic_estimation_file = "Vicinity_Traffic_Estimation.csv"
valid_bridge_file = "Bridges_that_pass_NBI_filters.csv"
valid_bridges = pd.read_csv(valid_bridge_file)

estimate_df = pd.read_csv(vicinity_traffic_estimation_file,
                          dtype={"UNIQUE_IDENTIFIER": str}) # To prevent interpretation from removing leading zeros

def convert_coords(coordinate, lon_indicator):
    # Convert coordinates from Integer Format to decimal degrees:
        # Int EX: (Lat, 41421215), (Lon, 073570204)
        # Out EX: (Lat, 41.703375), (Lon, -73.95056666666667)
    
    coordinate = coordinate.lstrip(" ").rstrip(" ")
    num_digits = len(coordinate)
    correct_number = 8 + lon_indicator
    
    coordinate += "0" * (correct_number - num_digits)
    
    degrees = coordinate[:2+lon_indicator]
    
    minutes = coordinate[2+lon_indicator:4+lon_indicator]
    
    seconds = coordinate[4+lon_indicator:]
    
    sign = 1 * (not lon_indicator) + -1 * (lon_indicator)
    return sign * (float(degrees) + float(minutes)/60 + float(seconds)/(60*60*100))


# Plot how many bridges achieve varying threshold levels of traffic
def analyze_traffic(bridges_to_analyze, estimate_df, vertical_scale,
                    min_traffic, max_traffic, step_size, num_years_of_data):
    
    # Pull the bridges you'd like to look at out of the dataframe with traffic estimations
    analysis_df = estimate_df[estimate_df["UNIQUE_IDENTIFIER"].apply(lambda x: x in bridges_to_analyze)]
    
    all_bridges, all_traffic = (analysis_df[col].values for col in ["UNIQUE_IDENTIFIER", "NUM_NEARBY_SHIPS"])
    
    traffic_levels = np.arange(min_traffic, max_traffic, step_size)
    
    heights = []
    
    for l in traffic_levels:
        threshold_bridges = set(all_bridges[(all_traffic / num_years_of_data) >= l])
        heights.append(len(threshold_bridges))

    
    plt.bar(traffic_levels, heights, width=step_size)
    plt.xlabel("Threshold Number of Ships that get 'close' / Year")
    plt.ylabel("Number of Bridges with at least X level of traffic")
    plt.title("Proportion of bridges with threshold level of traffic")
    plt.vlines(160, 0, max(heights), color="black", label="Conservative Threshold")
    
    plt.yscale(vertical_scale)
        
    plt.show()
    
    risky_list = (all_traffic / num_years_of_data) >= 160
    return set(analysis_df[risky_list]["UNIQUE_IDENTIFIER"].values)

step_size = 1
min_traffic = 0 + step_size
max_traffic = 200 # For plotting purposes, cutoff the graph at 200
num_years_of_data = 10 # 2015 - 2024

v_bridges = valid_bridges["UNIQUE_IDENTIFIER"].values


risky_list = analyze_traffic(v_bridges, estimate_df, "linear", 
                             min_traffic, max_traffic, step_size, num_years_of_data)

vicinity_traffic_dict = estimate_df.set_index("UNIQUE_IDENTIFIER").to_dict("index")

# When manually collecting coordinates, we'll need:
#   - The lat/lon of the "start" of the bridge (a single point at the edge of the waterway for a bridge)
#   - The lat/lon of the "end" of the bridge (same as above, but the opposite side of the waterway)
#   - The "Structure Name," which refers to the colloquial or human-readable name for a bridge (e.g. Francis Scott Key Bridge)

# We'll also want to extra columns for notes:
#   - One for when the bridge can be eliminated by visual observation (e.g. the bridge is obviously too short to handle large ship traffic)
#   - An additional notes section for any miscellaneous observations
some_extra_columns = [
    "STRUCTURE_NAME", 
    "START_Y", 
    "START_X", 
    "END_Y", 
    "END_X", 
    "Reason for Exclusion", 
    "Additional Notes"
]

for col in some_extra_columns:
    valid_bridges[col] = ["" for bridge in v_bridges]
    
# Adjust the lat/lon values to something copy-pastable into google earth (as opposed to the integer format it defaults to)
valid_bridges["NBI_LAT"] = valid_bridges["LAT_016"].astype(str).apply(convert_coords, args = (False,)).values
valid_bridges["NBI_LON"] = valid_bridges["LONG_017"].astype(str).apply(convert_coords, args = (True,)).values

risky_df = valid_bridges[valid_bridges["UNIQUE_IDENTIFIER"].apply(lambda x: (x in risky_list))]

risky_df.to_excel("Raw_Master_Bridge_Information.xlsx", index=False)

