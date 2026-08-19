## Written by Diran Jimenez
## Based on code written by Promit Chakroborty

import numpy as np
from scipy.signal import find_peaks
import scipy.stats as stats


def find_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    A = np.array([[x2-x1, x3-x4], [y2-y1, y3-y4]])
    b = np.array([x3-x1, y3-y1])

    t,u = np.linalg.inv(A) @ b

    a = x1 + t * (x2 - x1)
    b = y1 + t * (y2 - y1)

    return a, b

# Function to normalize the intersection point with respect to the bridge start and end points
def normalize_coordinate(x, y, bridge_start, bridge_end):
    x1, y1 = bridge_start
    x2, y2 = bridge_end

    dist_b = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    dist_p = np.sqrt((x - x1)**2 + (y - y1)**2)

    n = dist_p / dist_b

    return n

def angle_between_vectors(vX, vY, wX, wY):
    # Formula using extended arctan function
    # Source: https://wumbo.net/formulas/angle-between-two-vectors-2d/
    # units = radians
    angle = np.arctan2((vX * wY - vY * wX),(vX * wX + vY * wY))
    # angle = np.arccos( (vX * wX + vY * wY) / (np.sqrt(vX**2 + vY**2) * np.sqrt(wX**2 + wY**2)) )
    
    return angle



def triangular_projection(first_point, second_point):
    lon1, lat1 = first_point
    lon2, lat2 = second_point
    
    # Radius of the Earth
    R = 6371e3 # meters
    x = (lon2-lon1) * np.pi/180 * np.cos( ((lat1+lat2)/2) * np.pi/180)
    y = (lat2-lat1) * np.pi/180
    d = np.sqrt(x*x + y*y) * R 
    return d # meters


def pier_protection(pier_x, pier_y, bridge_start, bridge_end, ship_width, bridge_length, 
                    dolphin_x_list, dolphin_y_list, dolphin_width_list):
    """
    Determine how protected a pier is.
        If a pier is completely protected -> return 1
        If a pier is not protected at all -> return 0
        
    Protection comes from dolphins. A dolphin's
    protection = the fraction of angles a ship 
    could strike a pier that the dolphin covers. 
    One pier could be protected by multiple 
    dolphins, and one dolphin can cover multiple
    piers. See below edge case:
        
        
        _____           _____           _____  
       |Pier|          |Pier|          |Pier|               
       ‾‾‾‾‾           ‾‾‾‾‾           ‾‾‾‾‾
                ^                ^
               <D>              <D>
                v                v



    This function operates on just one pier, but 
    takes multiple dolphins as input. The math is
    taken from Section 3.14.5.5 of the AASHTO 
    design code. 
    
    There are exactly two adjustments made. Section
    3.14.5.5 assumes that a dolphin sits directly
    in front of a pier. This is handled by offsetting
    the angle of protection provided by the difference
    in angle between the position of the dolphin and  
    the perpendicular angle of the pier.
    
    Second, the protection provided by multiple dolphins
    is handled by tracking the angles covered by each 
    dolphin, and not adding additional protection when 
    there's overlap. 
    
    Note: ship width's is expected to be unitless
          It is normalized by the bridge's length
    """
    
    # Determine the pier perpendicular
    pier_perpendicular = np.arctan2((bridge_end[0]-bridge_start[0]),(-bridge_end[1]-bridge_start[1]))
    """
    A 90 degree rotation applied to (x,y) is (-y,x)
    However, np.arctan2 expects the y coordinate first, then x. 
    Hence, np.arctan2 is fed (x,-y) to get the 90 degree rotation
    """
    
    
    num_dolphins = len(dolphin_width_list)
    if num_dolphins == 0:
        return 0
    
    # Resolution of discretization
    dx = 0.001
    
    # Assume ships will NOT approach a pier from behind
        # Since risk from the other direction of traffic is handled separately
    # Hence, the angles that can be covered range from -pi/2 to pi/2
    theta_range = np.arange(-np.pi/2, np.pi/2, dx)
    angle_coverage = {a: 0 for a in theta_range}
    
    for i in range(num_dolphins):
        dolph_x = dolphin_x_list[i]
        dolph_y = dolphin_y_list[i]
        L = triangular_projection([dolph_x, dolph_y], [pier_x, pier_y]) / bridge_length
        
        D_E = dolphin_width_list[i] + (0.75 * ship_width)
        
        theta = np.arcsin(D_E / (2 * L))
        
        dolph_to_pier_x = pier_x - dolph_x 
        dolph_to_pier_y = pier_y - dolph_y 
        
        
        """
        We want the angle betwee the pier perpendicular and the dolphin direction.
        However, the normal angle from the pier may face away from
        the dolphin. See below. 
        
            ^           |
           <D>          |
            v         _____
                     |Pier|     --Normal Angle-->
                     ‾‾‾‾‾
                        |
                        |
                        |
        
        To fix this, we find the angle between the dophin and the normal, as
        well as the dolphin and the negative normal, and keep the smallest one
        
        """
        regular_phi = angle_between_vectors(dolph_to_pier_x, dolph_to_pier_y,
                                    np.cos(pier_perpendicular), np.sin(pier_perpendicular))
        
        opposite_phi = angle_between_vectors(dolph_to_pier_x, dolph_to_pier_y,
                                             -np.cos(pier_perpendicular), -np.sin(pier_perpendicular))
        
        if np.abs(regular_phi) < np.abs(opposite_phi):
            phi = regular_phi
        else:
            phi = opposite_phi
        
        for a in angle_coverage:
            if (phi - theta) <= a <= (phi + theta):
                angle_coverage[a] = 1
                
    angle_distribution = stats.norm(loc=0, scale=((30*np.pi)/180))      # Distribution on potential approach angles.
    
    # If an angle is protected by the pier, theta_protected = 1
    # If an angle isn't, theta_protected = 0
    theta_protected = np.array(list(angle_coverage.values()))
    
    # Find the area under the angle distribution where the pier is protected
    protection_factor = np.trapz(angle_distribution.pdf(theta_range) * theta_protected,
                                 dx = dx)                       # Only keep area which is protected
    
    return protection_factor


