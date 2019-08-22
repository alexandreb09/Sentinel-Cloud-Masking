######################################################################
#                           LOAD DATASET                             #
#  These functions are looking at the mask available in GEE          #
#  and return the matching mask or sentinel images                   #
######################################################################

import ee

def build_sentinel_dataset(maskCollection, sentinel_coll_name):
    """ Build sentinel data collection where mask in
        "maskCollection" is available
        Apply the mask to sentinel images
        Add the mask to sentinel images
    Arguments:
        :param maskCollection: 
        :param sentinel_coll_name: 
    """
    # Return one image from a given name
    def add_sent_image(mask, list):
        sent = ee.ImageCollection(sentinel_coll_name)   \
            .filter(ee.Filter.eq('system:index', mask.get('system:index'))) \
            .first()    \
            .addBands(mask.rename("mask"))  \
            .updateMask(mask)
        return ee.List(list).add(sent)

    # Get all names from the mask collection
    sentinel_collection = maskCollection.iterate(
        add_sent_image,
        [])

    # Return the image set as ImageCollection
    return ee.ImageCollection.fromImages(sentinel_collection)


def loadMaskCollection(name, sentinel_name, roi=None, date_start=None, date_end=None):
    """ Retrieve the correct maskCollection with updated metadata 
    from sentinel collection
    Arguments:
        :param name: collection name (string)
        :param sentinel_name: sentinel collection
        :param roi: area of interest 
        :param date_start: first image date
        :param date_end: last image date
        :return: List of all masks
        :return type: ee.ImageCollection()
    """
    def setMetaData(mask, sentinel_img):
        # Inverse binary mask
        mask = ee.Image(mask).Not()

        meta = ee.Dictionary({
            'system:footprint': sentinel_img.geometry(),
            'system:time_start': sentinel_img.get('system:time_start'),
            'system:time_end': sentinel_img.get('system:time_end'),
        })
        return mask.set(meta)

    def filter_existing_images(mask, list_):
        mask = ee.Image(mask)
        sentinel_img = ee.ImageCollection(sentinel_name)    \
            .filter(ee.Filter.eq('system:index',
                                 mask.get('system:index')))
        list_ = ee.List(ee.Algorithms.If(sentinel_img.size().eq(0),
                                         list_,
                                         ee.List(list_).add(setMetaData(mask, sentinel_img.first()))))
        return list_

    # Load mask and sentinel image collection
    coll = ee.ImageCollection(name)

    # Filter and update metadata
    coll = ee.ImageCollection.fromImages(
        coll.iterate(filter_existing_images, []))

    # coll = coll.map(setMetaData(sentinel));
    # If roi defined: filter
    if (roi):
        coll = coll.filterBounds(roi)

    # If date range defined: filter
    if (date_start and date_end):
        coll = coll.filterDate(date_start, date_end)

    return coll
