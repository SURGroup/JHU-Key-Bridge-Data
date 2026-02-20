## Written by Diran Jimenez

import pandas as pd
import numpy as np
import os
import time
import multiprocessing as mlt

# Ensure the current directory is the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

# Full path to folder with pre-filtered AIS data
pre_filter_folder_2015 = ""
pre_filter_folder_2018 = ""

files_2015 = [(pre_filter_folder_2015,file) for root, dirs, files in os.walk(pre_filter_folder_2015) for file in files]
files_2018 = [(pre_filter_folder_2018,file) for root, dirs, files in os.walk(pre_filter_folder_2018) for file in files]

all_files = files_2015 + files_2018

# Folder to store rough, vicinity-based traffic estimates
estimate_folder_name = ""
estimate_folder = os.path.join(curr_folder, estimate_folder_name)

# Ensure the estimate folder exists
if not os.path.exists(estimate_folder):
    os.makedirs(estimate_folder)
    
# Subset of the NBI database
valid_bridge_file = "Bridges_that_pass_NBI_filters.csv"
valid_bridges = pd.read_csv(valid_bridge_file)

def triangular_projection(lat1, lon1, lat2, lon2):
    # Find the distance between two points using a triangular projection
    R = 6371e3 # Radius of the Earth, meters
    meters_to_nautical_miles = 0.00054
    x = (lon2-lon1) * np.pi/180 * np.cos( ((lat1+lat2)/2) * np.pi/180)
    y = (lat2-lat1) * np.pi/180
    d = np.sqrt(x*x + y*y) * R * meters_to_nautical_miles
    return d # nautical miles

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

def estimate_nearby_traffic(input_folder_and_file, bridge_database,
                            estimates_folder):
    file_folder = input_folder_and_file[0]
    file_name = input_folder_and_file[1]
    date = file_name[4:14]

    meters_to_nautical_miles = 0.00054
    
    start = time.time()

    results = []
    
    # Prepare the AIS data
    df = pd.read_csv(os.path.join(file_folder, file_name),
                     usecols=["MMSI", "LAT", "LON", "SOG", "VesselType"])

    # Cargos and Tankers have these VesselTypes
    correct_types = [70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 1004, 1016, 
                     80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 1017, 1024]
 
    cargo_tanker = df[ (df["VesselType"].astype("Int64").isin(correct_types))
                     & (df["SOG"] >= 3)] # Ships can't cross a bridge if they're not moving
                                         # Too many points massively increases run time
    
    mmsi, ship_x_coords, ship_y_coords = (cargo_tanker[col].values for col in ["MMSI", "LON", "LAT"])

    # Prepare the bridge database
    bridge_names, bridge_lengths = (bridge_database[col].values for col in ["UNIQUE_IDENTIFIER", "STRUCTURE_LEN_MT_049"])
    bridge_x_coords = bridge_database["LONG_017"].astype(str).apply(convert_coords, args=(True,)).values
    bridge_y_coords = bridge_database["LAT_016"].astype(str).apply(convert_coords, args=(False,)).values
    
    for i in range(len(bridge_names)):
        traffic_distance = triangular_projection(bridge_x_coords[i], 
                                                 bridge_y_coords[i],
                                                 ship_x_coords,
                                                 ship_y_coords)
        
        # If a ship gets within 1 natuical mile of a bridge, it could collide with it during aberrancy
        nearby_traffic = traffic_distance <= 1.5 * max(1, bridge_lengths[i] * meters_to_nautical_miles)
            # Extremely long bridges w/ their NBI point at the start of the bridge can be farther than 1 nautical mile from the waterway
            # 50% safety factor, looking for conservative estimates of traffic
        num_nearby_ships = len(set(mmsi[nearby_traffic]))
        results.append(num_nearby_ships)
    
    pd.DataFrame({"UNIQUE_IDENTIFIER": bridge_names, "NUM_NEARBY_SHIPS": results}).to_csv(os.path.join(estimate_folder, f"{date}_Traffic_Estimate.csv"), index=False)
    
    print(f"{date} - {(time.time() - start)/60:.4f} min",flush=True)                                                             
    return 

if __name__ == "__main__":
    print("Script Began", flush=True)
    start = time.time()
    
    # Script was ran using 48 cores. Adjust based on your hardware
    num_cores = 48
    
    with mlt.Pool(num_cores) as pool:
        pool.starmap(estimate_nearby_traffic, [(input_file_and_folder, valid_bridges, estimate_folder)
                                               for input_file_and_folder in all_files])
        
    end = time.time()
    print(f"Script Finished in {(end-start)/60:.4f} minutes")


    


