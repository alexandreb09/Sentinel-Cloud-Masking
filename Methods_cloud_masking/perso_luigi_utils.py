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
    pol = image.get('system:footprint').getInfo()['coordinates']
    return ee.Geometry.Polygon(pol)


# Minimize the dimension of the image
# def getBarycentre(ll):
#     centre = [0, 0]
#     for pt in ll:
#         centre[0] += pt[0]
#         centre[1] += pt[1]
#     return centre[0] / len(ll), centre[1] / len(ll)
    
# def signof(x):
#     return (1, -1)[x < 0]

# def resizeRegion(list_points, alpha=1 / 1000):
#     bx, by = getBarycentre(list_points)
#     new_list = []
#     for pt in list_points:
#         pX = pt[0] + signof(bx - pt[0])* alpha
#         pY = pt[1] + signof(by - pt[1])* alpha
#         new_list.append([pX, pY])
#     return new_list