#####################################################
# Utils file for ASSETS management                  #
#                                                   #
# Methods:                                          #
#       - getAllImagesInColl(path)                  #
#       - delete_assets(list_assets, silent)        #
#       - move_list_file(source, dest, verbose)     #
#####################################################


from subprocess import check_output     # Run windows command from python
import ee                               # GEE
import time

# Others functions
import utils
import utils_tasks

def getAllImagesInColl(path):
    """ Return all the image in the directory
    Arguments:
        :param path: folder GEE path (python string)
        :return: python list with all image path in the folder
    """
    list_images = check_output("earthengine ls {}".format(path), shell=True) \
                                .decode("utf-8") \
                                .replace("\r", "") \
                                .split("\n")[:-1]
    if not list_images or "No such folder or collection:" in list_images[0]:
        raise ValueError(list_images[0] + " Check the correct path.")
    return list_images

def delete_assets(list_assets, silent=False):
    """ Delete all the image passed
    Arguments:
        :param list_assets: list of image path (GEE). 
                        Ex: ["users/ab43536/folder/imageId", ...]
        :param silent=False: Run in silent mode
    """
    total = len(list_assets)
    counter = 0

    list_assets = utils.list_reshape(list_assets, 20)
    if not silent:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Deletion started :-)", ""))
    
    for sublist_assets in list_assets:
        command = "earthengine rm {0}".format(' '.join(sublist_assets))
        check_output(command, shell=True)
        for img in sublist_assets:
            if not silent:
                print("\t- Image: {0}/{1}   {2}".format(counter + 1,
                                                        total, img))
            counter += 1
    if not silent:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Deletion Finished !", ""))



def move_list_file(source, dest, verbose=False):
    """ Move a list of files from source to dest
        Do not care if there is folder or not
    Arguments
        :param source: source folder
        :param dest: destination folder
        :param verbose=False: 
    """
    if verbose: print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Move started :-)", ""))
    
    ids = [elt["id"] for elt in ee.data.getList({"id": source})][1:]

    for i, id in enumerate(ids):
        new_id = dest + '/' + id.split('/')[-1]
        command = "earthengine mv {0} {1}".format(id, new_id)
        check_output(command, shell=True)
        if verbose:
            print("\t- Image: {0}/{1}".format(i+1, len(ids)))
    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Move Finished !", ""))


def getMetaDataImage(image):
    """ Retrive the geometry - time_start - time_end from the image
    Arguments:
        :param image: image to collect metadata
        :return: Python dict
    """
    # cast to GEE image (safety)
    image = ee.Image(image)
    # Collect image data
    sub_dict = ee.Dictionary({
        "geometry": image.geometry().coordinates().get(0),
        "date_deb": image.get("system:time_start"),
        "date_end": image.get("system:time_end")
    })
    # Return python object
    return sub_dict.getInfo()


def addMetaDataImage(mask):
    """ Add image geometry, time_start and time_end to the given image
        Use the Sentinel Collection to find matching image
    Arguments:
        :param mask: image to add metadata 
    """
    # Cast to image (safety)
    mask = ee.Image(mask)
    # Find matching sentinel image (with same id)
    sentinel_img = ee.ImageCollection("COPERNICUS/S2")  \
                        .filter(ee.Filter.eq('system:index',
                                            mask.get('system:index')))  \
                        .first()
    # Collection metadata from sentinel image
    meta = ee.Dictionary({
        'system:footprint': sentinel_img.geometry(),
        'system:time_start': sentinel_img.get('system:time_start'),
        'system:time_end': sentinel_img.get('system:time_end'),
    })
    # Set metadata to the image
    return mask.set(meta)


def export_image_to_drive(image, roi=None, name=None, folder="default_drive_folder_name"):
    """ Export one image to Google Drive
    Arguments
        :param image: image to export
        :param roi=None: specify the roi (as python list),
                         Default: compute from image dimension
        :param name=None: name of the image
    """
    if roi == None:
        roi = utils.getGeometryImage(image).coordinates().getInfo()
    if name == None:
        name = image.id().getInfo()

    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toDrive(image=image,
                                         description=name.split("/")[-1],
                                         scale=30,
                                         region=roi,
                                         driveFolder=folder
                                         )
    task.start()


def exportImageListToDrive(image_to_run, output_json="Metadata_mask.json", drive_folder_name="default_drive_folder_name"):
    """ Export a list of image to google drive
    Arguments:
        :param image_to_run: List a image image id to export
                            Use 'getAllImagesInColl' to get all image id from a directory
        :type image_to_run: List[string, ...] (python)
        :param output_json="Metadata_mask.json": path to output json file (storing metadata)
        :param drive_folder_name="default_drive_folder_name": 
    """

    # Maximum number of task running at the same time
    # Limited to 3000 concurent tasks by GEE
    nb_task_max = 100

    total = len(image_to_run)
    counter = 0
    print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Export to drive started", ""))

    while len(image_to_run) > 0:
        nb_task_pending = utils_tasks.getNumberActiveTask()
        if nb_task_pending < nb_task_max:
            new_images = nb_task_max - nb_task_pending

            # Select the n first images
            image_running = image_to_run[:new_images]
            # Remove them from image to run
            image_to_run = image_to_run[new_images:]

            # Export image in image_to_run
            for image_name in image_running:
                image = ee.Image(image_name)
                image = addMetaDataImage(image)

                meta_data = {image_name: getMetaDataImage(image)}
                # Export image
                export_image_to_drive(
                    image, name=image_name, folder=drive_folder_name)
                utils.updateJSONMetaData(output_json, meta_data)

                print("{:4d}/{} = {:05.2f}%   Image {}".format(counter,
                                                               total,
                                                               counter / total * 100, image_name))
                counter += 1

        # Use quit a long time (30s) since there is lag between the moment the task is launched
        # (in Python) and the time it really starts on GEE
        time.sleep(30)

    print("{:-<100}\n|{:^98}|\n{:-<100}".format("",
                                                "Export to drive finished !", ""))




