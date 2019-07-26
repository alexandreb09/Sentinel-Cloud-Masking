#####################################################
# Utils file                                        #
# Methods:                                          #
#   - getGeometryImage(image)                       #
#   - get_name_collection(collection)               #
#   - createJSONMetaData(filename, data)            #
#   - updateJSONMetaData(filename, new_data)        #
#   - list_reshape(one_D_list, n)                   #
#   - GenerateBandNames(bands, sufix)               #
#####################################################

# Modules required
import ee                               # Google Earth Engine API
from subprocess import check_output     # Run windows command from python
import json                             # Export metadata as JSON file
import logging                          # Write

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



def export_image_to_GEE(image, asset_id="users/ab43536/", roi=None, name=None, num=None, total=None):
    """ Export one image to asset
    Arguments
        :param image: image to export
        :param roi=None:  specify the roi, default compute from image dimension
        :param name=None: name of the image
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
    task.start()

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
    """ Reshape a 1D list to a 2D list n elements per sublist
    Arguments:
        :param one_D_list: list to process
        :param n: number elements per sublists
    """
    return [one_D_list[i:i+n] for i in range(0, len(one_D_list), n)]



def init_logger():
    level = logging.INFO
    format = '  %(message)s'
    handlers = [logging.FileHandler(parameters.LOG_FILE), logging.StreamHandler()]

    logging.basicConfig(level=level, format=format, handlers=handlers)


