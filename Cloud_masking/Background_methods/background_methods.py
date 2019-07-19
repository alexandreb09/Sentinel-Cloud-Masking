#################################################
# Methods file for background selection         #
# Methods used from selecting the background    #
#   - getImagesNeightboor(img,                  #
#                         dataset_asc,          #
#                         dataset_desc,         #
#                         number_of_images)     #
#   - method1(sentinel_img,                     #
#             number_of_images,                 #
#             dataset_date_asc,                 #
#             dataset_date_desc)                #
#   - method5(sentinel_img,                     #
#             number_of_images,                 #
#             number_preselect,                 #
#             dataset_date_asc,                 #
#             dataset_date_desc)                #
#################################################

# Import module
import ee

# Import parameters from "parameters.py"
import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..'))
from parameters import *

def getImagesNeightboor(img, dataset_asc, dataset_desc, number_of_images):                      
    """
    Select "number_of_images" previous images
    Arguments:
        :param img: 
        :param dataset_asc: dataset background candidates from more recent to older images
        :param dataset_desc: dataset background candidates from older to more recent
        :param number_of_images: number of images to select
    """
    # Select `number_of_images` previous images
    images = dataset_asc.filter(ee.Filter.lt("system:time_start",
                                             img.get("system:time_end"))) \
                        .limit(number_of_images)

    # Allow selecting image in futur (when there are no enough images in past)
    if PARAMS_SELECTBACKGROUND_DEFAULT['allow_future']:
        # If less than `number_of_images` images selected
        size = images.size()
        if size.lt(number_of_images):
            # calc number to add
            nbImagesToAdd = ee.Number(number_of_images).subtract(size)
            # print("Nombre images ajoutées après: ", nbImagesToAdd)
            # Add the next `number_of_images` images
            imagesAfter = dataset_desc.filter(ee.Filter.gt("system:time_start",
                                                        img.get("system:time_end"))) \
                                       .limit(nbImagesToAdd)
            # Merge of both collections
            images = images.merge(imagesAfter)
    return images


def method1(sentinel_img, number_of_images,
            dataset_date_asc, dataset_date_desc):  
    """
    Filter :
       - "number_of_images" previous images (time neightboor)
       - Select the most cloudy image

    Arguments:
        :param sentinel_img: image analysed
        :param number_of_images: number of images used in background
        :param dataset_date_asc: dataset background candidates from more recent to older images
        :param dataset_date_desc: dataset background candidates from older to more recent
    """

    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                  dataset_date_desc, number_of_images) \
                            .sort("CLOUDY_PIXEL_PERCENTAGE", False) \
                            .limit(number_of_images)
    return imgColl


def method5(sentinel_img, number_of_images, number_preselect,
            dataset_date_asc, dataset_date_desc):
    """
    Filter:
        - `numberPreSelect` previous images
        - `number_of_images` most cloudy

    Arguments:
        :param sentinel_img: image analysed
        :param number_of_images: number of images used in background
        :param number_preselect: number of images pre filter background
        :param dataset_date_asc: dataset background candidates from more recent to older images
        :param dataset_date_desc: dataset background candidates from older to more recent
    """
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                  dataset_date_desc, number_preselect) \
                            .sort("CLOUDY_PIXEL_PERCENTAGE") \
                            .limit(number_of_images)
    return imgColl