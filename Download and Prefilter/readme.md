The dataset used for this research project is hosted by [Marine Cadastre](https://hub.marinecadastre.gov/pages/vesseltraffic), and was downloaded locally.

The url constructor script creates a list of URL's to all files used in this study (January 1, 2015 to December 31, 2024). 
When this study began (and as of writing) the entire dataset for 2025 was unavailable. 

The prefilter script follows each link, downloads it, and applies some basic filters (e.g. removing small ships irrelevant to this study). 
The size of the entire pre-filtered dataset is about 362 GB. 
Since the files from 2015-2017 are slightly different from the rest (lack a column indicating the ship's Transceiver Class), they are handled and stored separately.
Thus, the script must be ran twice, once for 2015-2017 and again for 2018-2024.
