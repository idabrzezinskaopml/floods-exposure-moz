# Ida Brzezinska

# This script exports the flood layers saved as assets in Google Earth Engine to the Google Drive as .tif files

# Import the needed libraries
import ee

# Authenticate to GEE
ee.Authenticate()

# Initialise the GEE API - connect to the hydrafloods project on Google Earth Engine
ee.Initialize(project='moz-hydrafloods')

# Path to the GEE asset folder
project_path = 'projects/moz-hydrafloods/assets/'

# List all assets in the folder
assets = ee.data.listAssets({'parent': project_path}).get('assets', [])

# Version 1: All flood events from DFO archive
# Filter assets starting with 'DFO'
#dfo_assets = [a for a in assets if a['name'].split('/')[-1].startswith('DFO')]

# Version 2: export only EM-DAT flood layers (files starting with: DFO_1 DFO_2 DFO_3)
allowed_prefixes = ("DFO_1", "DFO_2", "DFO_3")

dfo_assets = [
    a for a in assets
    if a['name'].split('/')[-1].startswith(allowed_prefixes)
]

# Check which assets were picked up
print(dfo_assets)

# Export each DFO asset to Google Drive
for asset in dfo_assets:
    asset_id = asset['name']
    asset_name = asset_id.split('/')[-1]
    image = ee.Image(asset_id).uint16()

    task = ee.batch.Export.image.toDrive(
        image=image,
        description=f'Export_{asset_name}',
        folder='GEE_Exports',
        fileNamePrefix=asset_name,
        scale=250, # 250m spatial resolution - MODIS
        region=image.geometry(),
        maxPixels=1e13
    )

    task.start()
    print(f'Started export: {asset_name}')