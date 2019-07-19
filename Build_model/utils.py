import ee
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import h5py
import sys


def getDates(granule):
    """ Read a Sentinel image ID and extract the beginning and finishing date
    Arguments:
        :param granule: Sentinel Image ID
    """

    def format_date(date):
        """
        Convert "YYYYMMJJ" to "YYYY-MM-JJ"
            :param date: string date of format "YYYYMMJJ"
        """
        return datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")

    def add_one_day(date):
        return datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)

    details = granule.split("_")
    date_fin = format_date(details[5][:8])
    date_deb1 = format_date(details[7][1:9])
    date_deb2 = format_date(details[8][:8])
    date_deb = min(date_deb1, date_deb2)

    if (date_deb == date_fin):
        date_fin = add_one_day(date_fin)

    return date_deb, date_fin


# def addBands(image, band, new_band_name, old_band_name='constant'):
#     """ Add a band to an image
#         Rename the first band name matching to the "old_band_name" by the new name
#     Arguments:
#         :param image: Image to add bands
#         :param band: Band to add
#         :param new_band_name: Name for the band to add
#         :param old_band_name='constant': default name 
#     """
#     image = image.addBands(band)
#     new_band_names = image.bandNames().replace(old_band_name, new_band_name)
#     return image.select(image.bandNames(), new_band_names)


def add_row(df, row):
    """ Add a row at the end of the dataframe
    Arguments
        :param df: dataframe
        :param row: row to add
    """
    df.loc[-1] = row
    df.index = df.index + 1
    return df.sort_index()


# Progress bar
def startProgress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-" * 50 + "]" + chr(8) * 51)
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


def splitH5File(filename, output_f1="new_file_part1.h5", output_f2="new_file_part2.h5"):
    """
    Split the .h5 file in two files (same size)
    Argument: filename
        param filename: file name
        :param output_f1="new_file_part1.h5": 
        :param output_f2="new_file_part2.h5": 
    """
    with h5py.File(filename, 'r') as f_old:
        nb_rows = f_old["longitude"].shape[0]
        keys = list(f_old.keys())

        key_copy_all = ['band', 'class_ids', 'class_names']
        key_copy_part = ['latitude', 'longitude', 'granule_id', 'product_id',
                         'classes']

        with h5py.File(output_f1, 'w') as f_new:
            for key in keys:
                if key in key_copy_all:
                    f_new.create_dataset(key, data=f_old[key])
                elif key in key_copy_part:
                    f_new.create_dataset(key, data=f_old[key][:nb_rows//2])

        with h5py.File(output_f2, 'w') as f_new:
            for key in keys:
                if key in key_copy_all:
                    f_new.create_dataset(key, data=f_old[key])
                elif key in key_copy_part:
                    f_new.create_dataset(key, data=f_old[key][nb_rows//2:])


def export_df_to_excel(df, sheetname, filename="Data/results.xlsx"):
    """
    Export the dataframe to excel in a specific sheet
    Arguments:
        :param df: 
        :param sheetname: 
        :param filename="Data/results.xlsx": 
    """
    from openpyxl import load_workbook
    book = load_workbook(filename)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer, sheet_name=sheetname, index=False)


def export_df_train_eval_to_excel(df_training, df_evaluation, filename="Data/results.xlsx"):
    """
    Export the dataframe to excel in two sheets
    Arguments:
        :param df_training: Training dataframe
        :param df_evaluation: Evaluation dataframe
        :param filename="Data/results.xlsx": output excel file name
    """
    import xlsxwriter
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_training.to_excel(writer, sheet_name="Training", index=False)
        df_evaluation.to_excel(writer, sheet_name="Evaluation", index=False)
        writer.save()


def mergeTrainingDataset():
    df1 = pd.read_excel(
        "./Data/results - JH.xlsx", "Training")
    df2 = pd.read_excel(
        "./Data/results - PC-ALEX.xlsx", "Training")

    # Fusion
    df = df1.append(df2)

    # Split rows having -1 as values
    valid_pixels = (df == -1).any(axis=1)
    df_invalid = df[valid_pixels]
    df_valid = df[~valid_pixels]

    print("nb pixels invalid: ", df_invalid.shape[0])
    print("nb pixels valid: ", df_valid.shape[0])

    export_df_to_excel(df_valid, "Training", filename="Data/results.xlsx")
    export_df_to_excel(df_invalid, "Invalids_training",
                       filename="Data/results.xlsx")


def mergeEvalDataset():
    df = pd.read_excel("./Data/Evaluation.xlsx", "Evaluation")

    # Split rows having -1 as values
    valid_pixels = (df == -1).any(axis=1)
    df_invalid = df[valid_pixels]
    df_valid = df[~valid_pixels]

    print("nb pixels invalid: ", df_invalid.shape[0])
    print("nb pixels valid: ", df_valid.shape[0])

    export_df_to_excel(df_valid, "Evaluation", filename="Data/results.xlsx")
    export_df_to_excel(df_invalid, "Invalids_evaluation",
                       filename="Data/results.xlsx")


def deletefile(filename):
    """ Delete the current file if existing
    Arguments
        :param filename: file to delete
    """
    import os
    if os.path.exists(filename):    # If file existing
        os.remove(filename)         # Delete file
