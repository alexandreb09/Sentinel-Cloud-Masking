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


def mv_list_file_to_imageCollection(verbose=False):
    from subprocess import check_output
    
    ids = [elt["id"] for elt in ee.data.getList({"id": "users/ab43536"})][1:]
    # print(ids)
    if verbose: print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Move started :-)", ""))
    for i, id in enumerate(ids):
        new_id = id[:29] + "/" + id[29:]
        command = "earthengine mv {0} {1}".format(id, new_id)
        check_output(command, shell=True)
        if verbose:
            print("\t- Image: {0}/{1}".format(i+1, len(ids)))
    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Move Finished !", ""))


def export_image(image, asset_id="users/ab43536/", roi=None, name=None, num=None, total=None):
    """ Export one image to asset
    Arguments
        :param image: image to export
        :param roi=None:  specify the roi, default compute from image dimension
        :param name=None: name of the image
    """
    if roi == None: roi = getGeometryImage(image)
    if name == None: name = image.id().getInfo()
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


def add_meta_data_collection(collection_id_source, collection_id_dest):

    def add_meta_data_image(image):
        """ Given an image, update the starting date, end_date and geometry
            according the Sentinel image collection (original collection from GEE)
        Arguments:
            :param image: image to process
        """   
        image = ee.Image(image)
        image_s2 = sentColl.filter(ee.Filter.eq('system:index',
                                                image.get('system:index'))) \
                                .first()
        image = image.set('system:time_end', image_s2.get('system:time_end')) \
                     .set('system:time_start', image_s2.get('system:time_start'))
        return image.clip(image_s2.geometry())
    
    # Reférence dataset 
    sentColl = ee.ImageCollection("COPERNICUS/S2")
    # Collection to process
    maskCollection = ee.ImageCollection(collection_id_source)

    mask_updated = maskCollection.map(add_meta_data_image).limit(3)


    ## EXPORT DATA

    mask_updated_list = mask_updated.toList(mask_updated.size())
    nb_images = mask_updated.size().getInfo()
    if collection_id_dest[-1] != '/': collection_id_dest+= "/"

    # Create folder is not present
    if collection_id_dest[:-1] not in [elt["id"] for elt in ee.data.getList({"id": "users/ab43536"})]:
        ee.data.createAsset({'type': "ImageCollection"}, collection_id_dest[:-1])

    for i in range(nb_images):
        image = ee.Image(mask_updated_list.get(i))

        image_s2 = sentColl.filter(ee.Filter.eq('system:index',
                                                image.get('system:index'))) \
                            .first()

        description = "Image {} on {} equal {:05.2f} percent".format(i+1, nb_images, (i+1) / nb_images * 100)
        task = ee.batch.Export.image.toAsset(image=image.clipToBoundsAndScale(image_s2.geometry()),
                                             description=description,
                                             assetId=collection_id_dest + image_s2.id().getInfo(),
                                             scale=30,
                                             region=getGeometryImage(image_s2).coordinates().getInfo(),
                                             )
        task.start()
        print("\t- Image {}/{} e.g {:05.2f}%".format(i + 1, nb_images, (i+1) / nb_images * 100))



