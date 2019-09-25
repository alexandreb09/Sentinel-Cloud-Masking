#####################################################
# File to run the whole cloud masking process       #
#                                                   #
# WARNING: before running this file, be sure to     #
# check the "Cloud_masking/parameters.py" file.     #
# All the parameters are read from this file.       #
#                                                   #
# Method:                                           #
#   - process_and_store_to_GEE(date_start,          #
#                              date_end,            #
#                              geometry,            #
#                              folder_GEE,          #
#                              excel_file,          #
#                              image_to_exclude,    #
#                              nb_task_max,         #
#                              silent)              #
#                                                   #
# The function 'process_and_store_to_GEE' is        #
# called at the bottom of the file                  #
#                                                   #
# To ignore some images exported outside GEE        #
# the 'image_to_exclude' is designed for.           #
# At the bottom of the file (line 239)              #
#
#####################################################



# Import modules
import ee               # GEE
import sys, os          # Set file path
import time             # Sleep between task running
import logging          # Write logs
import json             # Read previously define json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))

from Utils.utils import getGeometryImage, get_name_collection, export_image_to_GEE, init_logger, date_gap
from Utils.utils_tasks import getNumberActiveTask, getTaskList, cancelAllTask
from Utils.utils_assets import getAllImagesInColl
from cloud_masking_model import computeCloudMasking
import parameters


