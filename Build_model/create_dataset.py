#########################################################################################
# Create training and test dataset script file                                          #
#                                                                                       #
# Methods:                                                                              #
#       - clean_H5_Files(filename)                                                      #
#       - getDataFromH5File(filename, number_rows_kept)                                 #
#       - filter_nb_pixels_per_image(df)                                                #   
#       - total_dataframe_filtered(filename, filename2)                                 #
#       - create_training_evaluation_dataset(df)                                        #
#       - add_empty_methods_columns(df)                                                 #
#                                                                                       #
# Process:                                                                              #
#   - Download the labelled data from gitlab repository                                 #
#     https://gitext.gfz-potsdam.de/EnMAP/sentinel2_manual_classification_clouds        #
#     File : 20160914_s2_manual_classification_data.h5                                  #
#   - Split the .h5 file into two subfiles (same size). This is to facilitate data      #
#     manipulation with smaller files                                                   #
#   - For each image in these files: add the GEE image ID based on Sentinel image ID    #
#   - Remove useless data                                                               #
#   - Merge these 2 files as 1 dataframe                                                #
#   - Filter images in order that each image has the same number of                     #
#     "cloudy" / "not cloudy" pixels                                                    #
#   - Add empty feature columns to training and test set                                #
#   - Export the results in the ".xlsx" file                                            #
#                                                                                       #
# Then the excel file created can be used in the "run_methods.py" file                  #
#                                                                                       #
# NOTE: change line 305 the path to the differents files (input .h5 file,               #
#       excel output..)                                                                 #
#########################################################################################

import pandas as pd
import numpy as np
from sklearn.utils import shuffle
import h5py
from utils import progress, startProgress, endProgress, getDates, export_df_train_eval_to_excel, splitH5File
import ee


#########################################################
#                   PARAMETERS                          #
#########################################################

# Path to the source dataset
# Assumes file is the same as downloaded here:
# https://gitext.gfz-potsdam.de/EnMAP/sentinel2_manual_classification_clouds/blob/master/20160914_s2_manual_classification_data.h5
h5_file = r'Build_model\Data\20160914_s2_manual_classification_data.h5'
sub_h5_file1 = r'Build_model\Data\20160914_sub_file1.h5'
sub_h5_file2 = r'Build_model\Data\20160914_sub_file2.h5'

excel_file_output = r'Build_model\Data\train_test_set.xlsx'

# Size training and test set
N_TRAINING = 100000
N_EVAL = 30000

#########################################################
#                   FUNCTIONS                           #
#########################################################

