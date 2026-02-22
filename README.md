# Key Bridge Analysis Project Code and Data
This repository contains the code and data used in the 2026 paper "THERE’S NO SUCH THING AS FREE SHIPPING: THE SIGNIFICANT
RISK LARGE VESSELS POSE TO U.S. BRIDGES." 

## Contents Description
Each folder contains the code / data used in the corresponding section of the paper. For more details, please read the paper. 
There is a discrepancy between the section numbering, and the order in which code must be run to replicate results. 
The paper sections were ordered based on what made sense narratively. 

To replicate the results in the paper, please run each section in the following order:
1. Section 3.1 Data Set - Download and Prefilter
2. Section 3.4 Traffic Data Collection
3. Section 3.5 Allision Probability Calculation
4. Section 3.6 Bridge Selection

A brief summary of each section is provided below, and a more in-depth summary provided within the corresponding folder. 

### Section 3.1 Data Set - Download and Prefilter
- Downloads a local copy of the AIS data base from Marine Cadastre.
- Applies a few filters to trim down unnecessary data points.

### Section 3.6 Bridge Selection
- Begins with the NBI, a list of all bridges in the United States.
- Applies some simple filters to rule out bridges physically incapable of seeing large ship traffic.
- Calculates a rough approximation of traffic under the remaining bridges.
- Discards all bridges which cannot see enough traffic to be at-risk.
  
### Section 3.4 Traffic Data Collection
- Takes the coordinates (manually collected) for each bridge left after section 3.6 and calculates a much more precise level of traffic for each.

### Section 3.5 Allision Probability Calculation
- Using the precise bridge traffic, performs AASHTO's probability of allision methodology using highly conservative assumptions.
- Bridges with a probability of allision below 1 in 1000, even under these conservative assumptions, are discarded.
- The piers and protections for the remaining bridges were collected manually.
- A precise allision probability estimation was made using the pier and protection data



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
