This section collects precise traffic data for each bridge which sees a sufficiently large number of ships (160) get close to it annually. 

The import and run modules script (as the name implies) imports the other scripts in this section and runs all of them.

The boundary constructor:
- Removes the bridges which were manually eliminated
- Turns the start and end coordinates of the remaining bridges into a dictionary of numpy arrays
- Returns the above dictionary

The process prefiltered script:
- Takes one day's data as input
- Removes barges and tug boats from the dataset (even if they report being over 150 meters long)
- Removes ships which travel impossibly fast
- Outputs the processed AIS data

The filter crossings script:
- Takes the boundaries and processed AIS data as input
- Then, for each bridge:
  - for each ship:
    - for each broadcast:
      - Constructs the line segment between the previous broadcast and this one
      - If this line segment intersects the bridge, records the current and previous broadcast
  - All recorded broadcasts are gathered into a CSV file for the current bridge and day of data and are saved
 
The aggregate daily data script aggregates daily CSV files into a single, complete record of data on a bridge-by-bridge basis