# Function to compute the location of the pier along the line joining the two ends of the bridge (from bank to bank)
def normalized_pier_center_location(bridge_start, bridge_end, pier_center):

    bridge_diff = bridge_end - bridge_start  # difference in lat/long coordinates of the bridge

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


# This finds the peak traffic in a distribution and returns its location
def locate_peak_traffic(normalized_intersections, resolution):
    # First, identify where points are along the normalized intersections
    counts, bins, = np.histogram(normalized_intersections, 
                                 bins=np.linspace(0,1,num=int(1/resolution)))
    
    bin_starts = bins[:-1]
    bin_ends = bins[1:]
    bin_centers = 0.5 * (bin_starts + bin_ends)

    travel_centerline_indices, _ = find_peaks(counts, prominence = np.max(counts) * 0.25,
                                              distance=20) # Parameters tuned by hand
    
    travel_centers = bin_centers[travel_centerline_indices]
    
    return travel_centers

# This finds the center of the navigation channel by finding the midpoint of signifcant traffic
def locate_channel_center(normalized_intersections, resolution):
    counts, bins, = np.histogram(normalized_intersections, 
                                 bins=np.linspace(0,1,num=int(1/resolution)))
    
    bin_starts = bins[:-1]
    bin_ends = bins[1:]
    bin_centers = 0.5 * (bin_starts + bin_ends)
    
    count_cdf = np.cumsum(counts) / sum(counts)
    
    distribution_start_threshold = 0.05
    distribution_end_threshold = 0.95
    
    dist_start, dist_end = (bin_centers[next(index for (index,value) in enumerate(count_cdf) if value > threshold)]
                            for threshold in [distribution_start_threshold, distribution_end_threshold])
    
                    # This is left as a single element array for convenience later
    channel_center = np.array([0.5 * (dist_start + dist_end)])
    
    return channel_center

    
