#############################################################
# File to build the training and test set                   #
# Methods:                                                  #
#       - newColumnsFromImage(df, mask_prev,                #
#                             isTreeMethod, geometry)       #
#       - apply_all_methods_save(filename, sheetname)       #
#                                                           #
# This file is used after having preprocess the H5 and      #
# assumes the excel file has been created                   #
#                                                           #
# What this script is doing:                                #
#   - Iterate over all the images in the excel file         #
#     according the "ig_GEE" columns                        #
#       -  Iterate over the 13 cloud masking methods        #
#          (percentile 1 to 5, persistence 1 to 5 and       #
#          tree 1 to 3). For each method:                   #
#           - Apply the cloud mask the GEE image            #
#           - Extract the values from the result image      #
#       - Save the results in the excel file                #
#                                                           #
# Note: For each method, the scrip is iterating until       #
#       the GEE request is successful. Indeed, acccording   #
#       to the charge on the GEE, the request might fails.  #
#       Rerunning the same task might solve it.             #
#                                                           #
#       If the "Background cloud masking" method fails,     #
#       the image is ignore and the results are save in the #
#       excel file.                                         #
#                                                           #
#       The current script doesn't use a logger, just calls #
#       "print" to output current status. The logs are      #
#       NOT save.                                           #
#############################################################

import os
import sys
import ee
import pandas as pd
import numpy as np

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from Methods_cloud_masking.multitemporal_cloud_masking import CloudClusterScore
from Methods_cloud_masking.perso_tree import getMaskTree1, getMaskTree2, getMaskTree3
from Methods_cloud_masking.perso_luigi_utils import getGeometryImage
from Upload_Data.utils import startProgress, progress, endProgress, export_df_to_excel


def newColumnsFromImage(df, mask_prev, isTreeMethod, geometry):
    """
    For each pixels in DF, returns the values in the "mask_prev"
    Arguments:
        :param df:
        :param mask_prev: predicted image
        :param isTreeMethod: boolean for the key in the Google Earth Engine dictionary
    """
    def get_pixel_result(row):
        """
        Read a GEE list composed of the pixel ID, longitude and latitude
        and return the values of the mask for this pixel
        Arguments:
            :param row: ee.List([id, long, lat])
            :return:    ee.List([id, res])
        """
        row = ee.List(row)
        point = ee.Geometry.Point(row.slice(1, 3))
        # Check if longitude - lattitude aren't swiped
        point = ee.Geometry.Point(ee.Algorithms.If(point.containedIn(geometry),
                                                   point.coordinates(),
                                                   point.coordinates().reverse()))
        # Apply reduction : extract pixel result
        val = mask_prev.reduceRegion(ee.Reducer.first(), point, 20).get(key)
        # Replace None value by -1
        val = ee.Algorithms.If(ee.Algorithms.IsEqual(val, 0),
                               val,
                               ee.Algorithms.If(ee.Algorithms.IsEqual(val, 1),
                                                val,
                                                -1))
        return row.slice(0, 1).add(val)

    # key = "cluster"
    # if isTreeMethod: key = "constant"
    key = mask_prev.bandNames().get(0)

    # Get coordinates
    coordinates = df[["index", "longitude", "latitude"]].values.tolist()

    # GEE array of coordinate
    array_coordinate_GEE = ee.List(coordinates)

    # GEE object : list of prediction for each pixel (1 x nb_pixels)
    new_col = array_coordinate_GEE.map(get_pixel_result)

    # Return python list
    return new_col.getInfo()




