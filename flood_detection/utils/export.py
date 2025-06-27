# Original script Colin Doyle; material was edited and added by Devin Routh
# Export functions
# These are different functions to export the maps to assets or cloud buckets

import ee
ee.Initialize(project='moz-hydrafloods')

# --------------------------------------------------------
# This function is used to export maps that were created from DFO events with an
# index number
    #    Args:
    #        flood_img : the standard Earth Engine Image object
    #        bounds: the ROI
    #        save_path: the asset path into which you'd like to save the image
    #        res: the resolution (in meters) per pixel of the image
    #    Returns:
    #        - Saves the image into the GEE Code Editor Asset path
# --------------------------------------------------------
def to_asset(flood_img, bounds, save_path, res=250):

    # This Fusion Table is the QC database from 11/12/18
    # dfo_props = ee.FeatureCollection('ft:1P_wUQQJqghdnN3UMAcXDlrbQFpJWN-md2eH1WprS')

    # This Fustino Table is the DFO Database from July 16th, 2019
    dfo_props = ee.FeatureCollection("projects/moz-hydrafloods/assets/emdat_moz_flood_shp")
    dfo_id = flood_img.get('id').getInfo()
    props = ee.Feature(dfo_props.filterMetadata('ID', 'equals', dfo_id).first())\
                                .getInfo()['properties']
    
    print(props)
    print("Printed properties")

    # Clean up some of the DFO database
    if props.get('GLIDENUMBE')=='0':
        glide_number = 'NA'
    else:
        glide_number = props.get('GLIDENUMBE')

    if props.get('OTHERCOUNT')=='0':
        dfo_other_country = 'NA'
    else:
        dfo_other_country = props.get('OTHERCOUNT')

    # ------------------------ EXPORT RESULTS-------------------------- #
    start_formatted = ee.Date(props.get('BEGAN')).format('yyyyMMdd').getInfo()
    end_formatted = ee.Date(props.get('ENDED')).format('yyyyMMdd').getInfo()
    save_name = "DFO_" + str(dfo_id) + "_From_" + str(start_formatted) + "_to_" + str(end_formatted) 
    save_asset = str(save_path + "/" + save_name)

    task = ee.batch.Export.image.toAsset(
        image=flood_img.set({
                            #'glide_index': ee.String(glide_number),
                             #'dfo_country': ee.String(props.get('COUNTRY')),
                             #'dfo_other_country': ee.String(dfo_other_country),
                             #'dfo_centroid_x': ee.Number(props.get('LONG')),
                             #'dfo_centroid_y': ee.Number(props.get('LAT')),
                             #'dfo_validation_type': ee.String(props.get("VALIDATION")),
                             'dfo_main_cause': ee.String(props.get("MAINCAUSE"))}),
                             #'dfo_severity': ee.Number(props.get("SEVERITY")),
                             #'dfo_dead': ee.Number(props.get("DEAD")),
                             #'dfo_displaced': ee.Number(props.get("DISPLACED"))}),
        description="ExportToAsset DFO" + str(dfo_id),
        assetId=save_asset,
        region=bounds.getInfo()['coordinates'],
        scale=res,
        maxPixels=1e12
    )
    task.start()
    return

# --------------------------------------------------------
# This function is an exact copy of the script above except
# it is used to export maps that were created from the
# map_Event_ByROIDateRange function to a CSB
#
    # Args:
    #     flood_img : the standard Earth Engine Image object
    #     bounds: the ROI
    #     cloud_path: the name of the Cloud Bucket to upload the file (as a string)
    #     res: the resolution (in meters) per pixel of the image
    #
    # Returns:
    #     - Saves the image into the GEE Code Editor Asset path

# --------------------------------------------------------
def to_gcs(flood_img, bounds, cloud_path, name_prefix='DFO', res=250):

    start_formatted = ee.Date(flood_img.get('began')).format('yyyyMMdd').getInfo()
    end_formatted = ee.Date(flood_img.get('ended')).format('yyyyMMdd').getInfo()
    index = flood_img.get('id').getInfo()
    save_name = name_prefix + "_" + str(index) + "_From_" + str(start_formatted) + "_to_" + str(end_formatted)
    save_csb = str(save_name)

    # ------------ EXPORT RESULTS! ------------ #
    task = ee.batch.Export.image.toCloudStorage(
        image=flood_img.toFloat(),
        description="ExportToCSB DFO" + str(index),
        bucket=cloud_path,
        fileNamePrefix=save_csb,
        region=bounds.getInfo()['coordinates'],
        scale=res,
        maxPixels=1e12
    )
    task.start()
    return
