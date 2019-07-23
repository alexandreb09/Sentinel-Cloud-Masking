#####################################################
# Utils file for TASKS management                   #
# Currently working on ...                          #
# Methods:                                          #
#   -                                               #
#####################################################

# Modules required
from subprocess import check_output     # Run windows command from python
import re                               # Regex
import ee                               # GEE module
import time

# Others functions
import utils



def getNumberActiveTask():
    """ Return the number of task RUNNING + READY 
        The sum must be bellow 3000 (GEE restriction)
    """
    cmd_out = check_output("earthengine task list", shell=True)  \
                        .decode("utf-8")  
    return cmd_out.count('READY') + cmd_out.count('RUNNING')


def getTaskList(verbose=False):
    """ Return all the current task RUNNING or READY
    Arguments
        :param verbose=False: 
    """
    cmd_out = check_output("earthengine task list", shell=True)  \
                        .decode("utf-8")
    tasks_list = cmd_out.replace('\n', '') \
                        .replace('\r', '') \
                        .split("---")

    tasks = []
    keys = ["id_task", "Operation", "Description", "Status"]

    for task in tasks_list:
        values = re.split(r'\s{2,}', task)[:-1]
        if len(values) == 4 and (values[3] == "READY" or values[3] == "RUNNING"):
            tasks.append({k: v for k, v in zip(keys, values) if k != ""})

    # tasks.pop('', None)
    if verbose:
        print(tasks)
        print("READY task:", cmd_out.count('READY'))
        print("RUNNING task:", cmd_out.count('RUNNING'))
    return tasks


def cancelAllTask(verbose=False):
    """ Cancel all the active task (READY and RUNNING)
        The commann seems to fail if more than 32 arguments (task_id) are given at the same time
    """
    # Max argument number given to one command
    nb_max = 32
    
    task_list = getTaskList(verbose=False)
    total = len(task_list)
    counter = 0

    # Reshape as 2d list
    task_list = [task_list[i:i + nb_max] for i in range(0, len(task_list), nb_max)]
    
    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("",
                                                    "Task cancellation started", ""))

    for task_subset in task_list:
        list_id = [task["id_task"] for task in task_subset]
        command = "earthengine task cancel {}".format(list_id)
        command = command.replace(",", "").replace("[", "").replace("]", "").replace("'", "")
        check_output(command, shell=True)

        if verbose:
            counter += len(task_subset)
            print("Tasks cancelled: {:4d}/{} = {:05.2f}%".format(counter, total,
                                                        counter / total * 100))

    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("",
                                                    "Task cancellation finished !", ""))


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
    return list_images


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
    if name == None: name = image.id().getInfo()

    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toDrive(image=image,
                                         description=name.split("/")[-1],
                                         scale=30,
                                         region=roi,
                                         driveFolder=folder
                                         )
    task.start()


def exportImageListToDrive(image_to_run, drive_folder_name="default_drive_folder_name"):
    """ Export a list of image to google drive
    Arguments:
        :param image_to_run: List a image image id to export
                            Use 'getAllImagesInColl' to get all image id from a directory
        :type image_to_run: List[string, ...] (python)
        :param drive_folder_name="default_drive_folder_name": 
    """
    
    # Maximum number of task running at the same time
    # Limited to 3000 concurent tasks by GEE
    nb_task_max = 100

    total = len(image_to_run)
    counter = 0
    print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Export to drive started", ""))
   
    while len(image_to_run) > 0:
        nb_task_pending = getNumberActiveTask()
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
                utils.updateJSONMetaData("Metadata_mask.json", meta_data)

                print("{:4d}/{} = {:05.2f}%   Image {}".format(counter,
                                                            total,
                                                            counter / total * 100, image_name))
                counter += 1

        # Use quit a long time (30s) since there is lag between the moment the task is launched 
        # (in Python) and the time it really starts on GEE
        time.sleep(30)
    
    print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Export to drive finished !", ""))


# ee.Initialize()

# list_image = getAllImagesInColl('users/ab43536/masks_4_methods')
# exportImageListToDrive(list_image, "Mask_UK_2018")
