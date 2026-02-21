## Written by Diran Jimenez
## Adapted from code written by Promit Chakroborty

import os

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import scipy.stats as stats

# Ensure that this script is run from the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

from helper_functions import (
    triangular_projection, 
    direction,
    find_intersection,
    normalize_coordinate,
    remove_ship_teleportation
)


def intersection_analysis(normalized_intersections):
    # num_bins = int(np.sqrt(len(normalized_intersections)))
    # counts, bins, = np.histogram(normalized_intersections, bins= num_bins )
    counts, bins, = np.histogram(normalized_intersections, 
                                 bins=np.linspace(0,1,num=200))
    
    bin_starts = bins[:-1]
    bin_ends = bins[1:]
    bin_centers = 0.5 * (bin_starts + bin_ends)
    
    travel_centerline_indices, _ = find_peaks(counts, prominence = np.max(counts) * 0.25,
                                              distance=20)
    # travel_centerline_indices, _ = find_peaks(counts, prominence = np.max(counts) * 0.25)
    travel_centers = bin_centers[travel_centerline_indices]
    
    return [counts, bin_starts, bin_ends, bin_centers,
            travel_centerline_indices, travel_centers]
    

# Full path to folder with bridge data
data_folder = ""

# Load bridge parameters from CSV file
bridge_parameters_file = "Master_Bridge_Information.xlsx"

bridge_data = pd.read_excel(bridge_parameters_file, header=0, # index_col = 0,
                            usecols=["STRUCTURE_NAME", "START_X", "START_Y","END_X", "END_Y", "Reason for Exclusion"],
                            converters={"START_X":float, "START_Y":float, "END_X": float, "END_Y":float})

# Some bridges are ignored for various reasons, thus there should not be a reason for exclusion
good_bridges = bridge_data[bridge_data["Reason for Exclusion"].isna()].drop("Reason for Exclusion", axis=1).set_index("STRUCTURE_NAME")

# Turn the dataframe into an appropriate dictionary
dict_bridges = good_bridges.loc[:, ["START_X", "START_Y","END_X", "END_Y"]].transpose().to_dict('list')

# Make the values more usable by turning them into appropriately shaped arrays
bridge_coordinates = {bridge: np.array(dict_bridges[bridge]).reshape(2,2) for bridge in dict_bridges}

bridge_names = list(bridge_coordinates.keys())
num_bridges = len(bridge_names)

# Only need these columns from the data:
desired_cols = ["BaseDateTime", "LON", "LAT", "Length", "Width", "VesselType"]

base_aberrancy = 0.6 * 1e-4 # Base aberrancy rate as per Section 3.14.5.2.3 of the AASHTO design code

length_min, length_max, length_step = 150, 400, 25 # meters
length_bins = [(0,length_min)] + [(i,i+length_step) for i in range(length_min, length_max, length_step)] + [(length_max, 100_000)]

cargo_tanker_types = [70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 1004, 1016,
                      80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 1017, 1024]

### Calculate collision probability ###
results = {}
traffic_by_bridge = {}

bridges_with_no_traffic = 0

for bridge in bridge_names:
    
    traffic_df = remove_ship_teleportation(pd.read_csv(os.path.join(data_folder, f"{bridge} Data.csv"), usecols=desired_cols))
    
    
    if traffic_df.shape[0] == 0:
        results[bridge] = 0
        bridges_with_no_traffic += 1
        continue
    
    bridge_start = bridge_coordinates[bridge][0]
    bridge_end = bridge_coordinates[bridge][1]
    bridge_middle = 0.5 * (bridge_start + bridge_end)
    waterway_length_meters = triangular_projection(bridge_start, bridge_end)
    
    
    num_crossings = traffic_df.shape[0] // 2 # Each crossing is always 2 points
    traffic_by_bridge[bridge] = num_crossings / 10 # Annual, 10 years of data    
    
    
    crossing_starts = np.zeros((num_crossings,2))
    crossing_ends = np.zeros((num_crossings,2))
    
    crossing_starts[:,0] = traffic_df["LON"].values[:-1:2]
    crossing_starts[:,1] = traffic_df["LAT"].values[:-1:2]
    crossing_ends[:,0]   = traffic_df["LON"].values[1::2]
    crossing_ends[:,1]   = traffic_df["LAT"].values[1::2]
    
    
    crossing_directions = np.array([direction(bridge_start, bridge_end, 
                                              crossing_starts[i], crossing_ends[i])
                                    for i in range(num_crossings)])
    
    collision_probability = 0 
    
    # Calculate the probability based on traffic from each direction
    for traffic_direction in [True, False]:
        
        directed_crossing_starts, directed_crossing_ends = (points[crossing_directions == traffic_direction]
                                                            for points in (crossing_starts, crossing_ends))
        
        
        lengths, widths = (traffic_df[col].values[::2][crossing_directions == traffic_direction]
                           for col in ["Length", "Width"])
        
        linear_intersections = np.array([find_intersection(bridge_start, bridge_end, start, end)
                                         for start,end in zip(directed_crossing_starts, directed_crossing_ends)])
        
        normals = np.array([normalize_coordinate(point[0], point[1], bridge_start, bridge_end)
                            for point in linear_intersections])
        
        counts, bin_starts, bin_ends, bin_centers, travel_centerline_indices, travel_centers = intersection_analysis(normals)
        
        
        # SUPER ARBITRARY, VIBES BASED
        pier_indicator = counts <= max(counts) * 0.01
        
        for length_bin in length_bins:
            correct_length_crossings = (lengths >= length_bin[0]) & (lengths < length_bin[1])
            number_length_crossings = sum(correct_length_crossings)
            
            
            if number_length_crossings == 0:
                continue
            
            ship_width, ship_length = (np.nanmean(series[correct_length_crossings]) / waterway_length_meters for series in [widths, lengths])
            
            _, _, _, _, _, l_travel_centers = intersection_analysis(normals[correct_length_crossings])
            
            middles = [0] + list(0.5 * (l_travel_centers[1:] + l_travel_centers[:-1])) + [1]
            weight_bins = [[middles[i], middles[i+1]] for i in range(len(middles)-1)]
            
            geom_probability = 0
            
            for i in range(len(l_travel_centers)):
                distribution = stats.norm(loc=l_travel_centers[i], scale = ship_length)
                weight = np.sum( (normals[correct_length_crossings] >= weight_bins[i][0])
                               & (normals[correct_length_crossings] <  weight_bins[i][1]) ) / number_length_crossings
                
                # In case there's no traffic for this bin, use nanmax to compare to 0
                geom_probability += np.nanmax([np.trapz(distribution.pdf(bin_centers) * pier_indicator, bin_centers) * weight,
                                              0])
                
            collision_probability += number_length_crossings * base_aberrancy * geom_probability * 0.1 # Annual, divide by number of years

    results[bridge] = collision_probability
        

minimum_likelihood_of_collision = 1/10_000

at_risk_bridges = sorted([bridge for bridge in bridge_names if results[bridge] >= minimum_likelihood_of_collision],
                         key = lambda x: results[x], reverse=True)


for i, bridge in enumerate(at_risk_bridges):
    print(f"{i+1}. {bridge}: {results[bridge]:.4f}")
    
print(f"Number of bridges with excessive AF: {len(at_risk_bridges)}")

keep = good_bridges[good_bridges["STRUCTURE_NAME"].isin(at_risk_bridges)]
keep.to_excel("raw_All_Piers_and_Protections")


