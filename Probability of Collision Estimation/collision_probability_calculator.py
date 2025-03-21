import os

import numpy as np
import pandas as pd
import scipy.stats as stats


# Function to compute the protection factor as detailed in Section 3.14.5.5 in the AASHTO design code
def protection_factor(pier_number, num_protections, protection_parameters, ship_width):
    angle_distribution = stats.norm(loc=0, scale=((30*np.pi)/180))      # Distribution on potential approach angles.
                                                                        # A standard deviation of 30 degrees has been assumed as per the design code
    protection_fraction = 0
    for i in range(num_protections):                                    # Looping over the number of dolphins
        if protection_parameters[i, 1] == pier_number:                  # Ensuring that the dolphin's protection is applied to the correct pier
            L = protection_parameters[i, 5]                             # Distance of dolphin from pier
            D_E = protection_parameters[i, 6] + (0.75*ship_width)       # Effective dolphin diameter
            theta = np.arcsin(D_E/(2*L))                                # Protection angle provided by dolphin
            protection_fraction += (2*(angle_distribution.cdf(theta) -  # Protection provided as fraction
                                       angle_distribution.cdf(0)) *
                                    protection_parameters[i, 2])
    res = 1 - protection_fraction                                       # Protection factor
    return res


# Function to compute the geometric probability as detailed in Section 3.14.5.3 in the AASHTO design code
def geometric_probability(normalized_pier_location, waterway_length, pier_width, ship_length, travel_centerline,
                          ship_width, bayonne_flag):

    ship_travel_distribution = stats.norm(loc=waterway_length*travel_centerline, scale=ship_length)             # Normal distribution assigned to possible ship travel paths
    impact_zone_width = pier_width + ship_width  # Width of ship/bridge impact zone
    if bayonne_flag == 1:
        # Procedure for the Bayonne bridge. Since the piers are on the edge of the bank and the arch is low and extends
        # over the waterway, the potential collision region only extends out on one side of the pier, which changes
        # depending on which pier is considered.
        if normalized_pier_location < 0.5:
            res = (ship_travel_distribution.cdf((waterway_length * normalized_pier_location) + (0.5 * impact_zone_width)) -
                   ship_travel_distribution.cdf(waterway_length * normalized_pier_location))
            # Geometric probability of collision for pier on one bank of the waterway
        else:
            res = (ship_travel_distribution.cdf(waterway_length * normalized_pier_location) -
                   ship_travel_distribution.cdf((waterway_length * normalized_pier_location) - (0.5 * impact_zone_width)))
            # Geometric probability of collision for pier on the other bank of the waterway
    else:
        res = (ship_travel_distribution.cdf((waterway_length * normalized_pier_location) + (0.5 * impact_zone_width)) -  # Geometric probability of collision
               ship_travel_distribution.cdf((waterway_length * normalized_pier_location) - (0.5 * impact_zone_width)))

    return res


# Function to compute the location of the pier along the line joining the two ends of the bridge (from bank to bank)
def normalized_pier_center_location(bridge_start, bridge_end, pier_center):

    bridge_diff = bridge_end - bridge_start                                             # difference in lat/long coordinates of the bridge

    # The following lines encode the location of the foot of the perpendicular dropped from the center of the pier onto
    # the line joining the ends of the bridge. This procedure allows for handling curvatures in the bridge.
    numerator_t1 = (pier_center[1] - bridge_start[1])*bridge_diff[0]*bridge_diff[1]
    numerator_t2 = pier_center[0]*(bridge_diff[0]**2)
    numerator_t3 = bridge_start[0]*(bridge_diff[1]**2)
    numerator = numerator_t1+numerator_t2+numerator_t3
    denominator = (bridge_diff[0]**2) + (bridge_diff[1]**2)

    # The x and y coordinate of the foot of the perpendicular from the pier
    projection_x = numerator/denominator
    projection_y = pier_center[1] - ((projection_x - pier_center[0])*(bridge_diff[0]/bridge_diff[1]))

    # The normalized location of the pier based on similar triangles
    if bridge_diff[0] == 0:
        res = (projection_y-bridge_start[1])/bridge_diff[1]
    else:
        res = (projection_x-bridge_start[0])/bridge_diff[0]

    return res


cwd = os.getcwd()                   # Path of current directory
traffic_dir = cwd + '/traffic'      # Path of directory storing yearly traffic data by ship size class for each bridge

# Reading all the important parameters of the bridge
bridge_parameters = pd.read_csv('bridge_parameters.csv').to_numpy()
bridge_names = bridge_parameters[:, 0]                      # Name of bridge
bridge_lengths = bridge_parameters[:, 1]                    # Length of line joining the ends of the bridge (bank to bank)
bridge_pier_counts = bridge_parameters[:, 2]                # Number of piers on the bridge that are exposed to collision in some capacity
bridge_protection_counts = bridge_parameters[:, 3]          # Number of dolphins protecting the bridge
num_bridges = len(bridge_names)                             # Number of bridges
bridge_end_coordinates = bridge_parameters[:, 4:].reshape((num_bridges, 2, 2))      # Coordinates of the ends of the bridge (on both banks)

base_aberrancy = 0.6 * 1e-4         # Base aberrancy rate as per Section 3.14.5.2.3 of the AASHTO design code

lengths = np.array([165.0, 197.5, 232.5, 262.5, 287.5, 300.0])      # Nominal values of the considered length classes of the ships
num_lengths = len(lengths)                                          # Number of length classes

