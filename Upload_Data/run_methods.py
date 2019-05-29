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


def newColumnsFromImage(df, mask_prev, isTreeMethod):
    """
    Return the result of
    Arguments:
        :param df:
        :param mask_prev: predicted image
        :param isTreeMethod: boolean for the key in the Google Earth Engine dictionary
    """

    key = "cluster"
    if isTreeMethod: key = "constant"

    # Get coordinates
    coordinates = df[["index", "longitude", "latitude"]].values.tolist()

    # GEE array of coordinate
    array_coordinate_GEE = ee.List(coordinates)

    # Row is compose by :
    def get_pixel_result(row):
        """
        Arguments:
            :param row: ee.List([id, long, lat])
            :return:    ee.List([id, res])
        """
        row = ee.List(row)
        point = ee.Geometry.Point(row.slice(1, 3))
        return row.slice(0, 1).add(mask_prev.reduceRegion(ee.Reducer.first(), point, 20)
                                   .get(key))
    # GEE object : list of prediction for each pixel (1 x nb_pixels)
    new_col = array_coordinate_GEE.map(get_pixel_result)

    # Return python list
    return new_col.getInfo()


# def applyTreeMasking(df, method_name):
#     """
#     Arguments:
#         :param df: dataframe to process
#     """
#     # progress bar
#     startProgress("Execution method" + method_name)

#     # For each images e.g. pixels from same image
#     for i, (name, df_pixels) in enumerate(df.groupby("id_GEE")):
#         # Create GEE Image
#         image = ee.Image(name)
#         # Apply tree1 cloud detection
#         maskTree1 = getMaskTree3(image)

#         df.loc[df.id_GEE == name, method_name] = newColumnsFromImage(
#             df_pixels, maskTree1, True)

#         # Update progress bar
#         progress(i * 100/80)

#     endProgress()
#     print(df)
#     return df


# def apply_method_1_to_5(df, method_name):
#     """
#     Arguments:
#         :param df: df to process
#     """
#     # progress bar
#     startProgress("Execution method 1 à 5")

#     # For each images e.g. pixels from same image
#     for i, (name, df_pixels) in enumerate(df.groupby("id_GEE")):
#         # Create GEE Image
#         image = ee.Image(name)
#         region_of_interest = getGeometryImage(image)

#         for i in range(1, 6):
#             cloud_score_persistence = CloudClusterScore(image,
#                                 region_of_interest,
#                                 method_pred="percentile")[0]
#             method_cour_name = method_name + "_" + str(i)
#             df.loc[df.id_GEE == name, method_cour_name] =
#                       newColumnsFromImage(df_pixels, cloud_score_persistence,False)

#         for i in range(1, 6):
#             cloud_score_persistence = CloudClusterScore(image,
#                                                         region_of_interest,
#                                                         method_pred="persistence")[0]
#             method_cour_name = method_name + "_" + str(i)
#             df.loc[df.id_GEE == name, method_cour_name] =
#              newColumnsFromImage(df_pixels, cloud_score_persistence, False)

#         df.loc[df.id_GEE == name, "tree1"] = newColumnsFromImage(
#             df_pixels, getMaskTree1(image), True)
#         df.loc[df.id_GEE == name, "tree2"] = newColumnsFromImage(
#             df_pixels, getMaskTree2(image), True)
#         df.loc[df.id_GEE == name, "tree3"] = newColumnsFromImage(
#             df_pixels, getMaskTree3(image), True)

#         df.to_excel("Data/training.xlsx")
#         # Update progress bar
#         progress(i * 100/80)

#     endProgress()
#     print(df)
#     return df


