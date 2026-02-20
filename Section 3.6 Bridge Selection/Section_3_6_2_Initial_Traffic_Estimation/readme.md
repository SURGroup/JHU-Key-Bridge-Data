This subsection creates a vicinity-based traffic estimation for each bridge that meets all the filters we placed on bridges in the NBI. 

BEFORE THIS SECTION CAN BE RAN, THE AIS DATA MUST BE DOWNLOADED AND PREFILTERED

The gather estimates scirpt performs the vicinity based traffic estimation, recording the number of large ships that get close to each bridge for a single day of data. This is done for all days.
The aggregate estimates (as the name implies) aggregates all these daily-recordings into a single, complete recording. This is the Vicinity_Traffic_Estimation.csv file.
Finally, the analyze estimates script selects all bridges which see at least 160 ships, annually, on average, and creates a subset of the NBI containing just these bridges. 
This spreadsheet comes out "raw" and is manually adjusted, see readme in parent directory. 
