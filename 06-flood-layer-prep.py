# Ida Brzezinska

# This script prepares the flood layers for all flood events in Mozambique between 2008-2022.
# It will import the multi-band rasters obtained from the Global Flood Database 
# and by applying the GFD flood detection algorithm to MODIS imagery. 
# For each layer, it will extract just the "flooded" band, mask to the country boundaries of Mozambique
# and save in the ArcGIS geodatabase 

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

# Folders with flood extents 
flood_folder = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\03 Flood\01 Global Flood Database"

# Number of raster band that contains the "flooded" layer - in this case Band 1 
flood_band_index = 1  

# Environment settings #####################################

# Set ArcGIS workspace to the ArcGIS geodatabase 
env.workspace = moz_des_flood_arcgis

# Set extent to Mozambique
arcpy.env.extent = moz_country_shapefile_geo

# Set condition value - keeping only values of 1 (flooded), non-flooded areas will be NA. 
# This will allow me to use the flood layer as a mask later on 
remap = RemapValue([[1, 1]])

# Loop through nested folders
for root, dirs, files in os.walk(flood_folder):
    for file in files:
        if file.endswith(".tif"):
            raster_path = os.path.join(root, file)
            raster_name = os.path.splitext(file)[0]
            
            print(f"Processing {raster_path}")
            
            # Step 1: Extract flood band (use MakeRasterLayer + CopyRaster to extract a single band)
            flood_band = arcpy.ia.ExtractBand(raster_path, flood_band_index)
            
            # Step 2: Mask using Mozambique boundary
            masked_raster = ExtractByMask(flood_band, moz_country_shapefile_geo)

            # Step 3: Recode 0 values to missing 
            output_name = raster_name + "_masked" 
            Reclassify(masked_raster, "VALUE", remap, "NODATA").save(output_name)
            
            print(f"Saved: {output_name}")