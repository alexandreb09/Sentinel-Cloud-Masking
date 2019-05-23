import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from Methods_cloud_masking.perso_luigi_utils import getGeometryImage
from Methods_cloud_masking.multitemporal_cloud_masking import CloudClusterScore
from Methods_cloud_masking.perso_tree import getMaskTree1, getMaskTree2, getMaskTree3
import ee
import pandas as pd
from utils import startProgress, progress, endProgress



def newColumnsFromImage(df, mask_prev, isTreeMethod):
    """
    Return the result of
    Arguments:
        :param df:
        :param mask_prev: predicted image
        :param isTreeMethod: boolean for the key in the Google Earth Engine dictionary
    """
    key = "cluster"
    if isTreeMethod:
        key = "constant"

    coordinates = df[["longitude", "latitude"]].values.tolist()

    # GEE array of coordinate
    array_coordinate_GEE = ee.List(coordinates)

    def get_pixel_result(coordinates):
        point = ee.Geometry.Point(coordinates)
        return mask_prev.reduceRegion(ee.Reducer.first(), point, 20).get(key)

    # GEE object : list of prediction for each pixel (1 x nb_pixels)
    new_col = array_coordinate_GEE.map(get_pixel_result)

    # print(new_col.size().getInfo())
    # Return python list
    return new_col.getInfo()


def applyTreeMasking(df, method_name):
    """
    Arguments:
        :param df: dataframe to process
    """
    # progress bar
    startProgress("Execution method" + method_name)

    # For each images e.g. pixels from same image
    for i, (name, df_pixels) in enumerate(df.groupby("id_GEE")):
        # Create GEE Image
        image = ee.Image(name)
        # Apply tree1 cloud detection
        maskTree1 = getMaskTree3(image)

        df.loc[df.id_GEE == name, method_name] = newColumnsFromImage(
            df_pixels, maskTree1, True)

        # Update progress bar
        progress(i * 100/80)

    endProgress()
    print(df)
    return df


def apply_method_1_to_5(df, method_name):
    """
    Arguments:
        :param df: df to process
    """
    # progress bar
    startProgress("Execution method 1 à 5")

    # For each images e.g. pixels from same image
    for i, (name, df_pixels) in enumerate(df.groupby("id_GEE")):
        # Create GEE Image
        image = ee.Image(name)
        region_of_interest = getGeometryImage(image)

        for i in range(1, 6):
            cloud_score_persistence = CloudClusterScore(image,
                                region_of_interest,
                                method_pred="percentile")[0]
            method_cour_name = method_name + "_" + str(i)
            df.loc[df.id_GEE == name, method_cour_name] = newColumnsFromImage(
                df_pixels, cloud_score_persistence, False)

        for i in range(1, 6):
            cloud_score_persistence = CloudClusterScore(image,
                                                        region_of_interest,
                                                        method_pred="persistence")[0]
            method_cour_name = method_name + "_" + str(i)
            df.loc[df.id_GEE == name, method_cour_name] = newColumnsFromImage(
                df_pixels, cloud_score_persistence, False)

        df.loc[df.id_GEE == name, "tree1"] = newColumnsFromImage(
            df_pixels, getMaskTree1(image), True)
        df.loc[df.id_GEE == name, "tree2"] = newColumnsFromImage(
            df_pixels, getMaskTree2(image), True)
        df.loc[df.id_GEE == name, "tree3"] = newColumnsFromImage(
            df_pixels, getMaskTree3(image), True)

        df.to_excel("Data/training.xlsx")
        # Update progress bar
        progress(i * 100/80)

    endProgress()
    print(df)
    return df


