# Import modules
import ee               # GEE
import sys, os          # Set file path
import time             # Sleep between task running
import logging          # Write logs
import json             # Read previously define json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))


from Utils.utils import getGeometryImage, get_name_collection, export_image_to_GEE, init_logger
from Utils.utils_tasks import getNumberActiveTask
from Utils.utils_assets import getAllImagesInColl
from cloud_masking_model import computeCloudMasking
import parameters





def process_and_store_to_GEE(date_start=None, date_end=None, geometry=None,
                             folder='users/ab43536/default_name', image_to_exclude=[],
                             nb_task_max=parameters.nb_task_max, silent=False):
    
    if not silent:
        logging.info("{:-<98}\n|{:^98}|\n{:-<100}".format("", "Processus started :-)", ""))
   

    if not date_start: date_start = parameters.date_start
    if not date_end: date_end = parameters.date_end
    if not geometry: geometry = parameters.geometry

    # Load geometry
    if isinstance(geometry, list):
        geometry = ee.Geometry.Polygon(geometry)
    elif isinstance(geometry, str):
        # Feature name
        geometry = ee.FeatureCollection(geometry)
    else:
        raise ValueError("The geometry must either be a list of coordinates"
                        " points or a string to a featureCollection already imported in GEE assets")

    # Get Sentinel ImageCollection according to filters
    col = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(date_start, date_end) \
            .filterBounds(geometry)

    # If imageCollection do not exist: create one
    if folder not in [elt["id"] for elt in ee.data.getList({"id":'/'.join(folder.split('/')[:-1])})]:
        ee.data.createAsset({'type': "ImageCollection"}, folder)

    # Get all image name as a python list (string)
    image_names = get_name_collection(col).getInfo()
    total = len(image_names)

    # Select image ID
    image_done = [ img.split('/')[-1] for img in getAllImagesInColl(folder)]
    image_to_exclude = [img.split('/')[-1] for img in image_to_exclude]
    image_names = [img.split('/')[-1] for img in image_names]

    image_names = list(set(image_names) - set(image_done))
    # Ignore image to exclude
    image_names = list(set(image_names) - set(image_to_exclude))

    if not silent:
        logging.info('\t- There are {} images in Sentinel Collection matching date and area constraints'.format(total))
        logging.info('\t- There are {} images already processed (already existing in GEE folder)'.format(len(image_done)))
        logging.info('\t- There are {} images to ignore'.format(len(image_to_exclude)))
        logging.info('\t- There are {} images to process'.format(len(image_names)))

    k = 0
    total = len(image_names)

    # Land geometry
    geo_land = ee.FeatureCollection(parameters.land_geometry)

    while len(image_names) > 0:
        nb_task_pending = getNumberActiveTask()

        if nb_task_pending < nb_task_max:
            new_images = nb_task_max - nb_task_pending
            # Select the n first images
            image_running = image_names[:new_images]
            # Remove them from image to run
            image_names = image_names[new_images:]

            for name in image_running:
                full_name = 'COPERNICUS/S2/' + name
                logging.info("{:4d}/{} = {:05.2f}%   Image {}".format(k, total, k / total * 100, name))

                # Ignore images that not intersect the land geometry
                if ee.Image(full_name).geometry().intersects(geo_land).getInfo():
                    mask = computeCloudMasking(full_name)
                    export_image_to_GEE(image=mask, asset_id=folder, roi=getGeometryImage(ee.Image(full_name)),
                                    name=name, num=k, total=total)
                else:
                    logging.info("The image {} do not intersect the area. It has been ignored".format(name))
                k += 1
        
        time.sleep(30)


if __name__ == "__main__":
    ee.Initialize()

    init_logger()

    
    with open('Metadata_mask.json', 'r') as f:
        data = json.load(f)
    
    image_done = list(data.keys())

    process_and_store_to_GEE(folder='users/ab43536/masks_4_methods', image_to_exclude=image_done)

    # land_geometry = ee.FeatureCollection(parameters.land_geometry)
    # print(ee.Image("COPERNICUS/S2/20180710T114349_20180710T114347_T30VXP")
    #       .geometry().intersects(land_geometry).getInfo())

    # computeCloudMasking("COPERNICUS/S2/20180710T114349_20180710T114347_T30VXP")
