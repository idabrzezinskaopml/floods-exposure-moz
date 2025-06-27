# Ida Brzezinska 

# This script imports the MODIS Land Cover layers for 2008-2022, 
# masks them to Mozambique country boundaries, and extracts "Cropland pixels".
# In the FAO-LCCS2 land use classification system, there are three categories of cropland: 
# 1: Pixel values of 25 (Forest/Cropland Mosaics: mosaics of small-scale cultivation 40-60% with >10% natural tree cover)
# 2: Pixel values of 35 (Natural Herbaceous/Croplands Mosaics: mosaics of small-scale cultivation 40-60% with natural shrub or herbaceous vegetation.)
# 3: Pixel values of 36 (Herbaceous Croplands: dominated by herbaceous annuals (<2m). At least 60% cover. Cultivated fraction >60%.)

# Environment setting = arcgis_env

# Import modules needed 
import arcpy
import os
from arcpy import env
from arcpy.sa import *

#overwrite existing data. 
arcpy.env.overwriteOutput = True 

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Set global variables #####################################
moz_des_flood_arcgis = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\06 GIS\Descriptive_analysis_flood_poverty_Mozambique\Descriptive_analysis_flood_poverty_Mozambique.gdb"

# Country-level shapefile 
moz_country_shapefile_geo = "MOZ_2017_country"

# Folder with land cover layers 
land_cover_folder = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\03 Flood\04 Land cover class\MODIS Land Cover MCD12 GEE"

# Environment settings #####################################

# Set ArcGIS workspace to the ArcGIS geodatabase 
env.workspace = moz_des_flood_arcgis

# Set extent to Mozambique
arcpy.env.extent = moz_country_shapefile_geo

# Set condition value - cropland pixel values according to FAO-LCCS2 land use classification system
remap = RemapValue([[25, 1], [35, 1], [36, 1]])

# Loop through nested folders
for root, dirs, files in os.walk(land_cover_folder):
    for file in files:
        if file.endswith(".tif"):
            raster_path = os.path.join(root, file)
            raster_name = os.path.splitext(file)[0]
            
            print(f"Processing {raster_path}")
            
            # Step 1: Mask using Mozambique boundary
            masked_raster = ExtractByMask(raster_path, moz_country_shapefile_geo)
            
            # Step 2: Reclassify cropland pixels 
            raster_output = raster_name + "_cropland"
            Reclassify(masked_raster, "VALUE", remap, "NODATA").save(raster_output)

            print(f"Saved: {raster_output}")
