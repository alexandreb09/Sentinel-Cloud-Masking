#####################################################
# Utils file                                        #
# Methods GEE:                                      #
#   - getGeometryImage(image)                       #
#   - get_name_collection(collection)               #
#   - GenerateBandNames(bands, sufix)               #
#   - export_image_to_GEE(image, asset_id, roi,     #
#                         name, num, total)         #
# Methods Python:                                   #
#   - createJSONMetaData(filename, data)            #
#   - updateJSONMetaData(filename, new_data)        #
#   - list_reshape(one_D_list, n)                   #
#   - init_logger()                                 #
#   - date_gap()                                    #
#####################################################

# Modules required
import ee                               # Google Earth Engine API
from subprocess import check_output     # Run windows command from python
import json                             # Export metadata as JSON file
import logging                          # Write
import datetime                         # Handle dates
import os                               # Handle files logging


import ee
import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..'))

import parameters

#############################################
#                   GEE                     #
#############################################


def getGeometryImage(image):
    """ Return the image geometry build from border
    Arguments:
        :param image: GEE Image
        :return: ee.Geometry.Polygon
    """
    return ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint')).coordinates())


def get_name_collection(collection):
    """ Return all the image name in an ee.ImageCollection
    Arguments: 
        :param collection: ee.ImageCollection to process
        :return: GEE list of all image id in the given collection
    """
    def get_name(image):
        """ Return the image id from 1 image
        Argument:
            :param image: 
        """
        return ee.String("COPERNICUS/S2/").cat(ee.Image(image).id())

    return collection.toList(collection.size()).map(get_name)


def GenerateBandNames(bands, sufix):
    """ Concat to each element in bands list the sufix string

    >>> GenerateBandNames(ee.List(["B1","B2"]), "_lag_1").getInfo()
    [u'B1_lag_1', u'B2_lag_1']

    :param bands: ee.List where each Element is a ee.String (GEE object)
    :param sufix: str to concat (Python string)
    :return: list
    :rtype ee.List (GEE)
    """
    bands = ee.List(bands)
    return bands.map(lambda band: ee.String(band).cat(ee.String(sufix)))


def export_image_to_GEE(image, asset_id="users/ab43536/", roi=None,
                        name=None, num=None, total=None):
    """ Export one image to asset
    Arguments:
        :param image: image to export
        :param asset_id="users/ab43536/": 
        :param roi=None: specify the roi, default compute from image dimension
        :type roi: Python List
        :param name=None: name of the image
        :param num=None: optional number for the image (appear on task list in GEE web interface )
        :param total=None: total number of image processing (appear on task list in GEE web interface )
        :return: task        
    NOTE: the ROI must be a Python list.
        For time efficiency, it's better to pass an already defined geometry
        If no geometry is given, the geometry is computed from the given image
        However, since it's the result from lot of process, requesting the geometry
        is ressource consuming (GEE request). As results, that will create an 
        asynchronous request very long (maybe 2 minutes).
        In our work, the geometry doesn't change over the cloud masking process. So it's 
        really faster to pass the geometry of the Sentinel 2 image.

        If "num" and "total" (must have the both) are passed, the description of the 
        task with be: "Image `num` on `total` equal `num/total` pourcent"
    """
    if roi == None:
        roi = getGeometryImage(image)
    if name == None:
        name = image.id().getInfo()
    description = "Default export"
    if num != None and total != None:
        description = "Image {} on {} equal {:05.2f} pourcent".format(
            num, total, num / total * 100)
    # print(description)
    assetId = asset_id + '/' + name
    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toAsset(image=image.clip(roi),
                                         description=description,
                                         assetId=assetId,
                                         scale=30,
                                         region=roi.coordinates().getInfo(),
                                         )
    # Run the task
    task.start()
    return task


#############################################
#                   Python                  #
#############################################


def createJSONMetaData(filename, data):
    """ Export the data in JSON file
    Arguments:
        :param filename: path to output file 
        :param data: data to export
    """
    with open(filename, "w+") as f:
        json.dump(data, f, indent=4)


def updateJSONMetaData(filename, new_data):
    """ Update the filename content according to the new data
    Arguments:
        :param filename: file to update (path) 
        :param new_data: new data
    """
    # Try to open file
    try:
        # read JSON object
        with open(filename, 'r') as f:
            old_data = json.load(f)
    except FileNotFoundError:
        old_data = {}
    # Merge data
    data = {**old_data, **new_data}
    # Save it (overwrite filename)
    createJSONMetaData(filename, data)


def list_reshape(one_D_list, n):
    """ Reshape a 1D list to a 2D list with n elements per sublist
    Arguments:
        :param one_D_list: list to process
        :param n: number elements per sublists
        :return: 2 * n list
    """
    return [one_D_list[i:i+n] for i in range(0, len(one_D_list), n)]


def init_logger(path=parameters.LOG_FILE):
    """ Init the logger
    """
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'a'): pass


    level = logging.INFO
    format = '  %(message)s'
    handlers = [logging.FileHandler(path),
                logging.StreamHandler()]
    
    logging.basicConfig(level=level, format=format, handlers=handlers)


def date_gap(date_start, date_end, nb_days_before=None, nb_days_after=None):
    """ Remove "nb_days_before" days for the "date_start" 
        and add "nb_days_after" for the "date_end"
    Arguments:
        :param date_start: starting date (python string)
        :param date_end: ending date (python string)
        :param nb_days_before: number of days to soustract to date_start
        :param nb_days_after: number of days to add to date_end
        :return: string dates
    """
    if nb_days_before == None:
        nb_days_before = parameters.nb_days_before
    if nb_days_after == None:
        nb_days_after = parameters.nb_days_after

    date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d')
    date_end = datetime.datetime.strptime(date_end, '%Y-%m-%d')

    date_start = date_start - datetime.timedelta(days=nb_days_before)
    date_end = date_end + datetime.timedelta(days=nb_days_after)

    return str(date_start.strftime("%Y-%m-%d")), str(date_end.strftime("%Y-%m-%d"))
