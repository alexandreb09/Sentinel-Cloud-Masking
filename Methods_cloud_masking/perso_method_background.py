import ee
from Methods_cloud_masking.perso_tree import getMaskTree1, getMaskTree2, getMaskTree3

#########################################
# Set of methods used to find images    #
# for building background               #
#########################################

#########################################
# LE TRI DU JEU DE DONNEE COMPLET PEUT ETRE FACTORISE ...
#########################################


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
       - 20 previous images

    Arguments:
        :param sentinel_img: 
        :param sentinel_collection: 
        :pram number_of_images: nombre d'image à conserver
    """
    # Peut être factorisé !!
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                  dataset_date_desc, number_of_images) \
                                .sort("CLOUDY_PIXEL_PERCENTAGE", False)
    return imgColl


def method2(sentinel_img, sentinel_collection, number_of_images, threshold_cc):
    """
    Filter :
        - CC < 10%
        - 20 previous images
    Arguments:
        :param sentinel_img: 
        :param sentinel_collection: 
        :param number_of_images: 
        :param threshold_cc: 
    """
    sentinel_collection = sentinel_collection.filter(ee.Filter.gt("CLOUDY_PIXEL_PERCENTAGE", threshold_cc))

    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                        dataset_date_desc, number_of_images) \
                                        .sort("CLOUDY_PIXEL_PERCENTAGE", False)

    return imgColl


def method3(sentinel_collection, number_of_images):
    """
    Filter CC : the `x` least cloud images over all the dataset

    Arguments: 
        :param sentinel_collection: 
        :param number_of_images: 
    """
    imgColl = sentinel_collection.sort("CLOUDY_PIXEL_PERCENTAGE", False).limit(number_of_images)
    return imgColl


def method4(sentinel_img, sentinel_collection, number_of_images, number_preselect):
    """
    Filter:
        - `numberPreSelect` previous images
        - `number_of_images` least cloudy

    Arguments:
        :param sentinel_img: 
        :param sentinel_collection: 
        :param number_of_images: 
        :param number_preselect: 
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                    dataset_date_desc, number_preselect)
    imgColl = imgColl.sort("CLOUDY_PIXEL_PERCENTAGE", False).limit(number_of_images)
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
                                    dataset_date_desc, number_preselect)
    imgColl = imgColl.sort("CLOUDY_PIXEL_PERCENTAGE").limit(number_of_images)
    return imgColl


def method6(image, sentinel_collection, number_of_images, threshold_cc, region_of_interest):
    """
    Compute mean cloud cover and add it as property to the image
        - Use tree method 1
    Filter : take the `number_of_images` least cloudy

    Arguments:
        :param image:
        :param sentinel_collection:
        :param number_of_images:
        :param threshold_cc:
        :param region_of_interest:
    """

    def compute_CC_M1(image):
        """
        Compute Cloud Cover estimation based on method tree 1
        """
        clouds = getMaskTree1(image)
        dictio = clouds.reduceRegion(reducer=ee.Reducer.mean(),
                                     geometry=region_of_interest,
                                     scale=30,
                                     bestEffort=True)
        numerito = ee.Number(dictio.get("constant")).multiply(100)
        image = image.set("CC", numerito)
        return image

    imgColl = sentinel_collection.map(compute_CC_M1).sort("CC")
    imgColl = imgColl.sort("CC").limit(number_of_images)
    return imgColl


def method7(image, sentinel_collection, number_of_images, threshold_cc, region_of_interest):
    """
    Compute mean cloud cover and add it as property to the image
        - Use tree method 2
    Filter : take the `number_of_images` least cloudy

    Arguments:
        :param image:
        :param sentinel_collection:
        :param number_of_images:
        :param threshold_cc:
        :param region_of_interest:
    """

    def compute_CC_M2(image):
        """
        Compute Cloud Cover estimation based on method tree 2
        """
        clouds = getMaskTree2(image)
        dictio = clouds.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
                                     bestEffort=True)
        numerito = ee.Number(dictio.get("cloud")).multiply(100)
        image = image.set("CC", numerito)
        return image

    imgColl = sentinel_collection.map(compute_CC_M2).sort("CC")
    imgColl = imgColl.sort("CC").limit(number_of_images)
    return imgColl


def method8(image, sentinel_collection, number_of_images, threshold_cc, region_of_interest):
    """
    Compute mean cloud cover and add it as property to the image
        - Use tree method 3
    Filter : take the `number_of_images` least cloudy

    Arguments:
        :param image:
        :param sentinel_collection:
        :param number_of_images:
        :param threshold_cc:
        :param region_of_interest:
    """

    def compute_CC_M3(image):
        """
        Compute Cloud Cover estimation based on method tree 3
        """
        clouds = getMaskTree3(image)
        dictio = clouds.reduceRegion(reducer=ee.Reducer.mean(),
                                     geometry=region_of_interest,
                                     bestEffort=True)
        numerito = ee.Number(dictio.get("cloud")).multiply(100)
        image = image.set("CC", numerito)
        return image

    imgColl = sentinel_collection.map(compute_CC_M3).sort("CC")
    imgColl = imgColl.sort("CC").limit(number_of_images)
    return imgColl

