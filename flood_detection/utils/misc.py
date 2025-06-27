# Import packages
import ee

ee.Initialize(project='moz-hydrafloods')

# Series of functions to extract overlapping watersheds from roi region. We use
# HydroSheds database provided a different levels. Also - functions for islands
# shapefiles are provided as HydroSheds does not cover some small islands.
def get_watersheds_level5(dfo_feature):
    basins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_5")
    return basins.filterBounds(dfo_feature)

def get_watersheds_level4(dfo_feature):
    basins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_4")
    return basins.filterBounds(dfo_feature)

def get_watersheds_level3(dfo_feature):
    basins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_3")
    return basins.filterBounds(dfo_feature)

#def get_islands(dfo_feature):
#    islands = ee.FeatureCollection('ft:14BijFeJ0MiV1CeP7FBst8P4Kf1Se0HK5Sfh78hJB')
#    return islands.filterBounds(dfo_feature)

#def get_american_somoa(dfo_feature):
#    asm = ee.FeatureCollection('ft:1C79v82bd1QfIsdGfDFOo2sz2XIHJCiVnXWXBeX0_')
#    return asm.filterBounds(dfo_feature)

# applySlopeMask() applies a mask to remove pixels that are greater than a
# certain slope based on SRTM 90-m DEM V4 the only parameter is the slope
# threshold, which is default to 5%
def apply_slope_mask(img, thresh=5):
    srtm = ee.Image("USGS/GMTED2010_FULL")
    slope = ee.Terrain.slope(srtm)
    masked = img.updateMask(slope.lte(thresh))
    return masked.set({'slope_threshold': thresh})

# this returns the permanent water mask from the JRC Global Surface Water
# dataset. It gets the permanent water from the transistions layer
def get_jrc_perm(roi_bounds):
    jrc_perm_water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")\
                    .select("transition").eq(1).unmask()
    return jrc_perm_water.select(['transition'],['jrc_perm_water']).clip(roi_bounds)

def get_jrc_yearly_perm(began, roi):
    ee_began = ee.Date(began)
    jrc_year = ee.Algorithms.If(ee_began.get('year')\
                    .gt(2022), 2022, ee_began.get('year'))
    jrc_perm = ee.Image(ee.ImageCollection('JRC/GSW1_4/YearlyHistory')\
                    .filterBounds(roi)
                    .filterMetadata('year', "equals", jrc_year).first())\
                    .remap([0, 1, 2, 3], [0, 0, 0, 1]).unmask()\
                    .select(['remapped'],['jrc_perm_yearly'])
    return jrc_perm.updateMask(jrc_perm)

def get_countries (roi):
    countries = ee.FeatureCollection("USDOS/LSIB/2017")
    img_country = countries.filterBounds(roi)

    cc_list = img_country.distinct('OBJECTID').aggregate_array('OBJECTID').getInfo()
    cc_list = [str(c) for c in cc_list]

    country_list = img_country.distinct('COUNTRY_NA').aggregate_array('COUNTRY_NA').getInfo()
    country_list = [str(c) for c in country_list]

    return cc_list, country_list
    
