This section focusses on calculating precise probabilities of allision.

AASHTO provides a formula for probability of allision, see Section 3.5 of the paper for a thorough explanation. 

For a given bridge, the formula requires:
- The probability of aberrancy of a given ship (per AASHTO, $0.6 \times 10^(-4)$ for all ships in the study).
- The number of ships that pass under the bridge annually
- The distribution of _where_ these ships pass under the bridge
- The location and width of each of the bridge's piers
- The location and width of any pier protections for the bridge

The last two items, piers and protections, required manual collection. For 357 bridges (the amount left before this section, see section 3.6.3 and 3.6.4 of paper for more details) this is excessively resource intensive.
To save on manual labor, the probability of allision was calculated using two highly conservative assumptions: each bridge had no pier protection, and anywhere that ships did not pass under the bridge was treated as a vulnerable surface to allision (see Figure 6 of paper).
The [inferred pier area script](../Section_3_6_3_Allision_Estimation_using_inferred_pier_area.py) calculates probability of allision using these conservative estimates. 
Bridges with a probability of allision below 1 in 1000 after this step were discarded, since they cannot be at risk of allision

The remaining bridges (105) had their piers and protections collected, listed in the "All_Piers_and_Protections" excel file. 
Each bridge has multiple rows, one for each pier. The LAT, LON, and length (projected on the bridge's perpendicular) are recorded. 
The two length values, MIN and MAX, correspond to the smallest and largest possible footprints which could be struck by a bridge. See the second paragraph of section 2.2 in the paper for more details. 

Some rows for piers are duplicated, to account for a pier having multiple dolphins as protection. The LAT, LON, and width (projected onto the bridge's perpendicular) are recorded. 
All other columns' purpose and information is identical to that of the [master bridge information](../Section%203.4%20Traffic%20Data%20Collection/Master_Bridge_Information.xlsx) spreadsheet in section 3.4. 

After collection all piers and protections, the [recorded pier area script](../Section_3_6_4_Precise_allision_calculation_using_recorded_piers.py) calculates a more accurate probability of allision for all 105 bridges with pier and protection data.
The probabilities using the MIN pier lengths correspond to the MIN allision probability estimates, and likewise for the MAX lengths. 

Each bridge has two estimate files in each estimate folder, one for each direction of traffic. Within the estimate file is the probability of allision for each pier in each year. 
