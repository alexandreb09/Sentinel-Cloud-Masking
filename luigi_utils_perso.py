import ee


def getImageBoundList(image):
    # Region of interest
    ROI = image.get("system:footprint").getInfo().coordinates
    return ee.Geometry.Polygon(ROI)

def getCenterPointFromImage(image):        
    lineRing = image.getInfo()['properties']['system:footprint']
    center = ee.Array(lineRing.coordinates)
    return center.reduce(ee.Reducer.mean(), [0]).getInfo()['0']
