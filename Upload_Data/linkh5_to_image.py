import pandas as pd
import numpy as np
import os
import h5py
import ee
import sys


from utils import getDates, startProgress, progress, endProgress

sys.path.append("../Methods_cloud_masking")
from perso_tree import getMaskTree1

def getDataFromH5File(filename, number_rows_kept=None):
    """
    Read h5 file and return data as a dict
    Arguments:
        :param filename: 
        :param number_rows_kept=None: 
    """

    # Open file
    with h5py.File(filename, 'r') as f:

        # Reduce the number of row read
        if not number_rows_kept:
            number_rows_kept = f["longitude"].shape[0]

        # Extra data
        data = {
            "keys": list(f.keys()),
            "class_names": f["class_names"][()].astype('U13'),
            "class_ids": [id for id in f["class_ids"]],
        }

        # DataFrame creation
        df = pd.DataFrame({
            "id_GEE": f["id_GEE"][:number_rows_kept].astype(str),
            "longitude": f["longitude"][:number_rows_kept].astype(np.float64),
            "latitude": f["latitude"][:number_rows_kept].astype(np.float64),
            "cloud": f["cloud"][:number_rows_kept].astype(np.float64) == 1,
        })
        
        print("Nb pixels:", f["longitude"].shape[0])


    # Remove valueless column
    # df = df[["longitude", "latitude", "cloud", "id_GEE"]]

    print("Loading file done !")
    return data, df



def createTrainingVerifDataset(df):
    """ Remove all the group of image having less than
            - 1000 cloud pixels 
            - 1000 non cloud pixels
    Arguments:
        :param df: dataframe to process
    """
    list_to_keep = []
    
    for name, df_images in df.groupby('id_GEE'):
        nb_pixel_cloud = len(df_images[df_images.cloud == True])
        nb_pixel_not_cloud = len(df_images[df_images.cloud == True])
        print(str(nb_pixel_cloud) + " + " + str(nb_pixel_not_cloud) + " = " + str(len(df_images.id_GEE)))
        if nb_pixel_cloud > 1000 or nb_pixel_not_cloud > 1000:
            list_to_keep.append(name)

    df = df[df.id_GEE.isin(list_to_keep)]

    return df


def printClassNames(class_ids, class_names):
    print("\nId Names")
    for id, name in zip(class_ids, class_names):
        print("%2d %s" % (id, name))




def newColumnsFromImage(df, image):    
    coordinates = df[["longitude", "latitude"]].values.tolist()

    # GEE array of coordinate
    array_coordinate_GEE = ee.List(coordinates)

    def setResult(row):
        point = ee.Geometry.Point(row)
        return image.reduceRegion(ee.Reducer.first(), point, 20).get("constant")

    new_col = array_coordinate_GEE.map(setResult)

    return new_col.getInfo()

def applyTree1Masking(df):
    list_image_id_df = np.unique(df[["id_GEE"]])
    # print(type(list_image_id_df))
    # print("List images:", [print(img) for img in list_image_id_df])

    # creation new dataframe
    df_final = pd.DataFrame()
    for image_id_gee in list_image_id_df:
        # print("id: ", image_id_gee)
        image = ee.Image(image_id_gee)
        maskTree1 = getMaskTree1(image)
        
        df_image = df.loc[df["id_GEE"] == image_id_gee]
        df_image = df_image.reindex()

        df_image["tree1"] = newColumnsFromImage(df_image, maskTree1)
        df_final.append(df_image)

    return df_final

if __name__ == "__main__":
    ee.Initialize()

    filename = 'Data/dataset_part1_20160914.h5'
    filename2 = 'Data/dataset_part2_20160914.h5'
    filename3 = 'Data/dataset_part3_20170710.h5'
    number_rows_kept = 3000000
    
    
    data, df = getDataFromH5File(filename, number_rows_kept=number_rows_kept)
    # data2, df2 = getDataFromH5File(filename2, number_rows_kept=number_rows_kept)

    print("Nb photos: ", len(df.groupby(by="id_GEE")))
    # print(df.groupby(by="id_GEE").size())
    
    # df = applyTree1Masking(df)

    createTrainingVerifDataset(df)
    
    pd.options.display.max_colwidth = 100
    print(df[:5])
    # print(df2[:5])
    
    # print(df[ df.columns[6:19]].tail(1))
    # pd.options.display.max_colwidth = 100
    # print(df[["granule_id", "product_id"]].tail(1))

    # print(df[["longitude", "latitude", "pixel_class"]].tail(1))
    # pd.options.display.max_colwidth = 100
    # print(df["id_GEE"].tail(1))

    # print(printClassNames(data["class_ids"], data["class_names"]))

    # print(df.head(5))
    # ids_image_sentinel = getIdsImagesSentinels(sentinel_dataset)
    # [print(x) for x in ids_image_sentinel[:5]]
    # print(np.unique(df[["granule_id", "product_id"]]))


"""
    df1 = df.groupby("granule_id").longitude.max()
    print(df1)
    print(df.longitude.min())
    
    df2 = df.loc[df["granule_id"] == "32TNR"]

    print(df2)

    df2.to_csv("data.csv.gz", compression='gzip')
"""

# Nb pixel cloud:
# cloud      Count
# False    2042931
# True      985802
