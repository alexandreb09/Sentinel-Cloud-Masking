#########################################################
# File to process the interpolation and save the        #
# output in GEE storage                                 #
#                                                       #
# Method:                                               #
#       - apply_interpolation_and_export()              #
#                                                       #
# What you need to do:                                  #
#   - Setup the parameters in parameters.py             #
#       - The dates and area are requried               #
#       - the land_geometry is optional (used to clip   #
#         output image)                                 #
#   - Run this current file                             #
#                                                       #
# NOTE:                                                 #
#   - This script doesn't handle the number of active   #
#     task. This is a problem if more than 3000 images  #
#     are processed.                                    #
#   - This script is exporting images to GEE storage    #
#     This destination might become a problem because   #
#     of restricted number of assets allowed by GEE     #
#     Also, the number of images will increase in GEE   #
#     storage however, the bigger the number of images  #
#     used for the interpolation, the better it is.     #
#       -> One solution might be to change to export    #
#          to the DRIVE using                           #
#          "ee.batch.Export.image.toDrive"              #
#       -> The function 'export_image_to_drive' in      #
#          Cloud_masking/Utils/utils_assets performs    #
#          this task..                                  #
#                                                       #
# What the script is doing:                             #
#   - Load parameters from "parameters.py"              #
#   - Load the data mask collection from GEE            #
#   - Build the sentinel dataset and filter according   #
#     area and date provided in parameters.py           #
#   - Apply the interpolation using the harmonic model  #
#   - Read images already processed from .json file     #
#   - Iterate over the interpolated images:             #
#       - Export each images one by one                 #
#         (one image = one GEE task)                    #
#########################################################


import ee
import json
import os
import logging

import interpolatation_model as harmo_model
import load_dataset
import utils

import parameters

def apply_interpolation_and_export():
    """ Apply the harmonic interpolations to all images matching the criteria from the 
        parameters.py file
        Export all the images one by one
    """

    roi = ee.Geometry.Polygon(parameters.ROI)
    date_start = parameters.date_start
    date_end = parameters.date_end
    day_gap_before = parameters.day_gap_before
    day_gap_after = parameters.day_gap_after

    sentinel_coll_name = parameters.sentinel_coll_name
    dependent = parameters.dependent
    json_file = parameters.JSON_FILE
    folder_GEE = parameters.folder_GEE
    land_geometry = parameters.land_geometry
    bands = parameters.bands

    if land_geometry:
        land_geometry = ee.FeatureCollection(land_geometry)
    
    utils.init_logger(parameters.log_path)
    # LOAD MASK FUNCTIONS
    # Date used for fitting the model
    date_start_fit = ee.Date(date_start).advance(-day_gap_before, "day")
    date_end_fit = ee.Date(date_end).advance(-day_gap_after, "day")

    maskCollection = load_dataset.loadMaskCollection('users/ab43536/masks_4_methods',
                                        sentinel_coll_name, roi,
                                        date_start_fit, date_end_fit)


    #####################################
    #       INTERPOLATION               #
    #####################################
    # Filter to the area of interest, mask clouds, add variables.
    sentinel = load_dataset.build_sentinel_dataset(maskCollection, sentinel_coll_name) \
                            .filterDate(date_start_fit, date_end_fit) \
                            .filterBounds(roi)


    fittedHarmonic = harmo_model.fit(sentinel, dependent)


    # Remove image date gap before and after
    fittedHarmonic = fittedHarmonic.filterDate(date_start, date_end)

    nb_images = fittedHarmonic.size().getInfo()
    fittedHarmonic = fittedHarmonic.toList(nb_images)

    data = {}
    
    if json_file:
        with open(json_file, "r") as f:
            data = json.load(f)
    else:
        json_file = "Interpolation/Data/Metadata_NDVI_images.json"
        directory = "/".join(json_file.split('/')[:-1])
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(json_file, "w") as f: f.write("{}")
    
    already_processed = [img.split('/')[-1] for img in list(data.keys())]

    # If imageCollection do not exist: create one
    if folder_GEE not in [elt["id"] for elt in ee.data.getList({"id": '/'.join(folder_GEE.split('/')[:-1])})]:
        ee.data.createAsset({'type': "ImageCollection"}, folder_GEE)

    logging.info("{:-<98}\n|{:^98}|\n{:-<100}".format("",
                                                "Processus started :-)", ""))
    for i in range(nb_images):
        image = ee.Image(fittedHarmonic.get(i))
        image_roi = image.geometry().coordinates()
        if land_geometry: image = image.clip(land_geometry)
        else: image = image.clip(roi)

        name = image.id().getInfo()
        logging.info("{:4d}/{} = {:05.2f}%   Image {}".format(i, nb_images,
                                                              i/nb_images*100, name))
        if name not in already_processed:
            task = utils.export_image_to_GEE(image.select(bands), asset_id=folder_GEE, roi=image_roi,
                                             name=name, num=i, total=nb_images)
            
            meta_data = {name: utils.getMetaDataImage(image)}
            utils.updateJSONMetaData(json_file, meta_data)

    logging.info("{:-<98}\n|{:^98}|\n{:-<100}".format("", "Process finished :-)", ""))
   

if __name__ == "__main__":
    ee.Initialize()
    
    apply_interpolation_and_export()
