This section focuses on culling the majority of the bridges from the NBI using a series of simple steps. 

The initial bridge inspection takes the entire NBI and applies a series of filters to them, eliminating bridges which cannot physically see large ship traffic.
That list of bridges is sent to the Initial Traffic Estimation folder. 
The scripts in that folder create a rough estimate of traffic around each bridge and returns a list of bridges which could see enough traffic to be at-risk.
That list is output as an excel file back to the current directory. 

This excel file, "Master_Bridge_Information.xlsx", has undergone manual processing in two ways:
1. Additional columns were added (see the data dictionary for more information). 
1. The arrangement of various columns (order + color) was adjusted for hand-collection.
2. The start and end coordinates of each bridge were collected using satellite imagery (i.e. google earth)

Some bridges were eliminated from the analysis during the inspection. The reason is listed in the "Reason for Exclusion" column, such as:
- Being too small to see large ship traffic (e.g. too short, too narrow)
- Being a duplicate bridge
  - If a bridge crosses state boundaries, both states have an entry for the same structure
  - If a bridge has two highway lanes, occasionally each lane gets its own entry in the NBI despite sitting on the same bridge
- Not actually being a bridge (many docks are included in the NBI)
- Not having a substructure under the deck which could be struck by a bridge
