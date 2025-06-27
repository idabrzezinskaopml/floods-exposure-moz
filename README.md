# Estimation of flood exposure at administrative level 3 in Mozambique (2008-2022)
This repository contains code for estimating population and cropland flooded in every major flood event in Mozambique between 2008-2022 at administrative level 3 (posto). This analysis uses Python, ArcGIS, and Google Earth Engine (GEE).

## Data sources
1. **Flood**: [Global Flood Database](https://global-flood-database.cloudtostreet.ai/) (GFD) for gridded data on all major flood events in Mozambique between 2008-2018 at a 250m spatial resolution. Since the GFD records end in 2018, to identify all major flood events in Mozambique between 2018-2022, I apply the flood detection algorithm underlying the GFD from the [MODIS_GlobalFloodDatabase](https://github.com/cloudtostreet/MODIS_GlobalFloodDatabase/tree/main) repository to daily MODIS imagery. 
   - [Dartmouth Flood Observatory](https://floodobservatory.colorado.edu/Archives/ArchiveNotes.html) (DFO) archive of all flood events in Mozambique between 2018-2021.
   - [EM-DAT](https://www.emdat.be/) database for archive of all natural disasters in Mozambique between 2021-2022 (focusing on floods). Given DFO records end in 2021.
2. **Population**: [WorldPop unconstrained population counts](https://hub.worldpop.org/) for Mozambique at a 100m spatial resolution for 2008-2020.
3. **Cropland**: [MODIS Land Cover Type (MCD12Q1) Version 6.1](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1) dataset at a 500m spatial resolution for 2008-2022.
4. **Administrative boundaries**: Enumeration-area level shapefile from the 2017 Mozambique Population and Housing Census, aggregated to administative level 3. Note that this shapefile is not publicly available, but other datasets with administrative boundaries for Mozambique can be found online.

## Overview of scripts 

| Script  | Description |
| ------------- | ------------- |
| 01-modis-gee-download.py | Download MODIS Land Cover data for Mozambique from GEE |
| 02-shapefile-prepare.py  | Prepare shapefiles for all adminsitrative levels in Mozambique from the EA-level census shapefile |
| 03-flood-event-list.py  | Construct spatial records of flood events to be used in the flood detection algorithm |
| 04-gfd-flood-detection.py  | Apply flood detection algorithm to MODIS imagery in GEE  |
| 05-gee-flood-export.py  | Export GEE assets to Google Drive |
| 06-flood-layer-prep.py | Prepare flood layers - mask to Mozambique, leave only the "flooded" raster band, import to ArcGIS database |
| 07-cropland-layer-prep.py | Process land cover data - extract cropland pixels |
| 08-population-exposed.py | Estimate number of people exposed to flooding at posto level |
| 09-cropland-flooded.py | Estimate area of cropland flooded at posto level |

Note that all the tools and utilities underpinning the flood detection algorithm are in the `flood_detection` folder. 
