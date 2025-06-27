# Ida Brzezinska

# This script calculates the area of cropland flooded in each flood event at the posto level 
# (as well as a % of total posto cropland that was flooded)

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

# Admin 3 shapefile for Mozambique 
moz_admin3_shp = "moz_admin3_shp"

# Output - admin 3 shapefile with cropland flooded stats 
adm3_crop_flooded_shp = "adm3_crop_flooded_shp"

# Output - reprojected admin 3 shapefile
adm3_crop_flooded_shp_proj = "adm3_crop_flooded_shp_proj"

# Results folder
results_folder = "results"

# Output - csv table with posto-level cropland flooded stats
adm3_crop_flooded_table = "adm3_crop_flooded_table.csv"

# Environment settings #####################################

# Set ArcGIS workspace to the ArcGIS geodatabase 
env.workspace = moz_des_flood_arcgis

# Set extent to Mozambique
arcpy.env.extent = moz_admin3_shp

# Flood layers - DFO_* file name. Flood layers are already in the geodatabase 
# Create a list of raster names that start with "DFO_"
raster_list = arcpy.ListRasters("DFO_*")
print(raster_list)

# Check length of list - we should have 24 events 
length_list = len(raster_list)
print(length_list)

# Copy the admin 3 shapefile - this is where the cropland flooded stats will be stored
arcpy.CopyFeatures_management(moz_admin3_shp, adm3_crop_flooded_shp) 

# Load the WKT2 text for Lambert Azim Mozambique from: https://epsg.io/42106
wkt2 = """
PROJCRS["WGS84_/_Lambert_Azim_Mozambique",
    BASEGEOGCRS["unknown",
        DATUM["Unknown based on Normal Sphere (r=6370997) ellipsoid",
            ELLIPSOID["Normal Sphere (r=6370997)",6370997,0,
                LENGTHUNIT["metre",1]]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433]]],
    CONVERSION["unknown",
        METHOD["Lambert Azimuthal Equal Area (Spherical)",
            ID["EPSG",1027]],
        PARAMETER["Latitude of natural origin",5,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",20,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["False easting",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]],
    CS[Cartesian,2],
        AXIS["(E)",east,
            ORDER[1],
            LENGTHUNIT["metre",1]],
        AXIS["(N)",north,
            ORDER[2],
            LENGTHUNIT["metre",1]],
    ID["EPSG",42106]]
"""

# Create a SpatialReference object from the WKT2 string
spatial_ref = arcpy.SpatialReference(text=wkt2)

# Reproject the shapefile to Lambert Azim Mozambique - to be consistent with rasters
arcpy.management.Project(adm3_crop_flooded_shp, adm3_crop_flooded_shp_proj, spatial_ref)

# Delete the old shapefile 
arcpy.Delete_management(adm3_crop_flooded_shp)

### LOOP STARTS HERE ###