def side(bridge_start, bridge_end, point_x, point_y):
    
    # Let P = (point_x, point_y)
    # Let A = (line_start_x, line_start_y)
    # Let B = (line_end_x, line_end_y)
    # The below formula evaluates the dot product of PA and PB
    # The sign determines the side of the point
        # If a point is on one side of a line, then the angle from PA to PB is positive
        # Opposite if the point is on the other side of the line
    
    line_start_x, line_start_y = bridge_start
    line_end_x, line_end_y = bridge_end
    
    side = (line_end_x - line_start_x) * (point_y - line_start_y) - (line_end_y - line_start_y) * (point_x - line_start_x)
    
    return np.sign(side)

def direction(bridge_start, bridge_end, first_point, last_point):
    
    # Get the side of the first point
    # Get the side of the second point
    
    first_point_x, first_point_y = first_point
    last_point_x, last_point_y = last_point
    
    
    first_side = side(bridge_start, bridge_end, first_point_x, first_point_y)
    
    last_side = side(bridge_start, bridge_end, last_point_x, last_point_y)

    # direction == True => went from negative side to positive side
    direction = (first_side < last_side)
    
    return direction

def remove_ship_teleportation(df):
    
    # Ships sometimes 'teleport', i.e. have a faulty broadcast which is hundreds of miles from its actual position
    
    meters_to_natuical_miles = 0.00054
    
    distances = triangular_projection([df["LON"].values[:-1:2], df["LAT"].values[:-1:2]], 
                                      [df["LON"].values[1::2],  df["LAT"].values[1::2]]) * meters_to_natuical_miles
        # units = nautical miles
    
    # Calculate the time between each pair of points
    t = df["BaseDateTime"].astype('datetime64[s]').values
    times = (t[1::2] - t[:-1:2]).astype(np.int32) / 3600 
        # units = hours
    times = np.where(times == 0, 0.0001, times) # Avoid divide by 0 errors
    
    # Calculate the actual velocity of each pair of points
    v = distances / times
    
    # Label each pair of points with the same velocity
    velocities = np.zeros(2 * v.shape[0])
    velocities[:-1:2] = v
    velocities[1::2] = v
        # units = knots
    
    # Only keep points that aren't too fast or too slow
    travels_at_appropraite_speeds = (velocities >= 0.5) & (velocities <= 25) # knots
        # Large Containership speeds peaked around 25 knots
        # Source: https://transportgeography.org/contents/chapter5/maritime-transportation/evolution-containerships-classes/
    
    cleaned_traffic = df[travels_at_appropraite_speeds]
    
    return cleaned_traffic

# When a bridge has multiple travel lanes, they each must be identified.
# It is faster to manually identify these travel lanes than to develop code which performs the same task
bridges_with_multiple_travel_lanes = {
    "RICHMOND_BRIDGE_(CA)": {
        True: np.array([0.487, 0.733]),
        False: np.array([0.482, 0.735])
        },
    "ALFRED_ZAMPA_MEMORIAL_BRIDGE_(CA)": {
        True: np.array([0.35, 0.738]),
        False:np.array([0.36, 0.73])
        },
    "HUEY_P_LONG_BRIDGE_(LA)": {
        True: np.array([0.41, 0.695]),
        False: np.array([0.42, 0.695])
        },
    "HORACE_WILKINSON_BRIDGE_(LA)": {
        True: np.array([0.13, 0.31]),
        False: np.array([0.13, 0.31, 0.76])
        },
    "SAN_FRANCISCO_OAKLAND_BAY_BRIDGE_(CA)": {
        True: np.array([0.22, 0.4, 0.55, 0.76]),
        False: np.array([0.23, 0.41, 0.56, 0.75])
        },
    "CARQUINEZ_BRIDGE_(CA)": {
        True: np.array([0.35, 0.74]),
        False: np.array([0.36, 0.75])
        },
    "SUNSHINE_BRIDGE_(FL)": {
        True: np.array([0.7]),
        False: np.array([0.37, 0.66])
        },
    "WALT_WHITMAN_BRIDGE_(NJ_PA)": {
        True: np.array([0.5, 0.94]),
        False: np.array([0.5, 0.95]),
        },
    "GOLDEN_GATE_BRIDGE_(CA)": {
        True: np.array([0.42, 0.64]),
        False: np.array([0.7])
        },
    "LEWIS_AND_CLARK_BRIDGE_(OR_WA)": {
        True: np.array([0.55, 0.88]),
        False: np.array([0.6])
        }
}
