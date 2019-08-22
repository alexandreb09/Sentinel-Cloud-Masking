import ee
import json
import os

import interpolatation_model as harmo_model
from parameters import *
import load_dataset
import utils


def apply_interpolation_and_export():
    """ Apply the harmonic interpolations to all images matching the criteria from the 
        parameters.py file
        Export all the images one by one
    """

    #################################
    #    LOAD MASK FUNCTIONS        #
    #################################
    roi = ee.Geometry.Polygon(ROI)

    # Date used for fitting the model
    date_start_fit = ee.Date(date_start).advance(-day_gap_before, "day")
    date_end_fit = ee.Date(date_end).advance(-day_gap_after, "day")

    # create bands names
    fitted_band = "fitted_" + str(harmo_10)
    recovered_band = "NDVI_final_" + str(harmo_10)

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
    json_file = JSON_FILE
    if json_file:
        with open(json_file, "r") as f:
            data = json.load(f)
    else:
        json_file = ".\Interpolation\Data\Metadata_NDVI_images.json"
        directory = "\\".join(json_file.split('\\')[:-1])
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(json_file, "w") as f: f.write("{}")
    
    already_processed = [img.split('/')[-1] for img in list(data.keys())]

    # If imageCollection do not exist: create one
    if folder_GEE not in [elt["id"] for elt in ee.data.getList({"id": '/'.join(folder_GEE.split('/')[:-1])})]:
        ee.data.createAsset({'type': "ImageCollection"}, folder_GEE)

    print("Exportation started :-)")

    for i in range(nb_images):
        image = ee.Image(fittedHarmonic.get(i)).clip(roi)
        name = image.id().getInfo()
        print("Image {:4d} on {:4d}  {}".format(i, nb_images, name))
        if name not in already_processed:
            task = utils.export_image_to_GEE(image, asset_id=folder_GEE, roi=None,
                                             name=name, num=i, total=nb_images)
            
            meta_data = {name: utils.getMetaDataImage(image)}
            utils.updateJSONMetaData(json_file, meta_data)

    print("Exportation finshed !")

if __name__ == "__main__":
    ee.Initialize()
    
    apply_interpolation_and_export()
