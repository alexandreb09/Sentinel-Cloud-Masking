#####################################################
# Utils file - background methods                   #
# Methods:                                          #
#   - GenerateBandNames(bands, sufix)               #
#   - filter_partial_tiles(images_background,       #
#                          image,                   #
#                          region_of_interest)      #
#####################################################

# Modules required
import ee                       # Google Earth Engine API

# Load parameters
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..'))
from parameters import COMMON_AREA

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


def filter_partial_tiles(images_background, image, region_of_interest):
    """ Remove image with different shapes (should share at least COMMON_AREA % common)
    Arguments:
        :param images_background: 
        :param image: 
        :param region_of_interest: 
    """
    def set_area_roi(image):
        image = ee.Image(image)
        pol = ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint')).coordinates())
        ratio = pol.intersection(region_of_interest).area() \
                    .divide(region_of_interest.area())
        return image.set({"common_area": ratio})

    # Add nb of pixels in area of interest
    images_background = images_background.map(set_area_roi)

    return images_background.filter(ee.Filter.gt("common_area", COMMON_AREA))
