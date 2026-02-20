## Written by Diran Jimenez

# Usual imports
import numpy as np
import pandas as pd
import os

def generic_mask_filter(file_path, MMSI=False, BaseDateTime=False, LAT=False, LON=False, SOG=False, COG=False,
                        Heading=False, VesselName = False, IMO = False, CallSign = False, VesselType = False, 
                        Status = False, Length = False, Width = False, Draft = False, Cargo = False, TransceiverClass = False):
    """
    Parameters
    ----------
    file_path : string
        This string should point to a CSV File of AIS Broadcast Data you wish to filter.
    ALL OTHER PARAMETERS: List
        
        Each parameter corresponds to a column of AIS Broadcast Data
        
        There are two types of parameters, continuous and discrete.
        
        Inputs for continuous parameters should be a list of two variables,
            the first being the minimum value and second the maximum.
            
        Inputs for discrete parameters should be a list of all values desired. 
        
        The values in each list should match the type specified in the
            pd.read_csv call below. Specifically, MMSI values should be a string.
            
        The data assumes the "and" condition between all columns, and the 
            "or" condition between values in a column.
            
        EX:
            Generic_Mask_Filter(MMSI = ["123456789"], Status = [2]) will return 
            broadcasts that have MMSI = 12345 & Status = 2
        
        EX:
            Generic_Mask_Filter(MMSI = ["123456789", "101010101"]) will return broadcasts
            that have MMSI = "123456789" || MMSI = "101010101"
                Note that the "or" condition is denoted with "||" by pandas and numpy
                
        EX:
            Generic_Mask_Filter(LAT = [25, 26], LON = [-81, -80], MMSI = ["338399202"])
            returns broadcasts between latitude 25 and 26, longitude -81 and 80, 
            and MMSI = "338399202"
        
    Returns
    -------
    df : DataFrame
        A DataFrame that has data which satisfies all criterion passed as input
        conditions.

    """
    # locals() creates a dictionary containing all local variables
    conditions = locals()
    del conditions["file_path"]
        # The only variable not tied to a condition is the file_path

    df = pd.read_csv(file_path, sep=',', header=0, dtype={"MMSI":str, #Technically this should be an integer, but some files accidentally insert an alphanumeric character, causing a ValueError
                                                          "BaseDateTime": str, 
                                                          "LAT":np.float64,
                                                          "LON":np.float64,
                                                          "SOG":np.float64,
                                                          "COG":np.float64,
                                                          "Heading":"Int64",
                                                          "VesselName":str,
                                                          "IMO":str,
                                                          "CallSign":str,
                                                          "VesselType":"Int64",
                                                          "Status":"Int64",
                                                          "Length":"Int64",
                                                          "Width":"Int64",
                                                          "Draft":np.float64,
                                                          "Cargo":"Int64",
                                                          "TranscieverClass":str},
                                                          on_bad_lines="skip")
    
    
    continuous = ["BaseDateTime", "LAT", "LON", "SOG", "COG", "Heading"]
   
    for column in continuous:
        # Only apply condition if it exists
        if conditions[column]:
            # Check that a value is above the min, and below the max
            df = df.loc[ df[column].between(conditions[column][0], conditions[column][1])]
            # Remove this continuous variable from the conditions
            del conditions[column]
    
    
    # Now the conditions only considers columns with discrete values
    for column, requirements in conditions.items():
        # Only apply a condition if it exists
        if requirements:
            # Check that at least one of the values in the requirements is present in a row of the df
            df = df.loc[df[column].isin(requirements)]
    
    
    return df.sort_values(["BaseDateTime"])
    