for raster in raster_list:

    ## STEP 1: LOAD DATA ##

    # Loop through all flood events - start with just one flood raster 
    flood_raster = raster

    # Extract the start date of the flood event (year) - this will always be 4 digits after "From_" in the file name
    flood_year = flood_raster.split("From_")[1][:4]

    # Get flood event ID  
    flood_event_id =  "DFO_" + flood_raster.split("_")[1]

    # Get the MODIS cropland raster which matches the year of the flood - already in the geodatabase
    cropland_raster = "MODIS_Land_Cover_" + flood_year + "_cropland"

    # Check where we are  
    print("-------------------------------------------------")
    print("Gathered the data. Processing flood event " + flood_event_id)

    ## STEP 2: ALIGN SPATIAL REFERENCE ##

    # Change spatial reference to equal-area projection. This is to be able to calculate area in ha 

    # Check spatial reference - both rasters are likely in WGS 1984 

    # Cropland raster 
    ref1 = arcpy.Describe(cropland_raster).SpatialReference

    # Flood raster
    ref2 = arcpy.Describe(flood_raster).SpatialReference

    # Output - cropland raster reprojected 
    cropland_raster_proj = cropland_raster + "_proj"

    # Reproject the raster
    arcpy.management.ProjectRaster(cropland_raster, cropland_raster_proj, spatial_ref)

    # Output - flood raster reprojected
    flood_raster_proj = flood_raster + "_proj"

    # Reproject the raster
    arcpy.management.ProjectRaster(flood_raster, flood_raster_proj, spatial_ref)
    print("Aligned spatial reference")

    ## STEP 3: ALIGN SPATIAL RESOLUTION ##

    # Resample the cropland data from 500m to the spatial resolution of the flood data (250m) - using nearest neighbour
 
    # Get the cell size of the flood  raster 
    flood_cell_size = arcpy.Describe(flood_raster_proj).meanCellWidth

    # Output to store the resampled cropland raster 
    cropland_raster_resample = cropland_raster_proj + "_resampled"

    # Resample flood layer to 100m spatial resolution using nearest neighbour
    arcpy.management.Resample(cropland_raster_proj, cropland_raster_resample, cell_size=flood_cell_size, resampling_type="NEAREST")
    print("Aligned spatial resolution")

    ## STEP 4: MASK CROPLAND USING FLOOD LAYER ##

    # Output - cropland flooded raster
    cropland_flooded = cropland_raster_resample + "_flood"

    # Extract by mask - using the flood layer. Get flooded cropland.
    raster_masked = ExtractByMask(cropland_raster_resample, flood_raster_proj)
    raster_masked.save(cropland_flooded)
    print("Masked the cropland layer using flood data")

    ## STEP 5: ZONAL STATS ##

    # First get the total amount of cropland (ha) in each posto

    # Cropland pixels are coded as values of 1 in the raster. 
    # Using the "SUM" function in zonal stats will get the total number of cropland pixels in a posto.
    # "SUM" also automatically calculates AREA - using exact pixel size (rather than average). 
    # Output is in m2. I can convert units to ha (1 ha = 10,000 m2). 

    # Output - table with total number of cropland pixels
    adm3_total_crop_table = "adm3_total_crop_table"

    # Calculate sum of cropland pixels using zonal stats 
    arcpy.sa.ZonalStatisticsAsTable(adm3_crop_flooded_shp_proj, "OBJECTID", cropland_raster_resample, adm3_total_crop_table, "DATA", "SUM")

    # Clean up the table - divide the m2 by 10,000 to get hectares and round the "AREA" column to the closest integer

    # Field to round (overwrite)
    field_to_round = "AREA"

    # Use CalculateField to round in place
    arcpy.CalculateField_management(
        in_table=adm3_total_crop_table,
        field=field_to_round,
        expression=f"round(!{field_to_round}! / 10000)",
        expression_type="PYTHON3"
    )

    # Merge back to the shapefile (this is a temporary column, which will be deleted once we get % of cropland flooded)
   
    # Define the fields of the join
    shapefile_id_field = "OBJECTID"  # This is the unique ID field in the shapefile
    table_id_field = "OBJECTID_1"   # This is the ID field in the Zonal Statistics table that corresponds to the shapefile ID

    # Define the fields to join from the table
    fields_to_join = ["AREA"] 

    # Add the join
    arcpy.management.JoinField(adm3_crop_flooded_shp_proj, shapefile_id_field, adm3_total_crop_table, table_id_field, fields_to_join)

    # Calculate the area of cropland flooded 

    # Output - table with total number of cropland flooded pixels
    adm3_total_crop_flood_table = "adm3_total_crop_flood_table"

    # Calculate sum of cropland pixels using zonal stats 
    arcpy.sa.ZonalStatisticsAsTable(adm3_crop_flooded_shp_proj, "OBJECTID", cropland_flooded, adm3_total_crop_flood_table, "DATA", "SUM")

    # Calculate the area of cropland flooded in ha and round to the closest integer 
    arcpy.CalculateField_management(
        in_table=adm3_total_crop_flood_table,
        field=field_to_round,
        expression=f"round(!{field_to_round}! / 10000)",
        expression_type="PYTHON3"
    )

    # Clean up variable name - to reflect ha 
    # Rename the field 
    old_field_name = "AREA" 
    new_field_name = "Crop_Flood_ha_" + flood_event_id 

    # Rename the field (and alias)
    arcpy.management.AlterField(adm3_total_crop_flood_table, old_field_name, new_field_name, new_field_alias=new_field_name)

    # Join back with the shapefile
    arcpy.management.JoinField(adm3_crop_flooded_shp_proj, shapefile_id_field, adm3_total_crop_flood_table, table_id_field, new_field_name)

    # Delete unnecessary layers 

    # List of files to delete
    files_to_delete = [
        adm3_total_crop_flood_table,
        cropland_flooded,
        cropland_raster_resample,
        flood_raster_proj,
        cropland_raster_proj,
        adm3_total_crop_table
    ]

    for file in files_to_delete:
        arcpy.Delete_management(file)

    # Calculate proportion of cropland flooded in each posto
    new_field = "Pct_C_Flood_" + flood_event_id

    # Add a new field to hold the percentage (as double)
    arcpy.AddField_management(adm3_crop_flooded_shp_proj, new_field, "DOUBLE")  

    # Calculate the percentage (rounded to two decimal points)
    expression = "round((!" + new_field_name + "! / !AREA!) * 100, 2)"  

    arcpy.CalculateField_management(
        in_table=adm3_crop_flooded_shp_proj,
        field=new_field,
        expression=expression,
        expression_type="PYTHON3"
    )

    # Delete the AREA field 
    arcpy.DeleteField_management(adm3_crop_flooded_shp_proj, "AREA")

    # Replace NA values with 0s 
    expression = "0 if !" + new_field_name + "! is None else !" + new_field_name + "!"  

    # Run the Field Calculator
    arcpy.management.CalculateField(adm3_crop_flooded_shp_proj, new_field_name, expression, "PYTHON3")

    # The same for the area (in ha)
    expression = "0 if !" + new_field + "! is None else !" + new_field + "!"  

    # Run the Field Calculator
    arcpy.management.CalculateField(adm3_crop_flooded_shp_proj, new_field, expression, "PYTHON3")

