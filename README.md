# Key Bridge Analysis Project Data
This repository contains data, analysis, and visualizations related to bridge traffic under major U.S. bridges. 


## Contents Description

### Bridge Ranking by Ship Traffic
- Contains folders with traffic data categorized by ship size.

### Distribution of Ship Size for Individual Bridges
- PDF files showing the distribution of ship sizes passing under specific bridges.

<ins>Further details can be found in the README file within that folder.</ins>


### Probability of Collision Estimation
#### Description
Contains the codes, input files, and result files detailing the estimated annual probability of collision of large ships (>150 m) with 23 of the most trafficked bridges in the US. An included pdf file titled "Documentation.pdf" details the contents of each file as well as the various assumptions and decisions involved in the calculation. The estimated collision probabilities and associated return periods are provided in the folder titled "Results".


### Processed Ship Traffic Data
#### Description
The processed dataset comprises **215 rows** and **149 columns**, representing the **215 bridges** included in this stage of the analysis. These bridges are primarily located along coastal areas, reflecting the focus on regions with significant maritime activity.

#### Data Composition
1. **NBI Data**:
   - The first **123 columns** are sourced from the **National Bridge Inventory (NBI)** dataset.

2. **Additional Columns**:
   - The remaining columns provide:
     - Standardized bridge names
     - Precise location coordinates (start and end points)
     - Traffic data derived from the **Automatic Identification System (AIS)** by different ship sizes.
    

### Raw Ship Traffic Data
- CSV files containing ship traffic data under individual bridges; these files were used to create the plots in "Bridge Ranking by Ship Traffic" and "Distribution of Ship Size for Individual Bridges".

#### Cumulative Jan 2018 - Mar 2024 Ship Traffic
- CSV files containing the total number of trips (January 2018 - March 2024) and the average number of trips per day for all bridges studied. These files were used to create the plots in "Bridge Ranking by Ship Traffic".

#### Traffic Distribution by Ship Size and Year - Jan 2018 - Mar 2024
- CSV files containing the number of trips for each year (Jan 2018 - Mar 2024) for different categories of ship lengths for all bridges studied. These files were used to create the plots in "Distribution of Ship Size for Individual Bridges".


## Usage

1. Navigate to the desired folder based on the analysis you're interested in.
2. For rankings, refer to the PDF files in the `Rankings` folder.
3. For raw data, check the CSV files in the respective folders.
4. To view plots and histograms, go to the `New Histograms and Plots for all Bridges` folder.

## License

This work is licensed under CC BY-SA 4.0 

## Contact

Michael Shields - michael.shields@jhu.edu

## Acknowledgments

- National Science Foundation - Award Number 2428805
- NOAA Office for Coastal Management, Bureau of Ocean Energy Management, U.S. Coast Guard: https://hub.marinecadastre.gov/pages/vesseltraffic
