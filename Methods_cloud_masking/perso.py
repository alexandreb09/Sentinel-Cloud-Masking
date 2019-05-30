"""
    Fonctions implementing background images
"""

##########################################
#              Functions                 #
##########################################
from Methods_cloud_masking.perso_parameters import *
from Methods_cloud_masking.perso_luigi_utils import callback_function_bg
import ee



def add_ndvi_bands(image):
    return image.addBands(image.normalizedDifference([NIR, RED]))


def add_evi_bands(image):
    # Formula : 2.5 * (NIR - RED) / ((NIR + 6*RED - 7.5*BLUE) + 1)
    L = 1
    C1 = 6
    C2 = 7.5
    red = image.select(RED)
    blue = image.select(BLUE)
    nir = image.select(NIR)
    numerateur = nir.subtract(red)
    denominateur = nir.add(red.multiply(C1)).subtract(blue.multiply(C2)).add(L)
    evi = numerateur.divide(denominateur).multiply(2.5)
    return image.addBands(evi)


def rename_bands_ft(image):
    # Rename the bands: 4 -> NDVI ; 5 -> EVI
    old_bands = image.bandNames()
    new_bands = old_bands.set(4, 'NDVI').set(5, "EVI")
    return image.select(old_bands, new_bands)

def ComputeCloudCoverGeomSentinel(img, region_of_interest):
    """Compute mean cloud cover and add it as property to the image"""
    # Undefined for sentinel !
    # clouds = ee.Algorithms.Landsat.simpleCloudScore(img).gte(50)

    # clouds= img

    # clouds_original = image_predict_clouds.select("fmask").eq(2)
    # clouds_original = clouds_original.where(image_predict_clouds.select("fmask").eq(4),2)

    # Add growing to the mask

    # clouds = clouds_original.reduceNeighborhood(ee.Reducer.max(),
    #                                            ee.Kernel.circle(radius=3))
    # clouds = ee.Algorithms.Landsat.simpleCloudScore(img).select("cloud").gt(50).toFloat()

    # dictio = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
    #                             bestEffort=True)
    # numerito = ee.Number(dictio.get("CLOUDY_PIXEL_PERCENTAGE")) #.multiply(100)
    img = img.set("CC", img.get('CLOUDY_PIXEL_PERCENTAGE'))
    return img

def filter_partial_tiles(images_background, image, region_of_interest):

    def set_area_roi(image):
        image = ee.Image(image)
        pol = ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint') ).coordinates() )
        ratio = pol.intersection(region_of_interest).area() \
                            .divide(region_of_interest.area())
        return image.set({"common_area": ratio})

    # Add nb of pixels in area of interest
    images_background = images_background.map(set_area_roi)

    return images_background.filter(ee.Filter.gt("common_area", 0.99))



def PreviousImagesWithCCSentinel(methodNumber, sentinel_img, number_of_images, threshold_cc,
                                 number_preselect, region_of_interest, include_img=False):
    """
    Return the NUMBER_IMAGES previous images with cloud cover
         
    Arguments
        :param methodNumber: 
        :param sentinel_img: 
        :param number_of_images: 
        :param threshold_cc: 
        :param number_preselect: 
        :param region_of_interest: 
    """

    # Get collection id
    sentinel_info = sentinel_img.getInfo()                                  # Sentinel infos
    sentinel_full_id = sentinel_info['id']                                  # full image ID
    image_index = sentinel_info['properties']['system:index']               # Image index
    sentinel_collection = sentinel_full_id.replace("/" + image_index, "")   # Sentinel collection (base for background)
    MGRS_TILE = sentinel_info['properties']['MGRS_TILE']                    # Tile the image analyzed

    # Retrieve previous images
    # Filter per area
    if region_of_interest is None:
        region_of_interest = ee.Element.geometry(sentinel_img)
        sentinel_collection = ee.ImageCollection(sentinel_collection) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))
    else:
        sentinel_collection = ee.ImageCollection(sentinel_collection) \
            .filterBounds(region_of_interest) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))

    # Remove image of same date
    time_start = sentinel_info["properties"]['system:time_start']
    filter_before = ee.Filter.lt('system:time_start', int(time_start) - 18 * 3600000)
    filter_after =  ee.Filter.gt('system:time_start', int(time_start) + 18 * 3600000)
    sentinel_collection = sentinel_collection.filter(ee.Filter.Or(filter_before, filter_after))

    # Remove partial tiles images
    sentinel_collection = filter_partial_tiles(sentinel_collection, sentinel_img, region_of_interest)

    # Background selection according to the method number
    imgColl = callback_function_bg(methodNumber, sentinel_img, sentinel_collection, \
                                   number_of_images, threshold_cc, number_preselect, \
                                   region_of_interest)

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

    imgColl = imgColl.map(_count_valid).sort("valids").limit(number_of_images)

    # from Methods_cloud_masking.perso_luigi_utils import print_image_GEE_code
    # from Methods_cloud_masking.perso_luigi_utils import getIdImageInImageCollection
    # from Methods_cloud_masking.perso_luigi_utils import print_list_to_imageCollection
    # print_list_to_imageCollection(getIdImageInImageCollection(imgColl), 0)

    return imgColl


def PredictPercentile(method_number, img, region_of_interest, number_of_images,
                      number_preselect, threshold_cc):
    """
    Add a percentile band after PreviousImagesWithCCSentinel call
    Arguments : 
        :param method_number: 
        :param img: 
        :param region_of_interest: 
        :param number_of_images:
        :param number_preselect: 
        :param threshold_cc: 
    """
    imgColl = PreviousImagesWithCCSentinel(method_number, img, number_of_images,
                                            threshold_cc, number_preselect,
                                            region_of_interest, include_img=False,
                                            )
    # from Methods_cloud_masking.perso_luigi_utils import print_image_GEE_code, \
    #                                                     getIdImageInImageCollection, \
    #                                                     print_list_to_imageCollection
    # print_image_GEE_code(getIdImageInImageCollection(imgColl))
    # print_list_to_imageCollection(getIdImageInImageCollection(imgColl), delta=0)

    img_percentile = imgColl.reduce(reducer = ee.Reducer.percentile(percentiles = [50]))
    return img_percentile




####################################
# GEE Cloud Mask                   #
####################################
def getMaskGEE(image):
    qa = image.select('QA60')

    cloudBitMask = 1 << 10              # Bit 10 is cloud
    cirrusBitMask = 1 << 11             # Bit 11 is cirrus

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

    return mask.Not()



"""
def exportToDrive(image):
    params = {
        'fileNamePrefix':'imageRGB',
        'folder':'datasetTestAberdeen',
        'image':image, # cast bands
        'description': 'description imageRGB',
        'scale': 30,
        'maxPixels':1e13
    }
    print("Début exportation ...")
    task = ee.batch.Export.image.toDrive(**params)
    # Import module for batch !
    # batch.Task.start(task)
    print("Exportation terminée :-)")
"""
