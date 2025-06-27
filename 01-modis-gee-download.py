# Ida Brzezinska

# This script uses the Google Earth Engine API to export .tif files from
# MCD12Q1.061 MODIS Land Cover Type Yearly Global 500m dataset annually for 2008-2022 to a Google Drive.

# hydrafloods_env environment contains all the GEE packages

# Import modules needed
import ee
import time

# Authenticate to GEE
ee.Authenticate()

# Initialise the GEE API - connect to the hydrafloods project on Google Earth Engine
ee.Initialize(project='moz-hydrafloods')

# Define the region of interest (Mozambique) using a bounding box (approximate)
mozambique = ee.Geometry.Rectangle([29.711948, -27.367828, 41.339403, -9.972775])

# Filter the MODIS MCD12Q1 dataset by date (2008-2022) and select the LC_Prop2 band (FAO-LCCS2 land use layer)

# Get dataset with the appropriate raster band and time period
dataset = ee.ImageCollection('MODIS/061/MCD12Q1') \
    .select('LC_Prop2') \
    .filterDate('2008-01-01', '2022-12-31') \
    .map(lambda image: image.clip(mozambique))


# Loop over the years 2008-2022
for year in range(2008, 2023):
    # Filter the dataset for the current year
    year_dataset = dataset.filterDate(f'{year}-01-01', f'{year}-12-31')

    # Get the first image for the current year
    image = year_dataset.first()

    # Define the export task to Google Drive for the current year
    export_task = ee.batch.Export.image.toDrive(
        image=image,
        description=f'MODIS_Land_Cover_{year}',  # Dynamic name for each year
        folder='GEE_Exports',  # Folder name in Google Drive
        region=mozambique,  # Define the region (Mozambique)
        scale=500,  # Pixel size (MODIS is 500m resolution)
        crs='EPSG:4326'  # Coordinate reference system (WGS84)
    )

    # Start the export task
    export_task.start()

    print(f"Export task started for MODIS Land Cover {year}.")

