################################################
# Convert data from JS code Editor
# Clean up and summarize data in one excel file
################################################

import glob
from itertools import groupby
import pandas as pd
import json
import ee
import logging
import os


def clean_and_save_data():
    """ Clean and save the data generated when exporting some points from the Web interface script:
        "users/ab43536/Interpolation"
    """
    def keyf(text):
        return "_".join(text.split("\\")[-1].split("_")[:3])


    list_file = glob.glob(r"Interpolation/Sample_data_Actual_fitted_NDVI/*.csv")
    list_file_grouped = [list(items)
                        for gr, items in groupby(sorted(list_file), key=keyf)]

    with pd.ExcelWriter('Interpolation/sample_data.xlsx') as writer:
        i = 0
        for filename in list_file_grouped:
            df = pd.read_csv(filename[0])
            df = pd.DataFrame()
            for sheet in filename:
                # print(sheet)
                col_name = sheet.split("_")[-1][:-4]
                df_cur = pd.read_csv(sheet)
                df_cur = pd.DataFrame({"NDVI" + col_name: eval(df_cur.NDVI.values[0]),
                                    col_name: eval(df_cur.fitted_name.values[0])})
                # print(df_cur)
                df = pd.concat([df, df_cur], axis=1)
            i += 1
            # print(df)
            df.to_excel(writer, sheet_name=keyf(filename[0]), index=False)


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
    except FileNotFoundError:
        old_data = {}
    # Merge data
    data = {**old_data, **new_data}
    # Save it (overwrite filename)
    createJSONMetaData(filename, data)


def getGeometryImage(image):
    """ Return the image geometry build from border
    Arguments:
        :param image: GEE Image
        :return: ee.Geometry.Polygon
    """
    return ee.Geometry.Polygon(ee.Geometry(image.get('system:footprint')).coordinates())


def export_image_to_GEE(image, asset_id="users/ab43536/", roi=None,
                        name=None, num=None, total=None):
    """ Export one image to asset
    Arguments:
        :param image: image to export
        :param asset_id="users/ab43536/": 
        :param roi=None: specify the roi, default compute from image dimension
        :type roi: Python List
        :param name=None: name of the image
        :param num=None: optional number for the image (appear on task list in GEE web interface )
        :param total=None: total number of image processing (appear on task list in GEE web interface )
        :return: task        
    NOTE: the ROI must be a Python list.

        If "num" and "total" (must have the both) are passed, the description of the 
        task with be: "Image `num` on `total` equal `num/total` pourcent"
    """
    if roi == None:
        roi = image.geometry().coordinates()
    if name == None:
        name = image.id().getInfo()
    description = "Default export"
    if num != None and total != None:
        description = "Image {} on {} equal {:05.2f} pourcent".format(
            num, total, num / total * 100)
    # print(description)
    assetId = asset_id + '/' + name

    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toAsset(image=image,
                                         description=description,
                                         assetId=assetId,
                                         scale=30,
                                         region=roi.getInfo(),
                                         )
    # Run the task
    task.start()
    return task


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


def init_logger(path):
    """ Init the logger
    """
    # Check directory exists 
    # If not: create directory
    directory = "/".join(path.split('/')[:-1])
    if not os.path.exists(directory):
        os.makedirs(directory)

    level = logging.INFO
    format = '  %(message)s'
    handlers = [logging.FileHandler(path),
                logging.StreamHandler()]

    logging.basicConfig(level=level, format=format, handlers=handlers)
