############################################
# 

import ee
import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..'))
from parameters import *
from utils import GenerateBandNames, filter_partial_tiles
from background_methods import method1, method5
from clustering import ClusterClouds




def SelectBackgroundImages(sentinel_img, methodNumber, number_of_images,
                            number_preselect, region_of_interest):
    """ Return the NUMBER_IMAGES previous images with cloud cover

    Arguments
        :param sentinel_img: 
        :param methodNumber: 
        :param number_of_images: 
        :param number_preselect: 
        :param region_of_interest: 
    """

    # Retrieve Sentinel Collection - filter by area of interest + Tile
    sentinel_collection = ee.ImageCollection("COPERNICUS/S2") \
                            .filterBounds(region_of_interest) \
                            .filter(ee.Filter.eq("MGRS_TILE", sentinel_img.get('MGRS_TILE')))

    # Remove image of same date (+ or - NUMBER_HOURS hours)
    time_start = sentinel_img.get('system:time_start')
    filter_before = ee.Filter.lt('system:time_start', ee.Number(time_start).subtract(NUMBER_HOURS*3600000))
    filter_after  = ee.Filter.gt('system:time_start', ee.Number(time_start).add(NUMBER_HOURS*3600000))
    sentinel_collection = sentinel_collection.filter(ee.Filter.Or(filter_before, filter_after))

    # Remove partial tiles images
    sentinel_collection = filter_partial_tiles(sentinel_collection, sentinel_img, region_of_interest)

    # Background selection according to the method number
    if methodNumber == 1:
        imgColl = method1(sentinel_img, sentinel_collection, number_of_images)
    elif methodNumber == 5:
        imgColl = method5(sentinel_img, sentinel_collection, number_of_images, number_preselect)
    else:
        raise NotImplementedError(
            "Method %s is not implemented. Please chose eathier the 1 or 5 methods" % methodNumber)


    # Get rid of images with many invalid values
    def _count_valid(img):
        mascara = img.mask()
        mascara = mascara.select(SENTINEL2_BANDNAMES)
        mascara = mascara.reduce(ee.Reducer.allNonZero())

        dictio = mascara.reduceRegion(reducer=ee.Reducer.mean(),
                                      geometry=region_of_interest,
                                      bestEffort=True)

        img = img.set("valids", dictio.get("all"))
        return img

    return imgColl.map(_count_valid).sort("valids").limit(number_of_images)


def SelectImagesTraining(sentinel_img, imgColl, number_of_images):
    """ Given a sentinel image, it returns the number_of_images previous 
    images building the background.

    Arguments:
        :param sentinel_img: sentinel 2 image
        :param imgColl: background image collection
        :param number_of_images: number of image to keep
        :return: ee.Image (GEE)
    """
   
    size_img_coll = ee.Number(imgColl.size())
    offset = ee.Number(0).max(size_img_coll.subtract(number_of_images))
    imagenes_training = imgColl.toList(count=number_of_images, offset=offset)

    # Join images into a single image
    for lag in range(1, number_of_images + 1):
        image_add = ee.Image(imagenes_training.get(number_of_images - lag))
        new_band_names = GenerateBandNames(SENTINEL2_BANDNAMES, "_lag_" + str(lag))

        image_add = image_add.select(SENTINEL2_BANDNAMES, new_band_names)
        sentinel_img = sentinel_img.addBands(image_add)
        sentinel_img = sentinel_img.set("system:time_start_lag_" + str(lag), image_add.get("system:time_start"))

    return sentinel_img


def CloudClusterScore(img, region_of_interest, method_number,
                      number_of_images=PARAMS_SELECTBACKGROUND_DEFAULT['number_of_images'],
                      number_preselect=PARAMS_SELECTBACKGROUND_DEFAULT['number_preselect']
                      ):
    """
    Function to obtain the cloud cluster score from percentile methods
    Params are defined in parameters.py file
        :param img: 
        :param region_of_interest: 
        :param method_number=PARAMS_SELECTBACKGROUND_DEFAULT['method_number']: 
        :param number_of_images=PARAMS_SELECTBACKGROUND_DEFAULT['number_of_images']: 
        :param number_preselect=PARAMS_SELECTBACKGROUND_DEFAULT['number_preselect']: 
        :return:  cloud mask (1: cloud, 0: clear)
    """

    params = PARAMS_CLOUDCLUSTERSCORE_DEFAULT

    # Forecast band names
    forecast_bands_sentinel2 = [i + "_forecast" for i in SENTINEL2_BANDNAMES]

    # Select background image in one image                  
    imgColl = SelectBackgroundImages(img,
                                     method_number,
                                     number_of_images,
                                     number_preselect,
                                     region_of_interest)
    
    # Summarize BackGround images in one band
    image_with_lags = SelectImagesTraining(img, imgColl, number_of_images)

    if method_number in [1,5]:
        # Compute percentile aggregation
        img_percentile = imgColl.reduce(reducer=ee.Reducer.percentile(percentiles=[50]))

        reflectance_bands_sentinel2_perc50 = [i + "_p50" for i in SENTINEL2_BANDNAMES]
        img_forecast = img_percentile.select(reflectance_bands_sentinel2_perc50,
                                        forecast_bands_sentinel2)
    else:
        raise NotImplementedError("Method %s is not implemented. Please chose eathier the 1 or 5 methods" % method_pred)


    clusterscore = ClusterClouds(image_with_lags.select(SENTINEL2_BANDNAMES),
                                 img_forecast.select(forecast_bands_sentinel2),
                                region_of_interest=region_of_interest,
                                threshold_dif_cloud=params["threshold_dif_cloud"],
                                do_clustering=params["do_clustering"],
                                threshold_reflectance=params["threshold_reflectance"],
                                numPixels=params["numPixels"],
                                bands_thresholds=params["bands_thresholds"],
                                growing_ratio=params["growing_ratio"],
                                n_clusters=params["n_clusters"])

    # Rename the band name
    clusterscore = clusterscore.select([clusterscore.bandNames().get(0)], ["percentile"+str(method_number)])
    return clusterscore.gte(CUTTOF), img_forecast

