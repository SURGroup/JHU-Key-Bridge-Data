## Written by Diran Jimenez

# Usual imports
import os
import pandas as pd
import numpy as np

# Ensure the script is run from the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

# Name of the folder where daily data is stored, organized by bridge
data_folder_name = ""
data_folder = os.path.join(curr_folder, data_folder_name)

# Name of the folder where the aggregated data should be placed
aggregate_folder_name = ""
aggregate_folder = os.path.join(curr_folder, aggregate_folder_name)
    # This will be within the data folder

if not os.path.exists(aggregate_folder):
    os.makedirs(aggregate_folder)
# Get the folder of each bridge in the data folder
bridge_folders = [f.path for f in os.scandir(data_folder) if f.is_dir()] 

for bridge in bridge_folders:
    # The base DataFrame that will hold all the data
    bridge_df = pd.DataFrame(columns =  ['MMSI', 'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG', 'Heading',
                                         'VesselName', 'IMO', 'CallSign', 'VesselType', 'Status', 'Length',
                                         'Width', 'Draft', 'Cargo', 'TransceiverClass'])
    
    bridge_name = bridge[len(data_folder)+1:]
    
    print(f"Started {bridge_name}")
    
    bridge_files = sorted([file for root, dirs, files in os.walk(bridge) for file in files if file.endswith('.csv')])
    
    for f in bridge_files:
    
        file_data = pd.read_csv(os.path.join(bridge, f))
        # Sometimes the bridge didn't have any crossings on a day
        if file_data.empty:
            continue
        bridge_df = pd.concat([bridge_df, file_data])
    
    bridge_df.to_csv(os.path.join(aggregate_folder, f"{bridge_name} Data.csv"), index=False)
    
    print(f"Finished {bridge_name}")