def apply_all_methods_save(filename):
    """
    Arguments:
        :param filename: filename to process
    """
    # progress bar
    # startProgress("Execution method")

    # get the number of group to process
    df = pd.read_excel(filename)

    nb_nan_values = df[df["percentile1"].isnull()].shape[0]

    # print("nb nan values: ", nb_nan_values)
    # print("nb group: ", nb_group)
    if nb_nan_values > 0:
        nb_group = len(df.groupby("id_GEE"))

    print("Nb images to process:", nb_group)

    # for i, (name, df_pixels) in enumerate(df_part.groupby("id_GEE")):
    for _ in range(nb_group):

        df_total = pd.read_excel(filename)
        cols_original = list(df_total.columns)

        # Ignore "unnamed" columns
        df_total = df_total[df_total.filter(regex='^(?!Unnamed)').columns]

        boolean_vector_done = ~df_total["percentile1"].isnull()

        df_already_done = df_total[boolean_vector_done]
        df_not_done = df_total[~boolean_vector_done].sort_values(by="id_GEE")

        print("Df done: ", df_already_done.shape)
        print("Df todo: ", df_not_done.shape)

        name, df_pixels = list(df_not_done.groupby("id_GEE"))[0]

        # Create GEE Image
        image = ee.Image(name)
        region_of_interest = getGeometryImage(image)

        for method_number in range(1, 6):
            method_name = "percentile"
            while True:
                try:
                    cloud_score_persistence = CloudClusterScore(image,
                                                                region_of_interest,
                                                                method_number=method_number,
                                                                method_pred=method_name)[0]
                    method_cour_name = method_name + str(method_number)
                    new_col = newColumnsFromImage(df_pixels, cloud_score_persistence, False)
                    df_not_done.loc[df_not_done.id_GEE == name, [method_cour_name]] = new_col
                    break
                except ee.ee_exception.EEException:
                    print("Error GEE occurs")


        for method_number in range(1, 6):
            method_name = "persistence"
            while True:
                try:
                    cloud_score_persistence = CloudClusterScore(image,
                                                                region_of_interest,
                                                                method_number=method_number,
                                                                method_pred=method_name)[0]
                    method_cour_name = method_name + str(method_number)
                    new_col = newColumnsFromImage(df_pixels, cloud_score_persistence, False)
                    df_not_done.loc[df_not_done.id_GEE == name, [method_cour_name]] = new_col
                    break
                except ee.ee_exception.EEException:
                    print("Error GEE occurs")

        print(" " * 5 + "- Method used: tree1")
        while True:
            try:
                new_col = newColumnsFromImage(df_pixels, getMaskTree1(image), True)
                df_not_done.loc[df_not_done.id_GEE == name, ["tree1"]] = new_col
                break
            except ee.ee_exception.EEException:
                print("Error GEE occurs")


        print(" " * 5 + "- Method used: tree2")
        while True:
            try:
                new_col = newColumnsFromImage(df_pixels, getMaskTree2(image), True)
                df_not_done.loc[df_not_done.id_GEE == name, ["tree2"]] = new_col
                break
            except ee.ee_exception.EEException:
                print("Error GEE occurs")
        
        print(" " * 5 + "- Method used: tree3")
        while True:
            try:
                new_col = newColumnsFromImage(df_pixels, getMaskTree3(image), True)
                df_not_done.loc[df_not_done.id_GEE == name, ["tree3"]] = new_col
                break
            except ee.ee_exception.EEException:
                print("Error GEE occurs")

        print("Sauvegarde")
        df_full = df_already_done.append(df_not_done)

        # Save - export
        df_full = df_full[df_full.filter(regex='^(?!Unnamed)').columns]
        df_full.to_excel(filename)
        # Read again (update df: restart from last row)
        # df_full = pd.read_excel(filename)
        # df_full = df_full[df_full.filter(regex='^(?!Unnamed)').columns]
        # print("Restauration")

        # Update progress bar
        # progress(_ * 100/80)
        print("Image: {0}/{1} = {2} %".format(_, nb_group, _/nb_group*100))
        print("*" * 50)

    # endProgress()




if __name__ == "__main__":
    ee.Initialize()
    # df_training = pd.read_excel("Data/training.xlsx")
    # print(df_training)
    # df_res = apply_method_1_to_5(df_training, method_name)

    file_name = "Data/training.xlsx"
    apply_all_methods_save(file_name)

