## Written by Diran Jimenez

"""
This script downloads and prefilters AIS files from a list of URL's
"""

##########################
### Importing Packages ###
##########################

# Packages for Handling Data
import pandas as pd
import numpy as np

# Packages for interfacing with internet
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from http.client import IncompleteRead

# Packages for parallel processing
import multiprocessing as mlt 

# Miscellaneous
import time
import os


# Ensure that this script is run from the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

# Please check that URL_Constructor is in the scope of this file
from url_constructor import url_list_no_transceivers, url_list_with_transceivers

# Name of the folder where produced data should be stored
data_folder_name = ""
data_folder = os.path.join(curr_folder, data_folder_name)

# Ensure the data folder exists
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

def pre_filter(file_path, file_name, transceiver, data_folder, min_boat_length=150):
    """
    Parameters
    ----------
    file_path : str 
        Zipfiles from the internet will be opened, with its path inputed here
    
    file_name : str
        The name of the file, without the path information
        
    transceiver : bool
        True if the data is has a column indicating the Transceiver Class
        False otherwise 
    
    data_folder: str
        Path to folder where data should be stored
        
    min_boat_length : int
        the smallest length for a ship to be considered 
        units = meters
        default: 150 meters, see Paper section 3.2 Vessel Selection
        
    Returns
    -------
    None. 
        Data is written to an external file 
        Data is a CSV file of AIS broadcasts from ships that meet our ship qualifications
    """
    
    # Each file is prepared as a data frame
    # To improve memory efficiency and read speeds, the datatype of each column is specified
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
    
    # If the transceiver class is listed, we want A class (class B tends to give faulty information)
    if transceiver:
        raw_data = pd.read_csv(file_path, sep=',', header=0, 
                               dtype = data_types, 
                               on_bad_lines="skip")
        try:
            raw_data = raw_data[raw_data["TransceiverClass"] == "A"]
        except KeyError:
            raw_data = raw_data[raw_data["TranscieverClass"] == "A"]
            # For some stupid reason there's occasionally a typo here
                # TranscIEver instead of TranscEIver
            # All qualifications are the same
    else:
        # Data from 2015-2017 records the following columns using floats
        data_types["Length"] = np.float32 
        data_types["Width"] = np.float32 
        
        raw_data = pd.read_csv(file_path, sep=',', header=0, 
                               dtype = data_types, 
                               on_bad_lines="skip")
        
    # Keep broadcasts based on our ship qualifications:
    filtered = raw_data.loc[
         ( (70 <= raw_data["VesselType"]) & (raw_data["VesselType"] < 90) ) 
         | (raw_data["VesselType"] == (1003 | 1004 | 1016 | 1017 | 1024 | 61) ) 
         | (raw_data["Length"] >= min_boat_length)
         ]
    # Ships must be longer than chosen minimum length (units are meters)
    # Or ships must be of class cargo, tanker, or cruise ship
        # For data analysis, we are interested in all tanker and cargo ships
        # For final results, we only include them if they are at least 150 meters long
    # Vessel Type codes are based on the following: https://coast.noaa.gov/data/marinecadastre/ais/VesselTypeCodes2018.pdf
        
    # Write the data to a CSV file
    write_path = os.path.join(data_folder, file_name + "_PreFiltered.csv")
    filtered.to_csv(write_path, index=False)
    print(f"Finished {file_name}", flush=True)
    return



def download_and_filter(url, transceiver, data_folder):
    """
    Parameters
    ----------
    url : string
        string representing link to AIS data from Marine Cadastre.
    
    transceiver : bool
        True if the data is has a column indicating the Transceiver Class
        False otherwise

    data_folder : string
        Path to folder where data should be stored
        
    Returns
    -------
    None.
    """
    # Download the file from the link so it can be interacted with
    try:
        download = urlopen(url)
    
    # Unzip the file
        data_zip_file = ZipFile(BytesIO(download.read()))
    
    #The actual file name is derived from the url, and looks like AIS_Year_DateNum
        file_name = url[55:-4] + '.csv'
        #The first 50 characters are the base url, the last 4 are .zip
    
    #Apply the filter function to the file
        pre_filter(data_zip_file.open(file_name), file_name[:-4], transceiver, data_folder)

    except IncompleteRead:
        time.sleep(10) # Wait 10 seconds before retrying
        download_and_filter(url, transceiver)
        
    except Exception as e:
        # If there's any error, rockfish will completely halt
        # Instead, ignore the error for later so the entire job doesn't get wasted
        print(f"File {file_name} failed, need to refilter! \n Error: {e}", flush=True)
    return 



if __name__ == "__main__":
    print("Script Began")
    
    # Script was ran using 48 cores. Adjust based on your hardware
    num_cores = 48
    
    # For data from 2018 onwards, the transceiver class is listed
    transceiver = True
    
    if transceiver:
        links = url_list_with_transceivers
    else:
        links = url_list_no_transceivers
    
    
    # Create a pool with max processes = num_cores
    with mlt.Pool(num_cores) as pool:
        pool.starmap(download_and_filter, [(link, transceiver, data_folder) for link in links])
    