def clean_H5_Files(filename):
    """
    - Read a file
    - Transform granule_id + product_id in GEE_id
    - Remove useless data
    - Save data in a new file with suffix "_cleaned"
        Ex: input: "filename.h5" >>> output: "filename_cleaned.h5"

    Arguments:
        :param filename: file to process
        :return: path to the new file created
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
                               .sort("system:asset_size", False) \
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

    new_filename = filename[:-3] + "_cleaned" + filename[-3:]
    with h5py.File(new_filename, "w") as f:
        f.create_dataset("latitude", data=df.latitude.values)
        f.create_dataset("longitude", data=df.longitude.values)
        f.create_dataset("id_GEE", data=np.string_(list_ID))
        f.create_dataset("cloud", data=df.pixel_class.isin([40, 50]).values)
        f.create_dataset("class_names", data=np.string_(data["class_names"]))
        f.create_dataset("band_names", data=np.string_(data["band_names"]))
        f.create_dataset("class_ids", data=data["class_ids"])

    print("New file created !")

    return new_filename

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


def filter_nb_pixels_per_image(df):
    """ 
    Iterating till having the same number of pixels for each images:
    For example: if there are 80 images and N_TRAINING=80 000 and N_EVAL = 20000
        All the images with less than (80 000 + 20 000)/ 80 = 1250 pixels are removed
        Then, among these 1250 pixels, 50% must be cloud, 50% not cloud
    At the end, we expect each image has the same number of cloudy/not cloudy pixels
    Arguments:
        :param df: dataframe to process
        :return: filtered dataset
    """
    list_to_keep = []

    # While each image hasn't the required number of pixel:
    stop = False
    while not stop:
        # Groupd the dataframe by imahe
        df_grouped = df.groupby('id_GEE')
        nb_images = len(df_grouped)
        n_tr = N_TRAINING//len(df_grouped)+1
        n_ev = N_EVAL//len(df_grouped)+1
        # Total number of cloudy and non cloudy pixels an must have
        n = n_tr + n_ev

        # For each image
        for name, df_images in df_grouped:
            # Compute the number of cloudy / non cloudy pixels
            nb_pixel_cloud = len(df_images[df_images.cloud == True])
            nb_pixel_not_cloud = len(df_images[df_images.cloud == True])
            # If thoses numbers greater than n
            if nb_pixel_cloud > n or nb_pixel_not_cloud > n:
                # The image is kept
                list_to_keep.append(name)

        # Reshape the dataframe with only the images to keep
        df = df[df.id_GEE.isin(list_to_keep)]
        # If the number of images hasn't changed
        if nb_images == len(df.groupby('id_GEE')):
            # exit the loop
            stop = True

    # print("FINAL Nb images: ", len(df_grouped))
    # print("FINAL Nb pixel per image expected: ", n)
    return df


def total_dataframe_filtered(filename, filename2):
    """ Return one dataframe from the 2 dataset file sources 
        + filter them
    Arguments:
        :param filename: .h5 file 1
        :param filename2: .h5 file 2
    """
    df = getDataFromH5File(filename)
    df2 = getDataFromH5File(filename2)

    df = df.append(df2)

    df = filter_nb_pixels_per_image(df)

    return df


def create_training_evaluation_dataset(df):
    """ 
    Return two dataframes:
        - a training dataset compose by pixels from all images:
            - Number of pixel per images = N_TRAINING // nb_images + 1
            -> final size: (N_TRAINING // nb_images + 1) * 2 * number_of_images
        - a training dataset compose by pixels from all images:
            - Number of pixel per images = N_EVAL // nb_images + 1
            -> final size: (N_EVAL // nb_images + 1) * 2 * number_of_images
    Arguments:
        :param df: dataframe to split in training and evaluation dataset
        :return: a training and test set
    """
    training_cloud = pd.DataFrame()
    training_not_cloud = pd.DataFrame()
    evaluation_cloud = pd.DataFrame()
    evaluation_not_cloud = pd.DataFrame()

    nb_images = len(df.groupby('id_GEE'))
    print("Nb images: ", nb_images)

    nb_pixel_per_image_training = 100000 // nb_images + 1
    nb_pixel_per_image_evaluation = nb_pixel_per_image_training + 30000 // nb_images + 1

    for name, images in df.groupby('id_GEE'):
        # Select cloudy and non cloudy dataframe
        df_cloud = images[images.cloud]
        df_not_cloud = images[~images.cloud]

        # Shuffle dataframe
        df_cloud = shuffle(df_cloud)
        df_not_cloud = shuffle(df_not_cloud)

        # Select the n first pixels for training dataset
        training_cloud = training_cloud.append(df_cloud.iloc[:nb_pixel_per_image_training])
        training_not_cloud = training_not_cloud.append(df_not_cloud.iloc[:nb_pixel_per_image_training])

        # Select the first n' pixels for evalutaion dataset
        evaluation_cloud = evaluation_cloud.append(df_cloud.iloc[nb_pixel_per_image_training:nb_pixel_per_image_evaluation])
        evaluation_not_cloud = evaluation_not_cloud.append(df_not_cloud.iloc[nb_pixel_per_image_training:nb_pixel_per_image_evaluation])

    # Resize to 100 000 and 30 000 pixels in total
    training = training_cloud[:100000].append(training_not_cloud[:100000]).sort_values("id_GEE")
    evaluation = evaluation_cloud[:30000].append(evaluation_not_cloud[:30000]).sort_values("id_GEE")
    
    training['index'] = np.arange(training.shape[0])
    evaluation['index'] = np.arange(evaluation.shape[0])

    return training, evaluation




def add_empty_methods_columns(df):
    """ Add the following columns to the dataframe
    Arguments:
        :param df: Dataframe to add columns
        :return:dataframe with the columns added
    """
    list_col = ["tree1", "tree2", "tree3", "percentile1", "percentile2","percentile3","percentile4","percentile5",
                "persistence1", "persistence2", "persistence3", "persistence4", "persistence5", ]
    for col_name in list_col:
        df[col_name] = ""
    return df



if __name__ == "__main__":
    # Connexion to GEE
    ee.Initialize()

    # Split big h5 into 2 sub h5 files
    splitH5File(h5_file, sub_h5_file1, sub_h5_file2)

    # Create GEE_ID image id from sentinel 2 image ID
    # Remove useless columns
    sub_h5_file1_cleaned = clean_H5_Files(sub_h5_file1)
    sub_h5_file2_cleaned = clean_H5_Files(sub_h5_file2)

    # Creation whole dataset from the 2 dataset files
    df_total = total_dataframe_filtered(sub_h5_file1_cleaned, sub_h5_file2_cleaned)

    print("Nb photos total: ",  len(df_total.groupby(by="id_GEE")))
    print("Nb pixel per image: ", df_total.groupby(by="id_GEE").size())

    # Create training and evaluation dataset
    training_df, evaluation_df = create_training_evaluation_dataset(df_total)

    training_df = add_empty_methods_columns(training_df)
    evaluation_df = add_empty_methods_columns(evaluation_df)

    print("Nb pixel per image: ", training_df.groupby(by="id_GEE").size())

    # Save both dataset to excel
    export_df_train_eval_to_excel(
        training_df, evaluation_df, filename=excel_file_output)

