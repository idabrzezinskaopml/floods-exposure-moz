# Ida Brzezinska

# This script calculates the number of people affected in each flood event at the posto level 
# (as well as a % of total posto population)

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

# Folder with population count layers 
moz_pop_count_folder = r"C:\Users\idabr\OneDrive - University of Southampton\05 Paper 1\02 Data\04 WorldPop Population density\02 Population counts - unconstrained"

# Output - admin 3 shapefile with population flooded stats
adm3_pop_flooded_shp = "adm3_pop_flooded_shp"

# Output - zonal statistics table with total population per posto
adm3_total_pop_table = "adm3_total_pop_table"

# Output - raster with population flooded 
moz_pop_flooded = "moz_pop_flooded"

# Output - zonal statistics table with flooded population per posto
adm3_pop_flood_table = "adm3_pop_flood_table"

# Results folder
results_folder = "results"

# Output - table with posto-level flood exposure stats for each event
adm3_pop_flooded_stats = "adm3_pop_flooded_stats.csv"

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

# Get a list of rasters in the population count folder - all files ending with .tif 
pop_count_tif_files = [f for f in os.listdir(moz_pop_count_folder) if f.lower().endswith('.tif')]

# Print the list of .tif files
for tif_file in pop_count_tif_files:
    print(tif_file)

# Copy the admin 3 shapefile - this is where the population flooded stats will be stored
arcpy.CopyFeatures_management(moz_admin3_shp, adm3_pop_flooded_shp)     

# First run - since we don't have the 2021 and 2022 population counts yet, drop flood events from those years 

#raster_list = [r for r in raster_list if "From_2021" not in r and "From_2022" not in r]

## LOOP THROUGH FLOOD EVENTS WILL START HERE   

for raster in raster_list:

    ## STEP 1: GATHER DATA ##

    # Loop through all flood events - start with just one flood raster 
    flood_raster = raster

    # Extract the start date of the flood event (year) - this will always be 4 digits after "From_" in the file name
    flood_year = flood_raster.split("From_")[1][:4]

    # Get flood event ID  
    flood_event_id =  "DFO_" + flood_raster.split("_")[1]

    # Get the population count raster that matches the year of the flood
    pop_count_raster = os.path.join(moz_pop_count_folder, "moz_ppp_" + flood_year + ".tif")

    ## STEP 2: ALIGN SPATIAL REFERENCE ##

    # Check spatial reference of the population count and flood data - it should be WGS 1984  

    # Flood layer
    ref1 = arcpy.Describe(flood_raster).SpatialReference
    print(ref1)

    # Population count layer 
    ref2 = arcpy.Describe(pop_count_raster).SpatialReference

    if ref1.Name == ref2.Name:
        print("Spatial refernce aligned between flood and population data. Continuing loop...")
    else:
        print("Spatial reference not aligned. Flood event " + flood_event_id)
        continue # move on to the next flood

    ## STEP 3: ALIGN SPATIAL RESOLUTION ##

    # Resample the flood layer to the spatial resolution of population count data - using nearest neighbour 

    # Get the cell size of the population count raster 
    pop_count_cell_size = arcpy.Describe(pop_count_raster).meanCellWidth
    print(pop_count_cell_size)

    # Output to store the resampled flood raster 
    flood_raster_resample = flood_raster + "_resampled"

    # Resample flood layer to 100m spatial resolution using nearest neighbour
    arcpy.management.Resample(flood_raster, flood_raster_resample, cell_size=pop_count_cell_size, resampling_type="NEAREST")

    ## STEP 4: ZONAL STATS ##

    # Zonal statistics as table - count all the pixels from population data per posto (SUM)
    # This will give the total population in each posto - base for calculating the % of population flooded 
    arcpy.sa.ZonalStatisticsAsTable(adm3_pop_flooded_shp, "OBJECTID", pop_count_raster, adm3_total_pop_table, "DATA", "SUM")

    # Clean up table - round to the closest integer 

    # Field to round (overwrite)
    field_to_round = "SUM"

    # Use CalculateField to round in place
    arcpy.CalculateField_management(
        in_table=adm3_total_pop_table,
        field=field_to_round,
        expression="round(!{}!)".format(field_to_round),
        expression_type="PYTHON3"
    )

    # Join this table to the shapefile - keep only SUM column
    # Define the fields of the join
    shapefile_id_field = "OBJECTID"  # This is the unique ID field in the shapefile
    table_id_field = "OBJECTID_1"   # This is the ID field in the Zonal Statistics table that corresponds to the shapefile ID

    # Define the fields to join from the table
    fields_to_join = ["SUM"] 

    # Add the join
    arcpy.management.JoinField(adm3_pop_flooded_shp, shapefile_id_field, adm3_total_pop_table, table_id_field, fields_to_join)

    # Delete the table 
    arcpy.Delete_management(adm3_total_pop_table)

    # Mask the population count layer with the flood layer - get only flooded population 
    raster_masked = ExtractByMask(pop_count_raster, flood_raster_resample)
    raster_masked.save(moz_pop_flooded)

    # Delete the resampled raster 
    arcpy.Delete_management(flood_raster_resample)

    # Zonal statistics as table - get the number of people flooded in each posto (SUM)
    arcpy.sa.ZonalStatisticsAsTable(adm3_pop_flooded_shp, "OBJECTID", moz_pop_flooded, adm3_pop_flood_table, "DATA", "SUM")

    # Field to round (overwrite)
    field_to_round = "SUM"

    # Use CalculateField to round in place
    arcpy.CalculateField_management(
        in_table=adm3_pop_flood_table,
        field=field_to_round,
        expression="round(!{}!)".format(field_to_round),
        expression_type="PYTHON3"
    )

    # Rename the field 
    old_field_name = "SUM" 
    new_field_name = "Pop_Flood_" + flood_event_id 

    # Rename the field (and alias)
    arcpy.management.AlterField(adm3_pop_flood_table, old_field_name, new_field_name, new_field_alias=new_field_name)

    # Join back with the admin 3 shapefile - keep only the population flooded field
    # Define the fields to join from the table
    fields_to_join = [new_field_name] 

    # Add the join
    arcpy.management.JoinField(adm3_pop_flooded_shp, shapefile_id_field, adm3_pop_flood_table, table_id_field, fields_to_join)

    # Remove the table 
    arcpy.Delete_management(adm3_pop_flood_table)

    # Clean up the population flooded field - replace missings with 0s 
    expression = "0 if !" + new_field_name + "! is None else !" + new_field_name + "!"  

    # Run the Field Calculator
    arcpy.management.CalculateField(adm3_pop_flooded_shp, new_field_name, expression, "PYTHON3")

    # Now calculate the proportion of population flooded in each posto 
    new_field = "Pct_P_Flood_" + flood_event_id

    # Add a new field to hold the percentage (as double)
    arcpy.AddField_management(adm3_pop_flooded_shp, new_field, "DOUBLE")  

    # Calculate the percentage (rounded to two decimal points)
    expression = "round((!" + new_field_name + "! / !SUM!) * 100, 2)"  

    arcpy.CalculateField_management(
        in_table=adm3_pop_flooded_shp,
        field=new_field,
        expression=expression,
        expression_type="PYTHON3"
    )

    # Delete the SUM field
    arcpy.DeleteField_management(adm3_pop_flooded_shp, "SUM")



