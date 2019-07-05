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



def get_name_collection(collection):
    """ Return all the image name in a list
    Arguments: 
        :param collection: ee.ImageCollection 
    """
    def get_name(image):
        """ Return the image id
        Argument:
            :param image: 
        """
        return ee.String("COPERNICUS/S2/").cat(ee.Image(image).id())
    
    return collection.toList(collection.size()).map(get_name)