def apply_all_methods_save(filename, sheetname):
    """ Read an excel file 
        For each images: 
            - Apply all the methods [percentile 1 to 5, persistence 1 to 5, tree 1 to 3]
            - Save the output for each pixel in a "result" dataframe
    Results: saved in the same excel file (same sheet) in the matching columns
    
    This process is quite long. The request might face GEE restriction. 
    The script is looping (infinite loop) till the success. 

    If the process failed or is stopped, the script is reading the "percentile1" columns
    to find the rows proceeded. The script will ignore all the rows where there is 
    data in "percentile1" column.

    Arguments:
        :param filename: excel files with the ["index", "longitude", "latitude"] columns
        :param sheetname: sheetname in the excel file
    """
    list_errors = []

    #  Read the excel file
    df_total = pd.read_excel(filename, sheet_name = sheetname)

    # Boolean vector of image to process
    boolean_vector_todo = df_total["percentile1"].isnull()

    # Split total dataframe in: done and todo
    df_todo = df_total[boolean_vector_todo].sort_values("id_GEE")

    # Nb images totals
    nb_images_total = len(df_todo["id_GEE"].unique())

    # Iterate per images (sub dataframe for each image)
    for i, (name, df_pixels) in enumerate(df_todo.groupby("id_GEE")):
        # Boolean vector of image to process
        boolean_vector_todo = df_total["percentile1"].isnull()

        # Split total dataframe in already done and todo
        df_todo = df_total[boolean_vector_todo].sort_values("id_GEE")
        df_done = df_total[~boolean_vector_todo].sort_values("id_GEE")

        # Some logs
        nb_pixels_todo = df_todo.shape[0]
        nb_pixels_done = df_done.shape[0]
        nb_image_done = len(df_done["id_GEE"].unique())
        nb_image_todo = len(df_todo["id_GEE"].unique())
        print("Image name: {0}".format(name))
        print("Nb images done: %2d e.g. %5d pixels" % (nb_image_done, nb_pixels_done))
        print("Nb images todo: %2d e.g. %5d pixels" % (nb_image_todo, nb_pixels_todo))
        print("Progression: %2.2f %%" % (i / nb_images_total * 100))
        
        # Create GEE Image - ROI
        image = ee.Image(name)
        region_of_interest = getGeometryImage(image)

        # Iterate over all the "percentile" and "persistence" methods
        list_methods = [(x, y) for x in ["percentile", "persistence"] for y in range(1, 6)]
        for method_name, method_number in list_methods:
            # Method name (for ex: "persistence1")
            method_cour_name = method_name + str(method_number)

            print(" " * 5 + "- Method used: " + method_name + " " + str(method_number))
            stop = False
            while not stop:
                try:
                    # GEE cloud mask
                    cloud_score_image = CloudClusterScore(image,
                                                        region_of_interest,
                                                        method_number=method_number,
                                                        method_pred=method_name)[0]

                    # Google answer (Python object)
                    pixel_res = np.array(newColumnsFromImage(df_pixels,
                                                            cloud_score_image,
                                                            False,
                                                            region_of_interest))
                    # Create df from GEE answer
                    new_df = pd.DataFrame({
                        "index": pixel_res[:, 0],
                        method_cour_name: pixel_res[:, 1]
                    })
                    stop = True

                # Handle GEE exception
                except ee.ee_exception.EEException as e:
                    print(" " * 10 + "Error GEE occurs:", e)

                    # If the script fails due to no data:
                    # The image is ignored
                    if str(e)[:18] == 'Dictionary.toArray':
                        print(" " * 15 + "Images skiped")

                        new_df = pd.DataFrame({'index': df_pixels["index"],
                                                method_cour_name: "ERROR"})
                        list_errors.append([method_cour_name, name])
                        stop = True


            new_df = new_df.set_index("index")

            # Update the column of current method on "index" index
            df_total = new_df.combine_first(df_total)

        # Apply the 3 "decision tree" methods
        for method in ["tree1", "tree2", "tree3"]:
            print(" " * 5 + "- Method used: {0}".format(method))
            # loop while the GEE request successes
            stop = False
            while not stop:
                # Handle GEE exception
                try:
                    # Google answer (Python object)
                    pixel_res = np.array(newColumnsFromImage(df_pixels, getMaskTree1(image),
                                                             True, region_of_interest))
                    stop = True
                except ee.ee_exception.EEException as e:
                    print(" " * 10 + "Error GEE occurs:", e)

            # Create df from GEE answer
            new_df = pd.DataFrame({"index": pixel_res[:, 0],
                                   method: pixel_res[:, 1]})
            new_df = new_df.set_index("index")

            # Update the column of current method on "index" index
            df_total = new_df.combine_first(df_total)

        # Save - export
        export_df_to_excel(df_total, sheetname, filename=filename)

        print("*" * 50)

    print("!" * 58 + "\n" + "!" * 5 + " " * 20 + "FINISHED" + " " * 20 + "!" * 5 + "\n" + "!" * 58)
    print("\n\n" + str(len(list_errors)) + " occured: ", list_errors)



if __name__ == "__main__":
    # Initiate GEE connection
    ee.Initialize()

    file_name = "Data/Evaluation.xlsx"
    sheet_name = "Evaluation"
    apply_all_methods_save(file_name, sheet_name)

    # import time
    # t1 = time.time()
    # df_total = pd.read_excel(file_name, sheet_name="Training")
    # t2 = time.time()

    # print("Read in %5s" % (t2 - t1))
    # ~ 30s
    # df_total["tree1"] = -1
    # t3 = time.time()
    # print("Process in %5s" % (t3 - t2))
    # export_df_to_excel(df_total, sheet_name)
    # print("Written in %5s" % (time.time() - t3))
    # ~ 150s = 2min 30
