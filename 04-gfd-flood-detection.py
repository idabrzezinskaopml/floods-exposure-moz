# Ida Brzezinska

# This script uses the flood detection algorithm underlying the Global Flood Database 
# From this GitHub repo: https://github.com/cloudtostreet/MODIS_GlobalFloodDatabase
# It applies the flood detection algorithm to MODIS satellite imagery 
# to identify floods in Mozambique between 2018-2022 (a period which the GFD doesn't cover)
# Flood events are identified based on records from the Dartmouth Flood Observatory: https://floodobservatory.colorado.edu/. 
# Records include spatial extent and duration of event. 
# The output will be rasters with flood extents for each flood event in Mozambique between 2018-2022 at 250m spatial resolution. 

# hydrafloods_env contains all the environment settings for Google Earth Engine (GEE)

# Import modules needed
import ee
from flood_detection import modis    # this is the flood_detection folder from the repo, which contains all the tools 
from flood_detection.utils import export, misc

import time, os, csv

# Authenticate to GEE
ee.Authenticate()

# Initialise the GEE API - connect to the hydrafloods project on Google Earth Engine
ee.Initialize(project='moz-hydrafloods')

# INPUTS
# Enter the ID of the GEE Asset that contains the list of events to be mapped
# and cast as ee.FeatureCollection(). GEE Asset must have at least 3 columns
# titled: "ID", "BEGAN", "ENDED". In this version of the script, the GEE
# Asset also needs to have polygons associated with each event that will be used
# to select watersheds from global HydroSheds data to use as the area to map the
# event over.

# This GEE Asset is the DFO archive for Mozambique between 14-01-2018 - 20-02-2021
#event_db = ee.FeatureCollection("projects/moz-hydrafloods/assets/dfo_moz_flood_shp").sort("ID")

# This GEE Asset is the EM-DAT archive with flood events for Mozambique in 2022
event_db = ee.FeatureCollection("projects/moz-hydrafloods/assets/emdat_moz_flood_shp").sort("ID")

# GEE Asset folder and Google Cloud Storage for image collection
gcs_folder = "gfd_mozambique"
asset_path = "projects/moz-hydrafloods/assets"  # Upload shapefile with events as an asset here 

#-------------------------------------------------------------------------------
# PROCESSING STARTS HERE

# Create list of events from input gee asset
event_ids = ee.List(event_db.filterMetadata("ID", "greater_than", 0).aggregate_array('ID')).sort() # first asset ID for EM-DAT is 1
id_list = event_ids.getInfo()
id_list = [int(i) for i in id_list]

# NOTE: Code snippet for when you are re-running floods in error log
# errors = "error_logs\\gfd_v3\\3Day_otsu_error_log_23_07_2019_1.csv"
# with open(errors) as f:
#     id_list = sorted([int(float(row["dfo_id"])) for row in csv.DictReader(f)])

# NOTE: ID List for Validation Floods
# id_list = [1641,1810,1818,1910,1925,1931,1971,2024,2035,2045,2075,2076,2099,
#            2104,2119,2143,2167,2177,2180,2183,2191,2206,2214,2216,2261,2269,
#            2296,2303,2332,2345,2366,2395,2443,2444,2458,2461,2463,2473,2507,
#            2543,2570,2584,2586,2597,2599,2629,2640,2650,2688,2711,2780,2821,
#            2829,2832,2940,2947,2948,3070,3075,3076,3094,3123,3132,3162,3166,
#            3179,3198,3205,3218,3267,3274,3282,3285,3306,3345,3365,3366,3464,
#            3476,3544,3567,3572,3625,3657,3658,3667,3673,3678,3692,3696,3754,
#            3786,3801,3846,3850,3856,3871,3894,3916,3931,3977,4019,4022,4024,
#            4083,4098,4115,4159,4163,4171,4179,4188,4211,4218,4226,4241,4258,
#            4272,4314,4315,4325,4339,4340,4346,4357,4364,4427,4428,4435,4444,
#            4464,4507,4516]

snooze_button = 1
for event in id_list:

    # Check if we have worn out GEE
    if snooze_button%50==0: #if true - hit the snooze button
        print("---------------------Giving GEE a breather for 15 mins--------------------")
        time.sleep(900)

    # Get event date range
    flood_event = ee.Feature(event_db.filterMetadata('ID', 'equals', event).first())
    began = str(ee.Date(flood_event.get('BEGAN')).format('yyyy-MM-dd').getInfo())
    ended = str(ee.Date(flood_event.get('ENDED')).format('yyyy-MM-dd').getInfo())
    #thresh_type = str(flood_event.get('ThreshType').getInfo())

    thresh_type = 'standard' # Threshold options are 'standard' or 'otsu'

    # Use polygon from event GEE Asset to select watersheds from global
    # HydroSheds data choose level3, level4, or level5
    watershed = misc.get_watersheds_level4(flood_event.geometry()).union().geometry()
    # watershed = misc.get_islands(flood_event.geometry()).union().geometry()

    try:
        # Map the event. Returns 4 band image: 'flooded', 'duration',
        # 'clearViews', 'clearPerc'
        print("Mapping Event {0} - {1} threshold".format(event, thresh_type))
        flood_map = modis.dfo(watershed, began, ended, thresh_type, "3Day")

        # Apply slope mask to remove false detections from terrain
        # shadow. Input your image and choose a slope (in degrees) as a threshold
        flood_map_slope_mask = misc.apply_slope_mask(flood_map, thresh=5)
        print("Applied the slope mask")

        # Get permanent water from JRC dataset at MODIS resolution
        perm_water = misc.get_jrc_perm(watershed)
        print("Returned the permanent water mask")

        # Get countries within the watershed boundary
        country_info = misc.get_countries(watershed)
        print("Got country info")

        # Add permanent and seasonal water as bands to image
        # Format the final DFO algorithm image for export
        dfo_final = ee.Image(flood_map_slope_mask).addBands(perm_water)\
                            .set({'id': event,
                                'gfd_country_code': str(country_info[0]),
                                'gfd_country_name': str(country_info[1])})
        
        # Print when finished
        print("Got final DFO image")


    except Exception as e:

        print("DFO Algorithm Error {0} - Cataloguing and moving onto next event".format(event))
        print("-------------------------------------------------")
        snooze_button+=1
        continue

    # Try exporting to your Google Drive 
        
    try:
    #     Export to an asset. This function needs the ee.Image of the flood map
    #     from map_DFO_event, the roi that is returned from the
    #     map_floodEvent_MODIS, the path to where the asset will be saved, and
    #     the resolution (in meters) to save it (default = 250m)
    #     Remember to set the "threshold" parameter in the export function - standard or otsu

        export.to_asset(dfo_final, watershed.bounds(), asset_path, 250)

        print("Exported asset")
        
        # Google Cloud Storage incurs a charge - leave out for now
        #export.to_gcs(dfo_final, watershed.bounds(), gcs_folder, 'DFO', 250)

        print("Uploading DFO {0} to GEE Assets & GCS".format(event))
        print("-------------------------------------------------")

    except Exception as e:
        s = str(e)
        print("Export Error DFO {0} - Cataloguing and moving onto next event".format(event))
        print("-------------------------------------------------")

    # Add to the snooze_button so we don't make Noel angry.
    snooze_button+=1


