## Writen by Diran Jimenez


### Python Standard Library ###

# Package for parallel processing
import multiprocessing as mlt 

# Package for organizing files
import os

# Misc
import time

'''
To avoid any discrepancies between where this file is located, and the current
working directory, we set the cwd to this file's location. 
'''

curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

'''
To import the rest of the modules, please ensure the following file structure:
    
{Project Folder} (Name does not matter)
 ├─ Boundary_Construction.py
 ├─ Filter_Crossings.py
 ├─ Import_and_Run_Modules.py
 ├─ Process_PreFiltered.py
 └─ {Boundary_File}.xlsx
  
  
'''

### Special Modules created for this project ###

from process_pre_filtered import process
from boundary_construction import boundary_construction

'''
If you wish to alter any of the imported functions, please create a new version
of the relevant module and import that instead. Please be mindful of the
function inputs, and ensure it produces the expected outputs.  
'''

#########################
### Preparing Folders ###
#########################


# Ensure this script is run from the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

# The name of the folder where the results will be stored
data_folder_name = ""
data_folder = os.path.join(curr_folder, data_folder_name)

# Ensure the folder exists to avoid errors
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Name of the excel file which contains the bridge boundaries
boundary_file = ""

boundaries = boundary_construction(boundary_file)

# Create a separate folder for each bridge
    # Each day's data will be stored for each bridge
for bridge in boundaries.keys():
    if not os.path.exists(os.path.join(data_folder, bridge)):
        os.makedirs(os.path.join(data_folder, bridge))
        

# Provide the full path to the folder with pre-filtered data
pre_filter_folder = ""


files = sorted([file for root, dirs, files in os.walk(pre_filter_folder)
                for file in files])
    # This is a bastard of a list comprehension I wrote for fun
    # It collects all files that end with .csv, i.e. all CSV files from the prefiltered folder
    

# One node on Rockfish has 48 cores
num_cores = 48
    # If running locally or on different hardware, adjust accordingly
    
min_ship_length = 150 # meters

if __name__ == "__main__":

    print("Script Began", flush=True)

    start = time.time()

    with mlt.Pool(num_cores) as pool:
            # starmap's first argument is a function to be applied
            # The second argument is a list of tuples of all arguments to be passed
                # Here, download is run on each batch of files, connected to the managed queues
        pool.starmap(process, [(file, min_ship_length, boundaries, pre_filter_folder, data_folder)
                               for file in files])
                # Note: Starmap implicitly joins all processes
                    # As in, the rest of the code in the main file will wait until all processes are complete

    end = time.time()
    print("Script Complete")
    print(f"Run time for script: {(end-start)/60:.4f} minutes")
