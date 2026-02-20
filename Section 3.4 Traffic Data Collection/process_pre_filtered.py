## Written by Diran Jimenez

# Standard Python Library
import time
import os

# Pandas and Numpy
import pandas as pd
import numpy as np


# Make sure the file is run from this file's location
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)
    
# Custom Module for this project:
from filter_crossings import filter_by_intersection

def triangular_projection(lat1, lon1, lat2, lon2):
    # Find the distance between two points using a triangular projection
    R = 6371e3 # Radius of the Earth, meters
    meters_to_nautical_miles = 0.00054
    x = (lon2-lon1) * np.pi/180 * np.cos( ((lat1+lat2)/2) * np.pi/180)
    y = (lat2-lat1) * np.pi/180
    d = np.sqrt(x*x + y*y) * R * meters_to_nautical_miles
    return d # nautical miles

def process(file, min_ship_length, boundaries, pre_filter_folder, data_folder):
    """
    Parameters
    ----------
    file : string
        Name of the file to be filtered
        
    pre_filter_folder : string
        Path to folder with pre-filtered files
        
    data_folder : string
        Path to folder to store results
        
    Returns
    -------
    None.
        Data is written to external csv file, rather than directly being returned
    """
    
    # Everything is jammed into a try-except to prevent a single error from 
    # crashing a potential multi-day job
    try:
        file_start = time.time()
    
        # Define this variable for error handling
        file_name = file
        date = file_name[4:14]
        
        # Improve read speed by specifying data types
        data_types = {"MMSI":str, #Technically this should be an integer, but some files accidentally insert an alphanumeric character, causing a ValueError
                      "LAT":np.float64,
                      "LON":np.float64,
                      "SOG":np.float64,
                      "COG":np.float32,
                      "Heading":"Int64",
                      "VesselName":str,
                      "IMO":str,
                      "CallSign":str,
                      "VesselType":"Int64",
                      "Status":"Int64",
                      "Length":"Int64",
                      "Width":"Int64",
                      "Draft":np.float32,
                      "Cargo":"Int64",
                      "TranscieverClass":str}
        
        # Data from 2015-2017 uses floats for length and width
        if date[:4] in ["2015", "2016", "2017"]:
            data_types["Length"] = np.float32 
            data_types["Width"] = np.float32
        
        print(f"Started filtering {file_name}", flush=True) 
        
        # Read the file into a dataframe
        df = pd.read_csv(os.path.join(pre_filter_folder,file), sep=',', header=0, 
                         dtype= data_types, on_bad_lines="skip").sort_values(by=["MMSI","BaseDateTime"])
        
        ## Perform some additional data-cleaning
        
        # We only consider ships above a minimum length
        over_min_length = df["Length"] >= min_ship_length
        
        # We ignore barges and tugs because they report lengths greater than their actual size
        barge_ids = [1003, 1014, 1015, 57] # 57 based on data observation
        tug_ids = [21, 22, 30, 31, 32, 52, 1023, 1025] # 30 based on data observation
            # Source: https://coast.noaa.gov/data/marinecadastre/ais/VesselTypeCodes2018.pdf
        
        barge_or_tug = df['VesselType'].astype("Int64").isin(barge_ids + tug_ids)
        
        # Finally, ships sometimes 'teleport', i.e. have a faulty broadcast which is hundreds of miles from its actual position
        
        distances = triangular_projection(df["LAT"].values[:-1:2], df["LON"].values[:-1:2], 
                                          df["LAT"].values[1::2], df["LON"].values[1::2])
            # units = nautical miles
        
        # Calculate the time between each pair of points
        t = df["BaseDateTime"].astype('datetime64[s]').values
        times = (t[1::2] - t[:-1:2]).astype(np.int32) / 3600 
            # units = hours
        times = np.where(times == 0, 0.0001, times) # Avoid divide by 0 errors
        
        # Calculate the actual velocity of each pair of points
        v = distances / times
        
        # Label each pair of points with the same velocity
        velocities = np.zeros(2 * v.shape[0])
        velocities[:-1:2] = v
        velocities[1::2] = v
            # units = knots
        
        # Only keep points that aren't too fast or too slow
        travels_at_appropraite_speeds = (velocities <= 40) # & (velocities > 0.5)
            # One of the fastest cargo ships is the Maersk Boston, with top speed ~37 knots
            # Thus, it should be physically impossible for any ship to pass under a bridge faster than 40 knots
            
        # Filter the appropriate dataframe based on bridge intersections
        # filter_by_intersection(df[over_min_length & ~barge_or_tug],
        #                        data_folder, date, boundaries)
        
        filter_by_intersection(df[over_min_length & ~barge_or_tug & travels_at_appropraite_speeds],
                               data_folder, date, boundaries)

        file_end = time.time()
        print(f"Finished filtering {file_name}\n\tRun time was {(file_end-file_start)/60:.4f} minutes", flush=True)   
    except Exception as e:
        # If there's any error, rockfish will completely halt
        # Instead, ignore the error for later so the entire job doesn't get wasted
        print(f"File {file_name} failed, need to refilter!\n  Error: {e}", flush=True)

    return 