def filter_by_intersection(df, data_folder, date, boundaries):
    """
    Parameters
    ----------
    df : Dataframe
        This is a dataframe that has been preparred for filtering, 
        i.e. only contains broadcasts that meet our ship qualifications
        
    data_folder : string
        Path to folder where data should be stored
        
    boundaries : Dictionary 
        Key:Value takes the form {Geographic_Region: Points Defining Geographic_Regions's Boundaries}
        A geographic region, in this case, is either a bridge or a port. This function is
        smart and can handle bridges or ports. They are nearly identical, 
        except each port is defined by five points (first and last should be 
        identical), while bridges defined by only two. 
     
    
    Returns
    -------
    None.
        ...Since the results are written to an external file instead of being
        stored in a variable. As discussed in the queues above, the data gets
        written by the file Running_Modules.py
        
        The actual data that gets written consists of pairs of AIS broadcasts
        corresponding to before and after a ship passes under a bridge / port.
        All columns are retained in case any becomes useful in the future. 
        
    """
                
    # A list of all the columns in the dataframe, to be used later
    columns = df.columns.values.tolist()

    # Get a list of each boat in the dataframe
    boats = df["MMSI"].unique()
    
    for bridge in boundaries:
        
        # Arrays can quickly be concatenated, great for combining chunks of data
        bridge_array = np.array([columns])
        
        # Data frames write to csv files quickly and robustly
        bridge_data = pd.DataFrame({})
        
        # Each bridge consists of 2 points
        bridge_1_x = boundaries[bridge][0][0]
        bridge_1_y = boundaries[bridge][0][1]
        
        bridge_2_x = boundaries[bridge][1][0]
        bridge_2_y = boundaries[bridge][1][1]
        

        for boat in boats:            
            # Filter by each boat separately to prevent paths from getting wonky
            # Additionally, organize chronologically to prevent paths from getting wonky
            boat_broadcasts = df.loc[df["MMSI"] == boat].sort_values(["BaseDateTime"]).to_numpy()
            
            # Keep in mind these are vectors of x coordinates and y coordinates
                # All calculations are performed as vectorized operations for speed
            
            boat_1_x = boat_broadcasts[:-1,3]
            boat_1_y = boat_broadcasts[:-1,2]
            
            boat_2_x = boat_broadcasts[1:,3]
            boat_2_y = boat_broadcasts[1:,2]
            
            # Be mindful of the indexing: if there are n boat points then there are n-1 line segments
            
            # a = segment boat_1 to boat_2
            # b = segment bridge_1 to bridge_2
            # c = segment boat_2 to bridge_1
            # d = segment boat_2 to bridge_2
            # e = segment bridge_2 to boat_1
            
            
            a_x = boat_2_x - boat_1_x
            a_y = boat_2_y - boat_1_y
            
            b_x = bridge_2_x - bridge_1_x
            b_y = bridge_2_y - bridge_1_y
            
            c_x = bridge_1_x - boat_2_x
            c_y = bridge_1_y - boat_2_y
            
            d_x = bridge_2_x - boat_2_x
            d_y = bridge_2_y - boat_2_y
            
            e_x = boat_1_x - bridge_2_x
            e_y = boat_1_y - bridge_2_y
            
            # The 2D cross product returns a scalar
            # Perform it on the boat segment to each bridge point, and bridge segment to each boat point
                # Hence, each cross product checks three points, since the end of one segment is the start of the second
            
            cross1 = a_x * c_y - a_y * c_x
            cross2 = a_x * d_y - a_y * d_x
            
            cross3 = b_x * e_y - b_y * e_x
            cross4 = b_y * d_x - b_x * d_y
            
                # cross4 should techincally be: b X (-d) {in english, b cross -d}
                # However, the negative has been distributed to d X b, as is done above
                # Hence, the swapping of x and y
            
            
            # If the scalar is positive, the points are oriented counterclockwise (denoted 1)
            # If the scalar is negative, the points are oriented clockwise (denoted -1)
            # If the scalar is 0, the points are collinear
            
            o1 = np.where( (cross1 > 0), 1, 0)
            O1 = np.where( (cross1 < 0), -1, o1)

            o2 = np.where( (cross2> 0), 1, 0)
            O2 = np.where( (cross2 < 0), -1, o2)

            o3 = np.where( (cross3> 0), 1, 0)
            O3 = np.where( (cross3 < 0), -1, o3)

            o4 = np.where( (cross4 > 0), 1, 0)
            O4 = np.where( (cross4 < 0), -1, o4)
            
            # When O1 and O2 have different signs, then the boat segment sees one bridge point on the left, and the other on the right
                # As in, the orientation of the points is different
                # Hence, it is intersected
                
            # However, the same must also be true from the bridge's perspective, otherwise the segments do not intersect
                # See this page for a diagram: https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/#

            o_mask = (O1 != O2) & (O3 != O4)
            
            # Special Case: The end of the boat segment lies on the bridge segment
                # True when:
                    # boat_2, bridge_1, and bridge_2 are collinear
                    # boat_2 lies between bridge_1 and bridge_2
            
            # To check if the boat lies between the bridge points, calculate the dot product of each bridge to the boat 
            dot = d_x * c_x + d_y * c_y
                # If the dot product is negative, the vectors point toward each other
                # NOTE: To save on calculations the sign of both vectors is flipped, so if the dot product is negative the vectors actually point away from each other
                    # This is equivalent since the dot product only cares about the *angle* between vectors, which doesn't change when the sign of both is flipped
                
        
            c_mask = (O4 == 0) & (dot <= 0)
                # (O4 == 0) checks that the points are collinear
                # (dot <= 0) checks that the boat lies between the bridge points
            
            """
            # Unfortunately, the data often has erroneous data points
                # EX: Boat A goes from -125 lon to -123 lon and back to -125 in the span of a few seconds (hundreds of miles)
                # EX: Boat B drops 4 hours of data and 'teleports' from 80 lat to 90 lat
                # EX: Boat C is parked at -100 lon, 30 lat, but spontaneously teleports 5 degrees in random directions
                
            # To avoid counting these bad trips, only keep segments that aren't impossibly long
            e_mask = (np.absolute(a_x) <= 1) & (np.absolute(a_y) <= 0.5)
                # These values were chosen after a visual inspection of erroneous data points
            """
            
            # Include segments that (intersect OR have collinear points) AND have normal jumps between data points 
            final_mask = (o_mask | c_mask) # & e_mask
            
            # Save each point of the intersecting line segments
            boat_data1 = boat_broadcasts[:-1][final_mask]
            boat_data2 = boat_broadcasts[1:][final_mask]
            
            # To make reconstructing line segments easier, points that form a line segment are stored next to each other
            boat_data = np.empty(((boat_data1.shape[0]*2), boat_data1.shape[1]), dtype=boat_data1.dtype)
            boat_data[0::2] = boat_data1
            boat_data[1::2] = boat_data2
            
            # Don't attempt to write data to the bridge array if there isn't any new data
            if boat_data.size != 0:
                bridge_array = np.concatenate((bridge_array, boat_data))
                
        # If there weren't any intersections with a bridge, don't attempt to write to its file        
        if len(bridge_array.shape) != 1:
            bridge_data = pd.DataFrame({columns[i]: bridge_array[1:,i] for i in range(len(columns))})
            bridge_data.to_csv(os.path.join(data_folder, bridge, f"{bridge}_{date}.csv"), index=False)
    return