def process_and_store_to_GEE(date_start=None, date_end=None, geometry=None,
                             geo_land=None, folder_GEE=None, excel_file=None,
                             image_to_exclude=[], nb_task_max=None,
                             silent=False):
    """ Method to run the whole cloud masking process
    Arguments:
        :param date_start=None: Starting date time (if None not set, read from parameter)
        :param date_end=None: End date time (if None not set, read from parameter)
        :param geometry=None: Geometry that roughly overlay the UK
        :param geo_land=None: path a GEE featureCollection (border area for example)
        :param folder_GEE=None: GEE folder (python string)
        :param excel_file=None: excel file (file create by previous ecution)
        :param image_to_exclude=[]: list images to exclude
        :param nb_task_max=parameters.nb_task_max: maximum number of tasks running at the same time
        :param silent=False: show log messages
    
    NOTE: The image already stored in the "folder_GEE" are ignored (not processed again)
    """

    if not silent:
        logging.info("{:-<98}\n|{:^98}|\n{:-<100}".format("", "Process started :-)", ""))
   
    # Load variable from parameters
    if not date_start:  date_start  = parameters.date_start
    if not date_end:    date_end    = parameters.date_end
    if not geometry:    geometry    = parameters.geometry
    if not folder_GEE:  folder_GEE  = parameters.folder_GEE
    if not excel_file:  excel_file  = parameters.excel_file
    if not nb_task_max: nb_task_max = parameters.nb_task_max
    if not geo_land:    geo_land    = ee.FeatureCollection(parameters.land_geometry)
    
    # Adjust date_start and date_end
    date_start, date_end = date_gap(date_start, date_end)

    # Load geometry
    if isinstance(geometry, list):
        geometry = ee.Geometry.Polygon(geometry)
    elif isinstance(geometry, str):
        # Feature name
        geometry = ee.FeatureCollection(geometry)
    else:
        raise ValueError("The geometry must either be a list of coordinates"
                        " or a string to a featureCollection already imported in GEE assets")

    # Get Sentinel ImageCollection according to filters
    col = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(date_start, date_end) \
            .filterBounds(geometry)

    # If imageCollection do not exist: create one
    if folder_GEE not in [elt["id"] for elt in ee.data.getList({"id":'/'.join(folder_GEE.split('/')[:-1])})]:
        ee.data.createAsset({'type': "ImageCollection"}, folder_GEE)

    # Get all image name as a python list (string)
    image_names = get_name_collection(col).getInfo()
    total = len(image_names)

    # Load image to ignore from xlsx file
    image_ignored = []
    output = pd.DataFrame({"Result": [], "Task_id": []})
    output.index.name = "Name"
    if os.path.isfile(excel_file):
        output = pd.read_excel(excel_file)
        image_ignored = output.Name.values
        output = output.set_index("Name")

        to_remove = output.Result.isin(["RUNNING", "READY"])

        # Cancel task running and ready
        cancelAllTask(task_list=output.Task_id[to_remove].values[:10])

        output = output[~to_remove]
        output.to_excel(excel_file)

    else:
        ans = input('The excel file "{}" doesn\'t exist. Continue and ignore? (Y/N) :'.format(excel_file))
        if lower(ans) != "y": sys.exit()
        else:
            output.to_excel(excel_file)
    
    # Select image ID
    image_done_GEE = [img.split('/')[-1] for img in getAllImagesInColl(folder_GEE)]
    image_to_exclude = [img.split('/')[-1] for img in image_to_exclude]
    image_names = [img.split('/')[-1] for img in image_names]

    # Ignore image to exclude
    image_names = list(set(image_names) - set(image_done_GEE)
                                        - set(image_to_exclude)
                                        - set(image_ignored))
    
    if not silent:
        logging.info('\t- There are {} images in Sentinel Collection matching date and area constraints'.format(total))
        logging.info('\t- There are {} images already processed (already existing in GEE folder)'.format(len(image_done_GEE)))
        logging.info('\t- There are {} images out of the area of interest (ignored)'.format(sum(output.Result.eq("Out of area"))))
        logging.info('\t- There are {} images that have failed'.format(sum(output.Result.eq("FAILED"))))
        logging.info('\t- There are {} images to ignored (given in parameters) '.format(len(image_to_exclude)))
        logging.info('\t- There are {} images to process'.format(len(image_names)))



    # Init variables
    read = True                     # Read output file (dynamically updated when the openning fails)
    counter_img = 0                 # Count the current image processed
    total = len(image_names)        # Number of images to process
    task_bag = set()                # Set of tasks
    
    process = True                  # While condition 
    while process:
        # Read the xlsx file 
        # "read" might be set to false if the previous writting try failed
        # If that is the case, the xlsx file isn't read (to not lose the updates
        # perform during the loop)
        if read:
            try:
                # read excel file
                output = pd.read_excel(excel_file)
                output = output.set_index("Name")
            except PermissionError:
                logging.info("The xlsx file has't been updated (permission denied)")


        # Get the number of active task (from xlsx file)
        # nb_task_pending = getNumberActiveTask()
        nb_task_pending = output.Result.isin(["READY", "RUNNING"]).sum()
        new_images = nb_task_max - nb_task_pending      # Number task that can be run

        # some counters
        nb_img_ran = 0
        k = 0

        # For the possible number of images to run
        while k < len(image_names) and nb_img_ran < new_images:
            # Select first image from list and remove it from list
            name = image_names[0]
            image_names = image_names[1:]

            # Create full image ID
            full_name = 'COPERNICUS/S2/' + name
            logging.info(
                "{:4d}/{} = {:05.2f}%   Image {}".format(counter_img, total, counter_img / total * 100, name))
            
            out_put_row = {"Result": "Out of area",
                           "Task_id": "ignored"}
            
            # Check if image intersect the land geometry
            if ee.Image(full_name).geometry().intersects(geo_land).getInfo():
                # Get cloud mask
                mask = computeCloudMasking(full_name)
                # Export (store) to GEE
                new_task = export_image_to_GEE(image=mask, asset_id=folder_GEE, roi=getGeometryImage(ee.Image(full_name)),
                                               name=name, num=counter_img, total=total)
                # Add task to list of tasks
                task_bag.add(new_task)
                # Update data informations 
                out_put_row.update({"Result": new_task.status().get("state"),
                                    "Task_id": new_task.status().get("id")})
                # Update counter
                nb_img_ran += 1
            else:
                logging.info("The image {} do not intersect the area. It has been ignored".format(name))

            # Add row in out_put dataframe (state of image)
            output.loc[name] = out_put_row
            # Update counter
            k += 1
            counter_img += 1
        
        # Update the task set
        to_remove = set()
        # For each task
        for task in task_bag:
            # Read task status 
            task_info = task.status()
            status = task_info.get("state")
            # If task failed or completed: add task to the tasks to remove
            if status in ["FAILED", "COMPLETED"]:
                to_remove.add(task)
            
            # Update output content (excel file)
            output.loc[output.Task_id == task_info.get("id"), "Result"] = status
        
        # Remove finished tasks
        for task_to_rm in to_remove:
            task_bag.remove(task_to_rm)

        # Save output in xlsx file
        try:
            output.to_excel(excel_file)
            read = True
        except PermissionError:
            logging.info("The xlsx file has't been updated (permission denied)")
            read = False

        # Exit condition
        if len(task_bag) == 0 and len(image_names) == 0:
            process = False    
        else: time.sleep(30)
    
    logging.info("{:-<98}\n|{:^98}|\n{:-<100}".format("",
                                                      "Process finished :-)", ""))



if __name__ == "__main__":
    # Initiate GEE connexion
    ee.Initialize()
    # Initiate logger
    init_logger(parameters.LOG_FILE)

    # Load image name from images already processed
    # (image exported from the GEE storage)
    image_done = []
    if parameters.JSON_FILE != None:
        with open(parameters.JSON_FILE, 'r') as f:
            data = json.load(f)
        image_done = list(data.keys())
        
    # Luanch process
    process_and_store_to_GEE(image_to_exclude=image_done)
