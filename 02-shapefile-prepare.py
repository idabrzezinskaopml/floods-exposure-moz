# Ida Brzezinska

# This script prepares the shapefiles needed for this analysis. This includes the country-level Mozambique shapefile and admin level 3 shapefile. 
# I will use the EA-level shapefile for 2017 that Luciano harmonised to the 2019/20 IOF survey.

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

# Path to the geodatabase from the ArcGIS "Descriptive analysis flood poverty Mozambique" project
moz_des_flood_arcgis = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\06 GIS\Descriptive_analysis_flood_poverty_Mozambique\Descriptive_analysis_flood_poverty_Mozambique.gdb"

# Path to the Mozambique country shapefile (which has already been aggregated from the EA-level shapefile)
moz_country_shapefile = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\03 Code\arcpy-analyses\results\MOZ_2017_country.shp"

# EA-level shapefile from Luciano 
EA_level_shapefile_moz = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\01 Poverty\04 Household data MZ\01 Luciano's data\Data\Shapefile\GeoCorrected_MOZ.shp"

# Output - country-level shapefile to be saved in the geodatabase
moz_country_shapefile_geo = "MOZ_2017_country"

# Output - admin 3 level shapefile to be saved in the geodatabase
moz_admin3_shp = "moz_admin3_shp"

# Output - admin 1 level shapefile 
moz_admin1_shp = "moz_admin1_shp"

# Output - admin 2 level shapefile
moz_admin2_shp = "moz_admin2_shp"

# Results folder 
results_folder = "results"

# Shapefile format for admin level 2 
moz_admin2_shp_results = "moz_admin2_shp.shp"

# Environment settings #####################################

# Set ArcGIS workspace to the flood folder (where input data is found). 
env.workspace = moz_des_flood_arcgis

# Prepare shapefiles #####################################

# Copy the country shapefile over to the geodatabase 
arcpy.CopyFeatures_management(moz_country_shapefile, moz_country_shapefile_geo)

# Look at the fields in the EA-level shapefile 
# Get fields
fields = arcpy.ListFields(EA_level_shapefile_moz)

# Print fields
for field in fields:
    print(f"Field Name: {field.name}, Field Type: {field.type}")


# Dissolve the EA-level shapefile at admin 3 level and save in the geodatabase. Keep the Posto character name 
arcpy.management.Dissolve(EA_level_shapefile_moz, moz_admin3_shp, "PA_ID", statistics_fields=[("Posto", "MAX")])

# Double check the fields in the admin level 3 shapefile
fields2 = arcpy.ListFields(moz_admin3_shp)

# Print fields
for field in fields2:
    print(f"Field Name: {field.name}, Field Type: {field.type}")

# Rename the "MAX_Posto" column 
old_field_name = "MAX_Posto" 
new_field_name = "Posto"

# Rename the field
arcpy.management.AlterField(moz_admin3_shp, old_field_name, new_field_name)    

# Create an admin 1 (province level shapefile)
arcpy.management.Dissolve(EA_level_shapefile_moz, moz_admin1_shp, "CodProv", statistics_fields=[("Provincia", "MAX")])

# Rename the "MAX_Provincia" column 
old_field_name = "MAX_Provincia" 
new_field_name = "Provincia"

# Rename the field
arcpy.management.AlterField(moz_admin1_shp, old_field_name, new_field_name)    

# Province names in the shapefile: "Niassa", "Cabo Delgado", "Nampula", "Zambezia", "Tete", "Manica", "Sofala", "Inhambane",
# "Gaza", "Maputo Provincia", "Maputo Cidade"

# Dissolve the EA-level shapefile at administrative level 2 (district)
# Variable to use: ID_DIST (unique district codes)
arcpy.management.Dissolve(EA_level_shapefile_moz, moz_admin2_shp, "ID_DIST", statistics_fields=[("Distrito", "MAX")]) # keep character district name

# Double check the fields in the admin level 2 shapefile
fields3 = arcpy.ListFields(moz_admin2_shp)

# Print fields
for field in fields3:
    print(f"Field Name: {field.name}, Field Type: {field.type}")

# Rename the "MAX_Distrito" column 
old_field_name = "MAX_Distrito" 
new_field_name = "Distrito"

# Rename the field
arcpy.management.AlterField(moz_admin2_shp, old_field_name, new_field_name)

# Get current working directory
cwd = os.getcwd()

# Save in the results folder 
arcpy.CopyFeatures_management(moz_admin2_shp, os.path.join(cwd, results_folder, moz_admin2_shp_results))





