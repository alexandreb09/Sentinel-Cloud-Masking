import subprocess
import ee
from Methods_cloud_masking.perso_method_background import *


def getImageBoundList(image):
    # Region of interest
    ROI = image.get("system:footprint").getInfo().coordinates
    return ee.Geometry.Polygon(ROI)


def getCenterPointFromImage(image):
    lineRing = image.getInfo()['properties']['system:footprint']
    center = ee.Array(lineRing.coordinates)
    return center.reduce(ee.Reducer.mean(), [0]).getInfo()['0']


def callback_function_bg(numMethod, sentinel_img, sentinel_collection, number_of_images, threshold_cc, number_preselect,
                         region_of_interest):
    """
    Select the method to call, equivalent as a switch case
    Give the appropriate parameters

    Arguments:
        :param numMethod: method number to call
        :param sentinel_img: 
        :param sentinel_collection: 
        :param number_of_images: 
        :param threshold_cc: 
        :param number_preselect: 
        :param region_of_interest: 
    """
    switcher_method = {
        1: method1,
        2: method2,
        3: method3,
        4: method4,
        5: method5,
        6: method6,
        7: method7,
        8: method8,
    }
    switcher_param = {
        1: [sentinel_img, sentinel_collection, number_of_images],
        2: [sentinel_img, sentinel_collection, number_of_images, threshold_cc],
        3: [sentinel_collection, number_of_images],
        4: [sentinel_img, sentinel_collection, number_of_images, number_preselect],
        5: [sentinel_img, sentinel_collection, number_of_images, number_preselect],
        6: [sentinel_img, sentinel_collection, number_of_images, threshold_cc, region_of_interest],
        7: [sentinel_img, sentinel_collection, number_of_images, threshold_cc, region_of_interest],
        8: [sentinel_img, sentinel_collection, number_of_images, threshold_cc, region_of_interest],
    }

    # Get the function from switcher dictionary
    func = switcher_method.get(numMethod)
    params = switcher_param.get(numMethod)
    # Execute the function
    return func(*params)


def cleanScreen():
    """
    Clear terminal screen on Windows
    """
    subprocess.Popen("cls", shell=True).communicate()


def getGeometryImage(image):
    """ Return the ee.Geometry.Polygon of image border
    Arguments:
        :param image: 
    """
    return ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint') ).coordinates() )


def getIdImageInImageCollection(imgColl):
    """
    Get the id of all images in the image Collection
        :param imgColl: ee.ImageCollection to iterrate
        :return: python list of all the image ids
    """
    list_images_id = ee.List([])
    def getListId(item, list_images_id):
        try:
            return ee.List(list_images_id).add(ee.Image(item).id())
        except ee.ee_exception.EEException as e:
            print("ici")
    
    id_list = imgColl.iterate(getListId, list_images_id)
    return id_list.getInfo()


def print_image_GEE_code(liste):
    print('-' * 10)
    for i, l in enumerate(liste):
        print(
            'Map.addLayer(ee.Image("COPERNICUS/S2/' + l[2:] \
            + '"), imageVisParam, "img' + str(i) + '");')

def print_list_to_imageCollection(liste, delta=2):
    print("ee.ImageCollection([")
    for l in liste:
        print(
            'ee.Image("COPERNICUS/S2/' + l[delta:] + '"),')
    print(']);')


def export_as_asset(image, region_of_interest, description='background-export',
                    scale=30, assetId='users/ab43536/background'):
    """
    Export image to GEE assets
    Arguments:
        :param image: 
        :param region_of_interest: 
        :param description='background-export': 
        :param scale=30: 
        :param assetId='users/ab43536/background': 
    """               
    ee.batch.Export.image.toAsset(
        image=image,
        description=description,
        scale=scale,
        assetId=assetId,
        region=region_of_interest.coordinates().getInfo(),
    ).start()
    print("Brillant ! Exportation has started !")
    