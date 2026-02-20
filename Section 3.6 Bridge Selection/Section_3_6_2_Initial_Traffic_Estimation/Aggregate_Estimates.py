## Written by Diran Jimenez

import pandas as pd
import numpy as np
import os

# Ensure the current directory is the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

print("Started")

estimate_folder = "Traffic_Estimates"

estimates = [file for root, dirs, files in os.walk(estimate_folder)
             for file in files]

from bridge_selector import valid_bridges

bridge_estimates = {b: 0 for b in valid_bridges["UNIQUE_IDENTIFIER"].values}

for file in estimates:
    data = pd.read_csv(os.path.join(estimate_folder, file), index_col = "UNIQUE_IDENTIFIER").to_dict("index")
    
    for b in bridge_estimates.keys():
        bridge_estimates[b] += data[b]["NUM_NEARBY_SHIPS"]
        
pd.DataFrame({"UNIQUE_IDENTIFIER": bridge_estimates.keys(),
              "NUM_NEARBY_SHIPS": bridge_estimates.values()}).to_csv("Vicinity_Traffic_Estimation.csv", 
                                                                     index=False)

print("Done")
    