# Aggregate table to get total number of people flooded between 2008-2020
# Note: waiting for WorldPop population count data for 2021 and 2022

# Identify fields with "Pop" in the name
fields = arcpy.ListFields(adm3_pop_flooded_shp)
pop_fields = [f.name for f in fields if "Pop" in f.name]

# New field name
popsum_field = "Pop_Flood_2008_2020"

# Add a new field which will store the sum the total number of people flooded 2008-2022
arcpy.AddField_management(adm3_pop_flooded_shp, popsum_field, "DOUBLE")

# Build the expression: sum of all pop fields
expression = " + ".join([f"!{f}!" for f in pop_fields])

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_pop_flooded_shp,
    field=popsum_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Field for number of flood events (which had any impact on the population)
num_flood_field = "num_floods"

# Create column for number of flood events 
arcpy.AddField_management(adm3_pop_flooded_shp, num_flood_field, "DOUBLE", field_alias="Number of floods")

# Count the number of "Pop" columns that are non-zero
# Columns are already save in the pop_fields list
expression = "sum([1 for x in [{}] if x and x > 0])".format(
    ", ".join([f"!{f}!" for f in pop_fields])
)

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_pop_flooded_shp,
    field=num_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Get average number of people flooded in a flood event
# Calculate this by diving the total number of people flooded between 2008-2020 by the number of floods in this period 

# Field for average area flooded
avg_pop_flood_field = "avg_pop_flood_2008_2020"

# Create the field
arcpy.AddField_management(adm3_pop_flooded_shp, avg_pop_flood_field, "DOUBLE", field_alias="Avg no people flooded 2008-20")

# Expression - total number of people flooded between 2008-2020 over the number of floods in this period 
# Round to the closest integer 
expression = f"round(!{popsum_field}! / !{num_flood_field}!)"

# Run the calculation
arcpy.CalculateField_management(
    in_table=adm3_pop_flooded_shp,
    field=avg_pop_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Replace NA values with 0s 
expression = "0 if !" + avg_pop_flood_field + "! is None else !" + avg_pop_flood_field + "!"  

# Run the Field Calculator
arcpy.management.CalculateField(adm3_pop_flooded_shp, avg_pop_flood_field, expression, "PYTHON3")

# Final statistic - average % of population flooded between 2008-2020

# Name of the field 
avg_prop_pop_flood_field = "avg_p_pop_flood_2008_2020"

# Create the field
arcpy.AddField_management(adm3_pop_flooded_shp, avg_prop_pop_flood_field, "DOUBLE", field_alias="Avg % pop flooded 2008-20")

# Expression - average of the % of population flooded across all flood events 

# Get the column names that have % of population flooded
pop_prop_fields = [f.name for f in fields if "Pct_P" in f.name]

# Turn into an expression
field_expression = ", ".join([f"!{field}!" for field in pop_prop_fields])

# Generate the expression for averaging non-zero proportions 
# Round to two decimal points 
expression = f"""
round(sum(v for v in [{field_expression}] if v is not None and v > 0) / (!num_floods! if !num_floods! > 0 else 1), 2)
"""
# Calculate field
arcpy.CalculateField_management(
    in_table=adm3_pop_flooded_shp,
    field=avg_prop_pop_flood_field,
    expression=expression,
    expression_type="PYTHON3"
)

# Export table 
arcpy.conversion.ExportTable(adm3_pop_flooded_shp, os.path.join(results_folder, adm3_pop_flooded_stats))

