## Written by Diran Jimenez

# Standard Imports
import pandas as pd
import numpy as np
   

'''
Our team has manually curated a list of bridges across the US. 
The purpose of this script is to turn an excel with their coordinates 
into a dictionary that can be easily used. 
'''

def boundary_construction(boundary_file):
    """
    Parameters
    ----------
    boundary_file : str
        Name of boundary file, which should be an excel spreadsheet
        containing a list of bridges (all with unique names) and 
        the coordinates of their start and end, using the following
        column names:
            STRUCTURE_NAME | START_X | START_Y | END_X | END_Y
            
    Returns
    -------
    bridge_lines : dictionary
        bridge_lines is a dictionary where each key is a bridge, and each value
        is a pair of points, aka a 2x2 Matrix, containing the start and end of 
        the bridge.
    """

    # Read in the relevant part of the excel file
    bridge_data = pd.read_excel(boundary_file, header=0, # index_col = 0, 
                                usecols=["STRUCTURE_NAME", "START_X", "START_Y","END_X", "END_Y", "Reason for Exclusion"], 
                                converters={"START_X":float, "START_Y":float, "END_X": float, "END_Y":float})
    
    # Some bridges are ignored for various reasons, thus there should not be a reason for exclusion
    good_bridges = bridge_data[bridge_data["Reason for Exclusion"].isna()].drop("Reason for Exclusion", axis=1).set_index("STRUCTURE_NAME")

    # Turn the dataframe into an appropriate dictionary
    dict_bridges = good_bridges.loc[:, ["START_X", "START_Y","END_X", "END_Y"]].transpose().to_dict('list')
    
    # Make the values more usable by turning them into appropriately shaped arrays
    bridge_lines = {bridge: np.array(dict_bridges[bridge]).reshape(2,2) for bridge in dict_bridges}
        # This dictionary now has a start point and end point for each bridge
        
    return bridge_lines
    