def apply_all_methods_save(filename):
    """
    Arguments:
        :param filename: filename to process
    """
    list_errors = []

    #  Read the excel file
    df_total = pd.read_excel(filename, sheet_name = "Training")

    df_total["index"] = [i for i in range(df_total.shape[0])]

    # Boolean vector of image to process
    boolean_vector_todo = df_total["percentile1"].isnull()

    # Split total dataframe in: done and todo
    df_todo = df_total[boolean_vector_todo].sort_values("id_GEE")

    # Nb images totals
    nb_images_total = len(df_todo["id_GEE"].unique())

    # for _ in range(image_already_done, nb_group + 1):
    for i, (name, df_pixels) in enumerate(df_todo.groupby("id_GEE")):

        # Boolean vector of image to process
        boolean_vector_todo = df_total["percentile1"].isnull()

        # Split total dataframe en already done and todo
        df_todo = df_total[boolean_vector_todo].sort_values("id_GEE")
        df_done = df_total[~boolean_vector_todo].sort_values("id_GEE")

        nb_pixels_todo = df_todo.shape[0]
        nb_pixels_done = df_done.shape[0]
        nb_image_done = len(df_done["id_GEE"].unique())
        nb_image_todo = len(df_todo["id_GEE"].unique())

        print("Image name: {0}".format(name))
        print("Nb images done: %2d e.g. %5d pixels" % (nb_image_done, nb_pixels_done))
        print("Nb images todo: %2d e.g. %5d pixels" % (nb_image_todo, nb_pixels_todo))
        print("Progression: %2.2f %%" % (i/nb_images_total*100))
        # Create GEE Image - ROI
        image = ee.Image(name)
        region_of_interest = getGeometryImage(image)


        for method in ["tree1", "tree2", "tree3"]:
            print(" " * 5 + "- Method used: {0}".format(method))
            stop = False
            while not stop:
                try:
                    # Google answer (Python object)
                    pixel_res = np.array(newColumnsFromImage(df_pixels, getMaskTree1(image),True))

                    stop = True
                except ee.ee_exception.EEException as e:
                    print(" " * 10 + "Error GEE occurs:", e)

            # Create df from GEE answer
            new_df = pd.DataFrame({"index": pixel_res[:, 0],
                                   method: pixel_res[:, 1]})
            new_df = new_df.set_index("index")

            # Update the column of current method on "index" index
            df_total = new_df.combine_first(df_total)


        list_methods = [(x, y) for x in ["percentile", "persistence"] for y in range(1,6)]
        for method_name, method_number in list_methods:
            method_cour_name = method_name + str(method_number)

            print(" " * 5 + "- Method used: " + method_name + " " + str(method_number))
            stop = False
            while not stop:
                try:
                    cloud_score_image = CloudClusterScore(image,
                                                                region_of_interest,
                                                                method_number=method_number,
                                                                method_pred=method_name)[0]

                    # Google answer (Python object)
                    pixel_res = np.array(newColumnsFromImage(df_pixels,
                                                                cloud_score_image,
                                                                False))
                    # Create df from GEE answer
                    new_df = pd.DataFrame({
                        "index": pixel_res[:, 0],
                        method_cour_name: pixel_res[:, 1]
                    })
                    stop = True

                except ee.ee_exception.EEException as e:
                    print(" " * 10 + "Error GEE occurs:", e)

                    if str(e)[:18] == 'Dictionary.toArray':
                        print(" " * 15 + "Images skiped")

                        new_df = pd.DataFrame({'index': df_pixels["index"],
                                                method_cour_name: "ERROR"})
                        list_errors.append([method_cour_name, name])
                        stop = True


            new_df = new_df.set_index("index")

            # Update the column of current method on "index" index
            df_total = new_df.combine_first(df_total)


        # Save - export
        export_df_to_excel(df_total, "Training")

        print("*" * 50)

    print("!" * 58 + "\n" + "!" * 5 + " " * 20 + "FINISHED" + " " * 20 + "!" * 5 + "\n" + "!" * 58)
    print("\n\n" + len(list_errors) + " occured: ", list_errors)

def find_problematic_pictures(filename):
    """
    Display all the problematic pictures (cloudclustering not working)
    Arguments:
        :param filename: 
    """
    df = pd.read_excel(filename)
    nb_group = len(df.groupby("id_GEE"))

    for i, (name, df_pixels) in enumerate(df.groupby("id_GEE")):
        # Create GEE Image
        image = ee.Image(name)
        region_of_interest = getGeometryImage(image)

        cloud_score_image = CloudClusterScore(image,
                                                    region_of_interest,
                                                    method_number=1,
                                                    method_pred="persistence")[0]
        try:
            cloud_score_image.getInfo()
        except ee.ee_exception.EEException:
            print(name)
        print("Image: {0}/{1} = {2} %".format(i+1, nb_group,(i+1)/nb_group*100))

if __name__ == "__main__":
    ee.Initialize()
    # df_training = pd.read_excel("Data/training.xlsx")
    # print(df_training)
    # df_res = apply_method_1_to_5(df_training, method_name)

    file_name = "Data/results.xlsx"
    sheet_name = "Training"
    apply_all_methods_save(file_name)

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