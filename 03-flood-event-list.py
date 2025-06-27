# Ida Brzezinska

# This script prepares the shapefile with flood events in Mozambique between 2018-2022.
# There is a shapefile ready from the Darthmouth Flood Observatory Archive - with start and end dates of the event. 
# Last event recorded in the DFO archive for Mozambique is in February 2021. 
# Last event recorded in the whole database is for October 2021. 
# We could use the EM-DAT database to supplement the period between October 2021-December 2022. 

# Last flood detected in Mozambique in the Global Flood Database is on the 1st January 2017
# The first flood recorded in the DFO archive but not included in the GFD is on the 14th January 2018. 
# There are 11 flood events in the DFO archive in Mozambique between 14-01-2018 - 20-02-2021.

# This will be an input into the flood detection script: 04-gfd-flood-detection.py. 
# I will need to upload the final shapefile as an asset in the GEE project. 

# The EM-DAT database has 7 records for natural disasters in Mozambique between 2021-2022. 
# One of them is a drought so can be discarded. Remaining events are either floods, storms, or cyclones.
# Two flood events in 2021 are already captured in the DFO database, so no need to include them. 
# The time period matches the DFO database. 
# One event does not have a specific location beyond Mozambique - should we keep it? 
# The other events are referenced by province or districts. 

# Environment setting = arcgis_env

# Import modules needed 
import arcpy
import os
from arcpy import env
from arcpy.sa import *
import datetime

#overwrite existing data. 
arcpy.env.overwriteOutput = True 

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Set global variables #####################################

# Path to the geodatabase from the ArcGIS "Descriptive analysis flood poverty Mozambique" project
moz_des_flood_arcgis = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\06 GIS\Descriptive_analysis_flood_poverty_Mozambique\Descriptive_analysis_flood_poverty_Mozambique.gdb"

# DFO Flood Archive shapefile
dfo_flood_archive_shp = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\03 Flood\03 Global Flood Observatory\FloodArchive_region.shp"

# Excel file with relevant flood events recorded by EM-DAT in 2022 (complements DFO records)
em_dat_moz_flood = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\03 Flood\07 EM-DAT\public_emdat_moz_floods_2022.xlsx"

# Results folder
results_folder = "results"

# Admin 1 shapefile for Mozambique in the geodatabase
moz_admin1_shp = "moz_admin1_shp"

# Output - DFO shapefile with flood events in Mozambique on or after 14-01-2018
dfo_moz_flood_shp = "dfo_moz_flood_shp"

# Output - EM-DAT shapefile with flood events in Mozambique for 2022
emdat_moz_flood_shp = "emdat_moz_flood_shp"

# Environment settings #####################################

# Set ArcGIS workspace to the flood folder (where input data is found). 
env.workspace = moz_des_flood_arcgis

# Filter for the shapefile: country (Mozambique) and start period (on and after 14th January 2018)

# Make a feature layer from the DFO archive shapefile
arcpy.management.MakeFeatureLayer(dfo_flood_archive_shp, "temp_layer")

# SQL query
sql_query = """ "COUNTRY" = 'Mozambique' AND "BEGAN" >= date '2018-01-14' """

# Select features by attributes
arcpy.management.SelectLayerByAttribute("temp_layer", "NEW_SELECTION", sql_query)

# Save selected features to the GDB
arcpy.management.CopyFeatures("temp_layer", dfo_moz_flood_shp)

# Need to change the format of the Date - needs to be "YYYY-MM-DD" for GEE

# Copy the shapefile over to the results folder and save in .shp format - to be uploaded to GEE 
arcpy.CopyFeatures_management(dfo_moz_flood_shp, results_folder + "//" + dfo_moz_flood_shp + ".shp")

# Supplement the rest with EM-DAT database - can use province polygons from the Mozambique country shapefile 

# The EM-DAT table will need to be transformed into a shapefile with a minimum of three fields: "ID", "Began", "Ended"
# I could link the events with the provinces and districts mentioned as affected. I already have start and end date.

# Define flood events from EM-DAT database for 2022 - follow the DFO archive format
# Spelling of provinces must match the admin 1 shapefile

flood_events = [
    {
        "ID": "1",
        "BEGAN": "2022-01-24",
        "ENDED": "2022-02-07",
        "MAINCAUSE": "Tropical Storm Ana",
        "provinces": ["Nampula", "Zambezia", "Tete", "Cabo Delgado", "Sofala", "Niassa"]
       
    },
    {
        "ID": "2",
        "BEGAN": "2022-02-18",
        "ENDED": "2022-02-21",
        "MAINCAUSE": "Tropical Storm Dumako",
        "provinces": ["Zambezia", "Nampula", "Niassa", "Tete", "Sofala", "Manica"]
        
    },
    {
        "ID": "3",
        "BEGAN": "2022-03-11",
        "ENDED": "2022-03-29",
        "MAINCAUSE": "Tropical Cyclone Gombe",
        "provinces": ["Nampula", "Zambezia", "Sofala", "Tete", "Niassa"]
        
    }
]

# Get spatial reference from the admin 1 shapefile
spatial_ref = arcpy.Describe(moz_admin1_shp).spatialReference

# Create the final shapefile
arcpy.CreateFeatureclass_management(
    out_path=arcpy.env.workspace,
    out_name=os.path.basename(emdat_moz_flood_shp),
    geometry_type="POLYGON",
    spatial_reference=spatial_ref
)

# Add required fields
arcpy.AddField_management(emdat_moz_flood_shp, "ID", "SHORT")
arcpy.AddField_management(emdat_moz_flood_shp, "BEGAN", "DATE")
arcpy.AddField_management(emdat_moz_flood_shp, "ENDED", "DATE")
arcpy.AddField_management(emdat_moz_flood_shp, "MAINCAUSE", "TEXT")

# Insert data
with arcpy.da.InsertCursor(emdat_moz_flood_shp, ["SHAPE@", "ID", "BEGAN", "ENDED", "MAINCAUSE"]) as insert_cursor:
    for event in flood_events:
        # Select affected provinces
        province_list = "', '".join(event["provinces"])
        where_clause = f"\"Provincia\" IN ('{province_list}')"
        arcpy.MakeFeatureLayer_management(moz_admin1_shp, "temp_layer", where_clause)

        # Dissolve selected provinces into one geometry
        dissolved_output = os.path.join(arcpy.env.workspace, "dissolved")
        arcpy.Dissolve_management("temp_layer", dissolved_output)

        # Insert the dissolved geometry with event attributes
        with arcpy.da.SearchCursor(dissolved_output, ["SHAPE@"]) as search_cursor:
            for row in search_cursor:
                insert_cursor.insertRow((
                    row[0],
                    event["ID"],
                    datetime.datetime.strptime(event["BEGAN"], "%Y-%m-%d"),
                    datetime.datetime.strptime(event["ENDED"], "%Y-%m-%d"),
                    event["MAINCAUSE"]
                ))

        # Clean up
        arcpy.Delete_management("temp_layer")
        arcpy.Delete_management(dissolved_output)

# Save as a shapefile in the results folder - to be uploaded to GEE
arcpy.CopyFeatures_management(emdat_moz_flood_shp, results_folder + "//" + emdat_moz_flood_shp + ".shp")