travel_centers = pd.read_csv('ship_travel_lines.csv').to_numpy()[:, 1:].flatten()       # Center of shipping lane computed using collected historical AIS data

ship_widths = np.zeros((num_bridges, num_lengths))
traffic_stats = np.zeros((num_bridges, num_lengths))     # mean, min, max
width_data = pd.read_csv('Average_Widths.csv')
for i in range(num_bridges):
    ship_widths[i, :] = width_data[width_data['Bridge'] == bridge_names[i]].to_numpy()[:, 1:].flatten()         # Average width of ship belonging to each of the
                                                                                                                # considered length classes for a given bridge
    traffic_data = pd.read_csv(traffic_dir + '/' + bridge_names[i] + ' Counts.csv').to_numpy()[:, 1:]         # Traffic seen by a given bridge as computed from
                                                                                                                # collected AIS data, divided by year (2018-2023)
                                                                                                                # and length class
    traffic_stats[i, :] = np.mean(traffic_data, axis=0)      # Average annual traffic of each class seen by the given bridge (between 2018-2023)

pier_location_data = pd.read_csv('bridge_piers.csv')                # Data on the location and sizes of the piers for each bridge
protection_location_data = pd.read_csv('bridge_protections.csv')    # Data on the location and size of dolphins for each bridge

# The following lines compute the probability of collision according to Section 3.14.5 in the AASHTO design code. The
# probability of collapse given collision is omitted in order to calculate the probability of collision itself.
collision_probabilities_unprotected = np.zeros(num_bridges)
collision_probabilities_protected = np.zeros(num_bridges)
for i in range(num_bridges):
    # Due to the geometry of the waterway and piers, the geometric factor of Bayonne bridge is computed slightly
    # differently than the other bridges. This flag informs the 'geometric_probability' function what procedure to use.
    if bridge_names[i] == 'BAYONNE BRIDGE (NY-NJ)':
        f = 1
    else:
        f = 0
    pier_parameters = pier_location_data[pier_location_data['Name'] == bridge_names[i]].to_numpy()[:, 1:]      # Reading information about the piers of a specific bridge
    protection_parameters = protection_location_data[protection_location_data['Name'] == bridge_names[i]].to_numpy()[:, 1:]     # Reading information about the dolphins of a specific bridge
    for l in range(num_lengths):                        # Iterate over all length classes
        if bridge_pier_counts[i] > 0:                   # Check if there are any piers
            for p in range(bridge_pier_counts[i]):      # Iterate over all piers of the bridge
                # Compute the normalized location of the pier
                pier_loc = normalized_pier_center_location(bridge_start=bridge_end_coordinates[i, 0, :],
                                                           bridge_end=bridge_end_coordinates[i, 1, :],
                                                           pier_center=pier_parameters[p, 1:3])

                # Compute probability of collision as per AASHTO design code Eq. 3.14.5-1, without considering
                # protection (PF), i.e., compute N x PA x PG
                probability_contribution_unprotected = (traffic_stats[i, l] * base_aberrancy *
                                                        geometric_probability(normalized_pier_location=pier_loc,
                                                                              waterway_length=bridge_lengths[i],
                                                                              pier_width=pier_parameters[p, 4],
                                                                              ship_length=lengths[l],
                                                                              travel_centerline=travel_centers[i],
                                                                              ship_width=ship_widths[i, l],
                                                                              bayonne_flag=f))
                # Store the 'unprotected' probability of collision
                collision_probabilities_unprotected[i] += probability_contribution_unprotected
                probability_contribution_protected = 0
                if bridge_protection_counts[i] == 0:        # Check if bridge has dolphins
                    probability_contribution_protected = probability_contribution_unprotected
                else:
                    # If bridge has dolphins, modify 'unprotected' probability of collision by including the protection
                    # factor, i.e., compute N x PA x PG x PF
                    probability_contribution_protected = (probability_contribution_unprotected *
                                                          protection_factor(pier_number=p,
                                                                            num_protections=bridge_protection_counts[i],
                                                                            protection_parameters=protection_parameters,
                                                                            ship_width=ship_widths[i, l]))
                # Store the probability of collision including protection
                collision_probabilities_protected[i] += probability_contribution_protected


estimated_return_period_stats = np.zeros(num_bridges)
for i in range(num_bridges):

    # Print the results
    print(bridge_names[i])
    print(collision_probabilities_unprotected[i])
    print('\n\n\n')

    # Compute return period. For bridges that are not at risk of a ship collision with pier (occurs when piers are on
    # land), return period is stored as -1.
    if collision_probabilities_protected[i] == 0:
        estimated_return_period_stats[i] = -1
    else:
        estimated_return_period_stats[i] = 1 / collision_probabilities_protected[i]

# Create DataFrames for the estimated collision probability and estimated return period with the bridge names
estimated_collision_stats_df = pd.DataFrame(collision_probabilities_protected, columns=['Estimated Probability of Collision'])
estimated_return_period_stats_df = pd.DataFrame(estimated_return_period_stats, columns=['Estimated Return Period of Collision'])

# Fill out the DataFrames for the estimated collision probability and estimated return period with the bridge names
estimated_collision_stats_df.insert(0, 'Name', bridge_names)
estimated_return_period_stats_df.insert(0, 'Name', bridge_names)


# # Save the DataFrames as CSV
os.chdir(cwd + '/Results')

estimated_collision_stats_df.to_csv('estimated_probability_of_collision_stats.csv')
estimated_return_period_stats_df.to_csv('estimated_return_period_stats.csv')
