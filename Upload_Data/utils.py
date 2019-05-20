from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import h5py
import sys
import ee

ee.Initialize()

def getDates(granule):
    details = granule.split("_")
    date_fin = format_date(details[5][:8])
    date_deb1 = format_date(details[7][1:9])
    date_deb2 = format_date(details[8][:8])
    date_deb = min(date_deb1, date_deb2)

    if (date_deb == date_fin):
        date_fin = add_one_day(date_fin)

    return date_deb, date_fin


def format_date(date):
    """
    Convert "YYYYMMJJ" to "YYYY-MM-JJ"
        :param date: string date of format "YYYYMMJJ"
    """
    return datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")

def add_one_day(date):
    return datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)


def startProgress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-"*50 + "]" + chr(8)*51)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    global progress_x
    x = int(x * 50 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x


def endProgress():
    sys.stdout.write("#" * (50 - progress_x) + "]\n")
    sys.stdout.flush()


def unzipFile(source):
    """
    Arguments:
        :param source: file.gz name to uncompress  
    """
    import gzip

    input = gzip.GzipFile(source, 'rb')
    s = input.read()
    input.close()

    output = open(source[:-3], 'wb')
    output.write(s)
    output.close()

    print("Fichier enregistré !")



def splitH5File(filename):
    """
    Split the .h5 file in two file (middle)
    Argument: filename
        param filename: 
    """
    with h5py.File(filename, 'r') as f_old:
        nb_rows = f_old["longitude"].shape[0]
        keys = list(f_old.keys())

        key_copy_all = ['band', 'class_ids', 'class_names']
        key_copy_part = ['latitude', 'longitude', 'granule_id', 'product_id', 'classes']


        with h5py.File("new_file_part1.h5", 'w') as f_new:
            for key in keys:
                if key in key_copy_all:
                    f_new.create_dataset(key, data=f_old[key])
                elif key in key_copy_part:
                    f_new.create_dataset(key, data=f_old[key][:nb_rows//2])

        with h5py.File("new_file_part2.h5", 'w') as f_new:
            for key in keys:
                if key in key_copy_all:
                    f_new.create_dataset(key, data=f_old[key])
                elif key in key_copy_part:
                    f_new.create_dataset(key, data=f_old[key][:nb_rows//2])



def convert_Granule_Product_ID_To_GEEID(filename):
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

        ['author', 'band', 'bandwidth_nm', 'central_wavelength_nm', 'cite', 'class_ids', 'class_names', 'classes', 'continent', 'country', 'dates', 'granule_id', 'latitude',
            'licence', 'longitude', 'product_id', 'spatial_sampling_m', 'spectra', 'sun_azimuth_angle', 'sun_zenith_angle', 'viewing_azimuth_angle', 'viewing_zenith_angle']

    print(list_ID[:10])

    with h5py.File("new_file.h5", "w") as f:
        f.create_dataset("latitude", data=df.latitude.values)
        f.create_dataset("longitude", data=df.longitude.values)
        f.create_dataset("id_GEE", data=np.string_(list_ID))
        f.create_dataset("cloud", data=df.pixel_class.isin([40, 50]).values)
        f.create_dataset("class_names", data=np.string_(data["class_names"]))
        f.create_dataset("band_names", data=np.string_(data["band_names"]))
        f.create_dataset("class_ids", data=data["class_ids"])

    print("New file created !")


def saveDF(df, new_filename):
    """
    Save dataframe as a new .h5 file
    Argument:
        :param df: dataframe to save 
        :param new_filename: new file name
    """
    with h5py.File(new_filename, 'w') as f:
        for column_name in df.columns:
            f.create_dataset(column_name, data=df[column_name])
    print("File saved !")
