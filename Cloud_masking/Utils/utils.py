#####################################################
# Utils file                                        #
# Methods:                                          #
#   - getGeometryImage(image)                       #
#####################################################

# Modules required
import ee                       # Google Earth Engine API

def getGeometryImage(image):
    """ Return the image geometry build from border
    Arguments:
        :param image: GEE Image
        :return: ee.Geometry.Polygon
    """
    return ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint')).coordinates())
