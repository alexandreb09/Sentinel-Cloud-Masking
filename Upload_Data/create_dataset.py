import pandas as pd
import numpy as np
from sklearn.utils import shuffle
import h5py
from utils import progress, startProgress, endProgress, getDates
import ee

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
        # data = {
        #     "keys": list(f.keys()),
        #     "class_names": f["class_names"][()].astype('U13'),
        #     "class_ids": [id for id in f["class_ids"]],
        # }

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

    print("File loaded !")
    return df #, data



def filter_nb_pixels_per_image(df, n=1625):
    """ Remove all the group of image having less than
            - n cloud pixels 
            - n non cloud pixels
    Arguments:
        :param df: dataframe to process
        :param n=1625: nb_min of cloud pixels and non cloud pixel per image
    """
    list_to_keep = []
    
    for name, df_images in df.groupby('id_GEE'):
        nb_pixel_cloud = len(df_images[df_images.cloud == True])
        nb_pixel_not_cloud = len(df_images[df_images.cloud == True])
        # print(str(nb_pixel_cloud) + " + " + str(nb_pixel_not_cloud) + " = " + str(len(df_images.id_GEE)))
        if nb_pixel_cloud > n or nb_pixel_not_cloud > n:
            list_to_keep.append(name)

    df = df[df.id_GEE.isin(list_to_keep)]

    return df


def total_dataframe_filtered(filename, filename2):
    """ Return one dataframe from the 3 dataset file sources 
        + filter them
    Arguments:
        :param filename: 
        :param filename2: 
        :param filename3: 
    """
    df = getDataFromH5File(filename)
    df2 = getDataFromH5File(filename2)

    df = filter_nb_pixels_per_image(df)
    df2 = filter_nb_pixels_per_image(df2)

    return df.append(df2)


def create_training_evaluation_dataset(df):
    """ 
    Return two dataframes:
        - a training dataset compose by 1000 cloudy pixels and 1000 non cloudy pixels per images
            -> final size: 1000 * 2 * number_of_images
        - an evaluation dataset compose by 300 cloudy pixels and 300 non cloudy pixels per image
            -> final size: 300 * 2 * number_of_images
    Arguments:
        :param df: dataframe to split in training and evaluation dataset
    """
    training = pd.DataFrame()
    evaluation = pd.DataFrame()
    print(len(df.groupby('id_GEE')))
    for name, images in df.groupby('id_GEE'):
        # Select cloudy and non cloudy dataframe
        df_cloud = images[images.cloud]
        df_not_cloud = images[~images.cloud]

        # Shuffle dataframe
        df_cloud = shuffle(df_cloud)
        df_not_cloud = shuffle(df_not_cloud)
        
        # Select the 1250 first pixels of training dataset
        training = training.append(df_cloud.iloc[:1250])
        training = training.append(df_not_cloud.iloc[:1250])

        # Select the first 375 pixels for evalutaion dataset
        evaluation = evaluation.append(df_cloud.iloc[1250:1625])
        evaluation = evaluation.append(df_not_cloud.iloc[1250:1625])

    # Shuffle training and evaluation dataframe
    training = shuffle(training)
    evaluation = shuffle(evaluation)

    return training, evaluation


def convert_Granule_Product_ID_To_GEEID(filename):
    """
    - Read a file
    - Transform granule_id + product_id en GEE_id
    - Remove useless data
    - Save file as a new one

    Arguments:
        :param filename: file to process
    """
    def removeT(df):
        """
        Remove the first letter 'T' of the columns
        Arguments:
            :param df: column of a dataframe 
        """
        if df.iloc[0][0] == 'T':
            df = df.str[1:]
        return df

    # Connexion to GEE
    ee.Initialize()
    with h5py.File(filename, "r") as f:
        data = {
            "class_names": f["class_names"][()].astype('U13'),
            "band_names": ["B" + bd.astype('U13') for bd in f["band"]],
            "class_ids": [id for id in f["class_ids"]],
        }

        df = pd.DataFrame({
            "product_id": f["product_id"][()].astype(str),
            "granule_id": f["granule_id"][()].astype(str),
            "longitude": f["longitude"][()].astype(np.float64),
            "latitude": f["latitude"][()].astype(np.float64),
            "pixel_class": f["classes"][()].astype(int),
        })

        # a 'T' is present in 2016 dataset
        df["granule_id"] = removeT(df.granule_id)

        list_ID = []
        dict_ID = {}

        dataset = ee.ImageCollection("COPERNICUS/S2")

        # Initialise progross bar
        nb_rows = df["granule_id"].shape[0]
        startProgress("Translation ID GEE")

        # For each pixel from .h5 file
        for i, (granule_id, product_id) in enumerate(zip(df["granule_id"], df["product_id"])):
            # If the granule + product_id unkonw:
            if granule_id + product_id not in dict_ID.keys():
                # read dates begin + end
                date_deb, date_fin = getDates(product_id)
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

        # End progress bar
        endProgress()

    with h5py.File("new_file.h5", "w") as f:
        f.create_dataset("latitude", data=df.latitude.values)
        f.create_dataset("longitude", data=df.longitude.values)
        f.create_dataset("id_GEE", data=np.string_(list_ID))
        f.create_dataset("cloud", data=df.pixel_class.isin([40, 50]).values)
        f.create_dataset("class_names", data=np.string_(data["class_names"]))
        f.create_dataset("band_names", data=np.string_(data["band_names"]))
        f.create_dataset("class_ids", data=data["class_ids"])

    print("New file created !")


    
def createDataSet():
    """
    Like entry function: brief summary to sample the data.
    """
    filename = 'Data/dataset_part1_20160914.h5'
    filename2 = 'Data/dataset_part2_20160914.h5'

    # Creation whole dataset from the 2 dataset files
    df_total = total_dataframe_filtered(filename, filename2)

    print("Nb photos total: ",  len(df_total.groupby(by="id_GEE")))
    print("Nb pixel per image: ", df_total.groupby(by="id_GEE").size())

    # Create training and evaluation dataset
    training_df, evaluation_df = create_training_evaluation_dataset(df_total)
    print("Nb pixel per image training: ", training_df.groupby(by="id_GEE").size())

    # Save both dataset to excel
    training_df.to_excel("training.xlsx")
    evaluation_df.to_excel("evaluation.xlsx")

# createDataSet()