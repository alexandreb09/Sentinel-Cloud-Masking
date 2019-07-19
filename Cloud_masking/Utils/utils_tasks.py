#####################################################
# Utils file for TASKS management                   #
# Currently working on ...                          #
#  Methods:                                         #
#   -                                               #
#####################################################

# Modules required
from subprocess import check_output     # Run windows command from python
import re                               # Regex
import ee                               # GEE module
import json                             # Export metadata as JSON file
import time

# Others functions
from utils import getGeometryImage

#################################
# Manage GEE Tasks              #
#################################

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
    """
    list_images = check_output("earthengine ls {}".format(path), shell=True) \
                                .decode("utf-8") \
                                .replace("\r", "") \
                                .split("\n")[:-1]
    return list_images

def getMetaDataImage(image):
    image = ee.Image(image)
    sub_dict = ee.Dictionary({
        "geometry": image.geometry().coordinates().get(0),
        "date_deb": image.get("system:time_start"),
        "date_end": image.get("system:time_end")
    })
    return sub_dict.getInfo()

def getMetaDataListImage(list_image_name):
    """ Return the metadata for a given list of image names
    Argument:
        :param list_image_name: list of image name (can be used as output of "getAllImagesInColl")
    """

    def getMetaDataImage(elt, dict_):
        elt = ee.List(elt)
        image = ee.Image(elt.get(0))
        sub_dict = ee.Dictionary({
            "geometry": image.geometry().coordinates().get(0),
            "date_deb": image.get("system:time_start"),
            "date_end": image.get("system:time_end"),
        })
        return ee.Dictionary(dict_).set(elt.get(1), sub_dict)
    
    image_col = ee.List([eval("[ee.Image('{0}'), '{0}']".format(name)) for name in list_image_name])

    return image_col.iterate(getMetaDataImage, {}) #.getInfo()

def addMetaDataImage(mask):
    mask = ee.Image(mask)
    sentinel_img = ee.ImageCollection("COPERNICUS/S2")  \
                                .filter(ee.Filter.eq('system:index',
                                        mask.get('system:index')))  \
                                .first()
    meta = ee.Dictionary({
        'system:footprint': sentinel_img.geometry(),
        'system:time_start': sentinel_img.get('system:time_start'),
        'system:time_end': sentinel_img.get('system:time_end'),
    })
    return mask.set(meta)

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
    except FileNotFoundError: old_data = {}
    # Merge data
    data = {**old_data, **new_data}
    # Save it (overwrite filename)
    createJSONMetaData(filename, data)


def export_image_to_drive(image, roi=None, name=None, folder="default_drive_folder_name"):
    """ Export one image to Google Drive
    Arguments
        :param image: image to export
        :param roi=None: specify the roi (as python list),
                         Default: compute from image dimension
        :param name=None: name of the image
    """
    if roi == None:
        roi = getGeometryImage(image).coordinates().getInfo()
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
    total = len(image_to_run)
    counter = 0
    nb_task_max = 100

    # metadata_list = getMetaDataListImage(image_to_run).getInfo()
    # image_to_run = []

    print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Export to drive started", ""))
   
    while len(image_to_run) > 0:
        # getTaskList()
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
                updateJSONMetaData("Metadata_mask.json", meta_data)

                print("{:4d}/{} = {:05.2f}%   Image {}".format(counter,
                                                            total,
                                                            counter / total * 100, image_name))
                counter += 1

        # Use quit a long time (30s) since there is lag between the moment the task is launched 
        # (in Python) and the time it really starts on GEE
        time.sleep(30)
    
    print("{:-<100}\n|{:^98}|\n{:-<100}".format("", "Export to drive finished !", ""))


ee.Initialize()

list_image = getAllImagesInColl('users/ab43536/masks_4_methods')
exportImageListToDrive(list_image, "Mask_UK_2018")

# cancelAllTask()