# Aggregate table to get total area of cropland flooded between 2008-2022 - or average per flood event?
# Get another table which is at the country-year level. Trends over time (this could be done in R)

# Identify fields with "Crop" in the name
fields = arcpy.ListFields(adm3_crop_flooded_shp_proj)
crop_fields = [f.name for f in fields if "Crop" in f.name]

# New field name
cropsum_field = "Crop_Flood_ha_2008_2022"

# Add a new field which will store the sum the total area of cropland flooded 2008-2022
arcpy.AddField_management(adm3_crop_flooded_shp_proj, cropsum_field, "DOUBLE")

# Build the expression: sum of all crop fields
expression = " + ".join([f"!{f}!" for f in crop_fields])

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_crop_flooded_shp_proj,
    field=cropsum_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Field for number of flood events
num_flood_field = "num_floods"

# Create column for number of flood events 
arcpy.AddField_management(adm3_crop_flooded_shp_proj, num_flood_field, "DOUBLE", field_alias="Number of floods")

# Count the number of "Crop_Flood_ha_DFO" columns that are non-zero
# Columns are already save in the crop_fields list
expression = "sum([1 for x in [{}] if x and x > 0])".format(
    ", ".join([f"!{f}!" for f in crop_fields])
)

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_crop_flooded_shp_proj,
    field=num_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Get average area of cropland flooded in a flood event
# Calculate this by diving the total area of cropland flooded between 2008-2022 by the number of floods in this period 

# Field for average area flooded
avg_crop_flood_field = "avg_crop_flood_2008_2022"

# Create the field
arcpy.AddField_management(adm3_crop_flooded_shp_proj, avg_crop_flood_field, "DOUBLE", field_alias="Avg ha crop flooded 2008-22")

# Expression - total area flooded between 2008-2022 over the number of floods in this period 
# Round to the closest integer 
expression = f"round(!{cropsum_field}! / !{num_flood_field}!)"

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_crop_flooded_shp_proj,
    field=avg_crop_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Replace NA values with 0s 
expression = "0 if !" + avg_crop_flood_field + "! is None else !" + avg_crop_flood_field + "!"  

# Run the Field Calculator
arcpy.management.CalculateField(adm3_crop_flooded_shp_proj, avg_crop_flood_field, expression, "PYTHON3")

# Final statistic - average % of cropland flooded between 2008-2022

# Name of the field 
avg_prop_crop_flood_field = "avg_p_crop_flood_2008_2022"

# Create the field
arcpy.AddField_management(adm3_crop_flooded_shp_proj, avg_prop_crop_flood_field, "DOUBLE", field_alias="Avg % crop flooded 2008-22")

# Expression - average of the % of crop flooded across all flood events 

# Get the column names that have % of cropland flooded
crop_prop_fields = [f.name for f in fields if "Pct_C" in f.name]

# Turn into an expression
field_expression = ", ".join([f"!{field}!" for field in crop_prop_fields])

# Generate the expression for averaging non-zero proportions 
# Round to two decimal points 
expression = f"""
round(sum(v for v in [{field_expression}] if v is not None and v > 0) / (!num_floods! if !num_floods! > 0 else 1), 2)
"""
# Calculate field
arcpy.CalculateField_management(
    in_table=adm3_crop_flooded_shp_proj,
    field=avg_prop_crop_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Save shapefile attribute table as csv 
arcpy.conversion.ExportTable(adm3_crop_flooded_shp_proj, os.path.join(results_folder, adm3_crop_flooded_table))


