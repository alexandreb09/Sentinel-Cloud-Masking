import pandas as pd
import numpy as np
import os
import h5py
import ee


from utils import getDates, startProgress, progress, endProgress

import sys
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
        if not (number_rows_kept):
            number_rows_kept = f["longitude"].shape[0]

        # Extra data
        data = {
            "keys": list(f.keys()),
            "class_names": f["class_names"][()].astype('U13'),
            "band_names": ["B" + bd.astype('U13') for bd in f["band"]],
            "class_ids": [id for id in f["class_ids"]],
        }

        # DataFrame creation
        df = pd.DataFrame({
            "longitude": f["longitude"][:number_rows_kept].astype(np.float64),
            "product_id": f["product_id"][:number_rows_kept].astype(str),
            "granule_id": f["granule_id"][:number_rows_kept].astype(str),
            "latitude": f["latitude"][:number_rows_kept].astype(np.float64),
            "pixel_class": f["classes"][:number_rows_kept].astype(np.float64),
        })
        df["cloud"] = df.pixel_class.isin([40, 50])

        print(f["longitude"].shape)

        for i, band in enumerate(data["band_names"]):
            df[band] = (f["spectra"][:number_rows_kept, i]*10000).astype(int)

    df = ajout_GEE_Ids(df)

    print("Loading file done !")
    return data, df


def printClassNames(class_ids, class_names):
    print("\nId Names")
    for id, name in zip(class_ids, class_names):
        print("%2d %s" % (id, name))


"""
def getIdsImagesSentinels(sentinel):
    granual_id_list = ee.Dictionary(sentinel.aggregate_histogram('GRANULE_ID')).keys()
    return granual_id_list.getInfo()
"""


def ajout_GEE_Ids(df):
    """Create a new columns: id_GEE (image id in GEE dataset)
        :param df: 
    """
    
    list_ID = []
    dict_ID = {"33UUUS2A_OPER_PRD_MSIL1C_PDMC_20160817T230018_R022_V20160817T101032_20160817T101559.SAFE":
               "COPERNICUS/S2/20160817T101032_20160817T171509_T33UUU"}

    dataset = ee.ImageCollection("COPERNICUS/S2")

    # Initialise progross bar
    nb_rows = df["granule_id"].shape[0]
    startProgress("Translation ID GEE")

    # For each pixel from .h5 file
    for i, (granule_id, product_id) in enumerate(zip(df["granule_id"], df["product_id"])):
        # If the granule + product_id unkonw:
        if granule_id + product_id not in dict_ID.keys():
            date_deb, date_fin = getDates(product_id)               # read dates begin + end
            # Filter dataset per date, area
            # + sort per time + select first image
            image = dataset.filterDate(date_deb, date_fin) \
                            .filterMetadata('MGRS_TILE', 'equals', granule_id) \
                            .sort("system:time_end") \
                            .first()
            # Add id to list of known id
            dict_ID[granule_id + product_id] = image.getInfo()["id"]

        # Set GEE image id in dataframe
        list_ID.append(dict_ID[granule_id + product_id])
        
        # Update progress bar
        if (i % (nb_rows // 100) == 0):
            progress(i/nb_rows*100)

    # Add id_GEE column
    df["id_GEE"] = pd.DataFrame(list_ID)
    
    # End progress bar
    endProgress()
    return df

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
    print(type(list_image_id_df))
    print("List images:", [print(img) for img in list_image_id_df])

    # creation new dataframe
    df_final = pd.DataFrame()
    for image_id_gee in list_image_id_df:
        print("id: ", image_id_gee)
        image = ee.Image(image_id_gee)
        maskTree1 = getMaskTree1(image)
        
        df_image = df.loc[df["id_GEE"] == image_id_gee]
        df_image = df_image.reindex()

        df_image["tree1"] = newColumnsFromImage(df_image, maskTree1)
        df_final.append(df_image)

    return df_final

if __name__ == "__main__":
    ee.Initialize()

    filename = 'Data/20170523_s2_manual_classification_data.h5'
    number_rows_kept = 200000
    
    
    data, df = getDataFromH5File(filename, number_rows_kept=number_rows_kept)
    
    df = applyTree1Masking(df)
    print(df.head(10))



    
    pd.options.display.max_colwidth = 100
    print(df[:5])


    # df = df.iloc[4000]

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

    # df_image1 = df.loc[df["granule_id"] == "32TNR"]
    # createOneRaster(df_image1, "test.tif", 20)

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
