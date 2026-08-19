## Written by Diran Jimenez

"""
This script constructs the URL's of all Marine Cadastre data from 2015-2024
"""

# First, construct the day portion of each date
days = ['0' + str(i) if i < 10 else str(i) for i in range(1,32)]

# Then, construct the date for each day in each month
JANUARY = ['_01_' + i for i in days]
FEBRUARY = ['_02_' + i for i in days[:28]]
MARCH = ['_03_' + i for i in days]
APRIL = ['_04_' + i for i in days[:30]]
MAY = ['_05_' + i for i in days]
JUNE = ['_06_' + i for i in days[:30]]
JULY = ['_07_' + i for i in days]
AUGUST = ['_08_' + i for i in days]
SEPTEMBER = ['_09_' + i for i in days[:30]]
OCTOBER = ['_10_' + i for i in days]
NOVEMBER = ['_11_' + i for i in days[:30]]
DECEMBER = ['_12_' + i for i in days]
    # The underlines are to make the date fit into the final url
    
months = [JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER]

# Produce one long list with every day in the calendar year
date_nums = [day for month in months for day in month]

# Next, the beginnning of each URL is the same for 2015 - 2023
base_url = 'https://coast.noaa.gov/htdata/CMSP/AISDataHandler/'

# Combine the date numbers with the general url format to get all URL's:
url_list_no_transceivers = [base_url + str(Year) + '/AIS_' + str(Year) + Date + '.zip' for Year in range(2015, 2018) for Date in date_nums]
url_list_with_transceivers = [base_url + str(Year) + '/AIS_' + str(Year) + Date + '.zip' for Year in range(2018, 2025) for Date in date_nums]

# Don't forget leap years!
url_list_with_transceivers.append('https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2016/AIS_2016_02_29.zip')
url_list_with_transceivers.append('https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2020/AIS_2020_02_29.zip')
url_list_with_transceivers.append('https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2024/AIS_2024_02_29.zip')