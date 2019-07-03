#################################################
# Methods file for background selection         #
# Methods used from selecting the background    #
#   - getImagesNeightboor(img,                  #
#                         dataset_asc,          #
#                         dataset_desc,         #
#                         number_of_images)     #
#   - method1(sentinel_img,                     #
#             sentinel_collection,              #
#             number_of_images)                 #
#   - method5(sentinel_img,                     #
#             sentinel_collection,              #
#             number_of_images,                 #
#             number_preselect)                 #
#################################################

import ee

def getImagesNeightboor(img, dataset_asc, dataset_desc, number_of_images):
    """
    Select 10 previous images
    If not enough images, select image in futur, starting after the current date image
    docstring here
        :param img: 
        :param dataset_asc: from more recent to older images
        :param dataset_desc: from older to more recent
        :param number_of_images: 
    """
    # Select `number_of_images` previous images
    images = dataset_asc.filter(ee.Filter.lt("system:time_start", img.get("system:time_end"))) \
                        .limit(number_of_images)

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


def method1(sentinel_img, sentinel_collection, number_of_images):
    """
    Filter :
       - "number_of_images" previous images (time neightboor)
       - Select the most cloudy image

    Arguments:
        :param sentinel_img: 
        :param sentinel_collection: 
        :pram number_of_images: nombre d'image à conserver
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                  dataset_date_desc, number_of_images) \
                            .sort("CLOUDY_PIXEL_PERCENTAGE", False) \
                            .limit(number_of_images)
    return imgColl


def method5(sentinel_img, sentinel_collection, number_of_images, number_preselect):
    """
    Filter:
        - `numberPreSelect` previous images
        - `number_of_images` most cloudy

    Arguments:
        :param sentinel_img: 
        :param sentinel_collection: 
        :param number_of_images: 
        :param number_preselect: 
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                  dataset_date_desc, number_preselect) \
                            .sort("CLOUDY_PIXEL_PERCENTAGE") \
                            .limit(number_of_images)
    return imgColl
