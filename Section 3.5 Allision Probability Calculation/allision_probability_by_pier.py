## Written by Diran Jimenez

import os
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Make sure the file is run from this file's location
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

from helper_functions import (
    triangular_projection, 
    direction,
    side,
    find_intersection,
    normalize_coordinate,
    locate_channel_center,
    normalized_pier_center_location,
    pier_protection,
    bridges_with_multiple_travel_lanes
)

def probability_calculator(bridge_name, bridge_start, bridge_end, bridge_traffic, 
                           piers_df, dolphins_df, traffic_direction, resolution,
                           plotting):

    """
    bridge_start: [LON, LAT] = [float, float]
        The LON and coordinates of the start of the bridge
        units = decimal degrees
    
    bridge_traffic: DataFrame
        DataFrame where each pair of rows represents the AIS 
        broadcasts of a ship just before and after crossing
        this bridge
        
    piers_df: DataFrame
        Contains all the piers for a bridge, including LAT, LON, and width
        
    dolphins_df: DataFrame
        Contains all the piers for a bridge, including LAT, LON, and width
        
    traffic_direction: bool
        The "direction" of traffic. 
            TRUE <-- traffic moves from the 'positive' side to 'negative' side
            FALSE <-- opposite, negative to positive
    
    resolution: float
        Step size when discretizing values
        
    plotting: bool
        Whether to draw various plots
        Turn on while debugging, off to save time
    """
    
    if plotting: 
        print(bridge_name)
        
    num_crossings = bridge_traffic.shape[0] // 2
    
        
    crossing_starts = np.zeros((num_crossings,2))
    crossing_ends = np.zeros((num_crossings,2))
    
    crossing_starts[:,0] = bridge_traffic["LON"].values[:-1:2]
    crossing_starts[:,1] = bridge_traffic["LAT"].values[:-1:2]
    crossing_ends[:,0]   = bridge_traffic["LON"].values[1::2]
    crossing_ends[:,1]   = bridge_traffic["LAT"].values[1::2]
    
    # We are only concerned with traffic in one direction
    crossing_directions = np.array([direction(bridge_start, bridge_end, 
                                              crossing_starts[i], crossing_ends[i])
                                    for i in range(num_crossings)])
    
    incoming_direction = (crossing_directions == traffic_direction)
    
    incoming_starts, incoming_ends = (points[incoming_direction]
                                      for points in (crossing_starts, crossing_ends))
    
    
    # Traffic goes from 2015 to 2024
    num_years_of_data = 10
        # This is hard coded since it is impossible to determine solely from a bridge's traffic data    
        # A bridge may have no traffic in one year, len(set(years)) would give the wrong value
        # If a bridge saw no traffic in the earliest or latest year, max(years) - min(years) + 1 wouldn't work either
    
    directed_annual_traffic = len(incoming_starts) / num_years_of_data
    
                                               # This needs to match the shape of incoming crossings
    lengths, widths = (bridge_traffic[col].values[::2][incoming_direction] # Assume a ship's length and width don't change between consecutive broadcasts
                       for col in ["Length", "Width"]) 
    
    # A linear interpolation between consecutive broadcasts is assumed
    linear_intersections = np.array([find_intersection(bridge_start, bridge_end, start, end)
                                     for start,end in zip(incoming_starts, incoming_ends)])
    
    normals = np.array([normalize_coordinate(point[0], point[1], bridge_start, bridge_end)
                        for point in linear_intersections])
    
    pier_Xs, pier_Ys, pier_Ws = (piers_df[col].values for col in 
                                 ["PIER_CENTER_LON", "PIER_CENTER_LAT", "LENGTH_m"])

    waterway_length_meters = triangular_projection(bridge_start, bridge_end)
    
    pier_Ws /= waterway_length_meters
  
    dolphin_Xs, dolphin_Ys, dolphin_Ws = (dolphins_df[col].values
                                          for col in ["DOLPHIN_CENTER_LON", "DOLPHIN_CENTER_LAT", "DOLPHIN_DIAMETER_m"]) 
    
    dolphin_Ws /= waterway_length_meters
    
    # a "TRUE" direction of traffic indicates moving from the 'negative' side of the bridge to the 'positive' side
        # Thus, a dolphin protects against "TRUE" traffic if it's on the negative side of the bridge
        # Vice versa for "FALSE" traffic
    facing_traffic = (side(bridge_start, bridge_end, dolphin_Xs, dolphin_Ys) < 0) == traffic_direction
    
    num_piers = len(pier_Ws)


    """
    To calculate the probability of collision for a bridge, 
    the probability of collision for each pier is summed together. 
    A pier's prob. of coll. is calculated by consider the risk
    from ships between DWT_i and DWT_(i+1). Since DWT is unnavailable,
    length is used instead. 
    """
    
    prob_aberrancy = 0.6 * 1e-4 # Base aberrancy rate as per Section 3.14.5.2.3 of the AASHTO design code

    length_min, length_max, length_step = 150, 400, 25 # meters                                                            # Assume no ship is longer than 100 km  
    length_bins = [(i,i+length_step) for i in range(length_min, length_max, length_step)] + [(length_max, 100_000)]
    
    collision_probability_matrix = np.zeros((len(length_bins), num_piers))
    
    # If there are no crossings in this direction, the probability of collision is 0
    if len(incoming_starts) == 0:
        return [collision_probability_matrix, directed_annual_traffic]
    
    potential_travel_centers = locate_channel_center(normals, resolution)
    
    # If a bridge has multiple travel lanes, use that. Otherwise, use the computer's answer
    travel_centers = bridges_with_multiple_travel_lanes.get(bridge_name, {traffic_direction: potential_travel_centers})[traffic_direction]
                                                                        # This is a default value to use if the bridge isn't in the multiple lane dictionary
        
    for row, length_bin in enumerate(length_bins):
        correct_length_crossings = (lengths >= length_bin[0]) & (lengths < length_bin[1])
        number_length_crossings = sum(correct_length_crossings)
        
        # If there are no crossings in a length bin, there's no risk of collision
        if number_length_crossings == 0:
            continue
        
        avg_ship_width, avg_ship_length = (np.nanmean(series[correct_length_crossings]) / waterway_length_meters for series in [widths, lengths])
        
        # Determine which ships should be considered for each travel lane
        ship_splits = [0] + list(0.5 * (travel_centers[1:] + travel_centers[:-1])) + [1]
        """
            If there's only one travel lane, all ships crossing from 0 to 1 are included in that lane
            Now suppose there's a travel lane at 0.25, and another at 0.75
            Ships crossing from 0 - 0.5 should be considered for that lane, and 0.5-1 for the other
        """
        
        weight_bins = [[ship_splits[i], ship_splits[i+1]] for i in range(len(ship_splits)-1)]
        
        for p in range(num_piers):
            center = normalized_pier_center_location(bridge_start, bridge_end, [pier_Xs[p], pier_Ys[p]])
            
            protection_factor = pier_protection(pier_Xs[p], pier_Ys[p], bridge_start, bridge_end, avg_ship_width, waterway_length_meters,
                                              *[d[facing_traffic] for d in [dolphin_Xs, dolphin_Ys, dolphin_Ws]])
            
            right_bound = min(1,center + pier_Ws[p]/2 + avg_ship_width/2)
            left_bound = max(0,center - pier_Ws[p]/2 - avg_ship_width/2)
            
            for i in range(len(travel_centers)):
                distribution = stats.norm(loc=travel_centers[i], scale = avg_ship_length)
                weight = np.sum( (normals[correct_length_crossings] >= weight_bins[i][0])
                               & (normals[correct_length_crossings] <  weight_bins[i][1]) ) / number_length_crossings
                
                
                prob_geometric = (distribution.cdf(right_bound) - distribution.cdf(left_bound)) * weight
                collision_probability_matrix[row,p] += number_length_crossings * prob_aberrancy * prob_geometric * (1 - protection_factor) / num_years_of_data # Annual, divide by number of years
            
                if plotting and (number_length_crossings > 10):
                    points = np.arange(0,1.01,0.01)
                    plt.plot(points, distribution.pdf(points), c="black")
                    plt.axvline(travel_centers[i], c="black", linestyle="dashed")
                    
           
            if plotting and (number_length_crossings > 10):
                plt.bar(center,  (1 - protection_factor), width= pier_Ws[p], label=f"{collision_probability_matrix[row,p]:.3e}")
                

        if plotting and (number_length_crossings > 10):
            counts, bins = np.histogram(normals[correct_length_crossings], bins=50)
            counts = counts / max(counts) * max(distribution.pdf(points))
            plt.hist(bins[:-1], bins, weights = counts, color="purple", label="Adjust traffic distribution")
            handles, _ = plt.gca().get_legend_handles_labels()
            handles.extend([Line2D([0], [0], linestyle = "dashed", label='Channel Center', color='black')])
            plt.title(f"{bridge_name} {traffic_direction}: {length_bin[0]} - {length_bin[1]}")
            plt.legend(loc="center right", bbox_to_anchor=[1.4, 0.5], handles = handles)
            plt.show()

    return [collision_probability_matrix, directed_annual_traffic]
