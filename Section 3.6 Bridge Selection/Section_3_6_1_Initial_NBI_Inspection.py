## Written by Diran Jimenez

import pandas as pd
import os

# Ensure the current directory is the location of this file
curr_folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_folder)

nbi_database_file = "2025HwyBridgesDelimitedAllStates.csv" # Name same as the file download

avoid_interpreting = {"STATE_CODE_001": str,
                      "STRUCTURE_NUMBER_008": str,
                      "LAT_016": str,
                      "LONG_017":str}


nbi = pd.read_csv(nbi_database_file, dtype=avoid_interpreting).dropna(subset=["LAT_016","LONG_017"])

# Ignore leading zeros and erroneous spaces so string equality can be checked
nbi["STRUCTURE_NUMBER_008"] = nbi["STRUCTURE_NUMBER_008"].apply(lambda x: str(x).lstrip(" ").rstrip(" "))
nbi["STATE_CODE_001"] = nbi["STATE_CODE_001"].apply(lambda x: str(x).lstrip(" ").rstrip(" "))
nbi["UNIQUE_IDENTIFIER"] = nbi["STATE_CODE_001"] + " " + nbi["STRUCTURE_NUMBER_008"]

# Source for item descriptions: www.fhwa.dot.gov/bridge/mtguide.pdf

# Item 06A describes any landmarks that the bridge crosses over
types_of_water = ["STREAM",
                  " RV",
                  " RIV",
                  " RIVR",
                  "RIVER",
                  "CHANNEL",
                  "SHIP",
                  "CANAL",
                  "STRAIT",
                  "WATER",
                  "BAY",
                  "HARBOR",
                  "PORT",
                  ]
    # NOTES:
    # creeks are ignored due to their small size
    # abbreviations include a space so a word like 'Harvard' (containing "rv") doesn't register as a river
    
over_water = nbi["FEATURES_DESC_006A"].apply(lambda x: any(water in x.upper() for water in types_of_water))

# Item 38, Navigation Permit, is "N" for not applicable when a bridge is not over water
navigable = nbi["NAVIGATION_038"].apply(lambda x: str(x).lstrip(" ").rstrip(" ").upper()) != "N"

# Item 39, Min Vertical Clearance, describes the clearance above the water for a bridge
min_height_meters = 0   # Some large bridges, such as the Dames Point Bridge (FL), report a height above water of 0.3 meters (1 foot) 
tall_enough = nbi["NAV_VERT_CLR_MT_039"] > min_height_meters

# Item 42, Type of Service Under, indicates what type of service is "under" the bridge
water_services = [i for i in range(5,10)] # Source: www.fhwa.dot.gov/bridge/mtguide.pdf
water_under = nbi["SERVICE_UND_042B"].astype("Int64").isin(water_services)

# Item 60, Substructure Condition, has an "N" if the bridge has no substructures, e.g. piers
may_have_piers = nbi["SUBSTRUCTURE_COND_060"].apply(lambda x: str(x).lstrip(" ").rstrip(" ").upper()) != "N"


valid_bridges = nbi[(over_water | navigable | water_under) & tall_enough & may_have_piers]


print(f"Number of Valid Bridges: {valid_bridges.shape[0]}")
