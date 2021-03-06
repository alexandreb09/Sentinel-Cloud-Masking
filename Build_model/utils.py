#########################################################
# Utils file                                            #
#                                                       #
# Methods:                                              #
#       - getDates(granule)                             #
#       - splitH5File(filename, output_f1, output_f2)   #
#       - export_df_to_excel(df, sheetname, filename)   #
#       - export_df_train_eval_to_excel(df_training,    #
#                                       df_evaluation,  #
#                                       filename)       #
#       - mergeTrainingDataset(output_file)             #
#       - mergeEvalDataset(file_source, file_out)       #
#       - add_row(df, row)                              #
#       - deletefile(filename)                          #
#                                                       #
#       - startProgress(title)                          #
#       - progress(x)                                   #
#       - endProgress()                                 #
#########################################################

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
        :return: begining date and finishing date
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
    date_start1 = format_date(details[7][1:9])
    date_start2 = format_date(details[8][:8])
    date_deb = min(date_start1, date_start2)

    if (date_deb == date_fin):
        date_fin = add_one_day(date_fin)

    return date_deb, date_fin


def splitH5File(filename, output_f1="new_file_part1.h5", output_f2="new_file_part2.h5"):
    """
    Split the .h5 file in two files (same size)
    Using one single file was too slow...
    Argument: 
        :param filename: file name
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


#################################################
#              Pandas exports                   #
#################################################

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


def mergeTrainingDataset(output_file="Data/results.xlsx"):
    """ Split data into valid and invalid sheet
        Used for TRAINING dataset
        A "-1" means the method failed
    Arguments:
        :param file_source="./Data/Evaluation.xlsx": source file
        :param file_out="Data/results.xlsx": output file
    """
    # Read 2 files
    df1 = pd.read_excel("./Data/results - JH.xlsx", "Training")
    df2 = pd.read_excel("./Data/results - PC-ALEX.xlsx", "Training")

    # Fusion
    df = df1.append(df2)

    # Filter rows having at least one "-1" as values
    # "-1" meens the method failed
    valid_pixels = (df == -1).any(axis=1)
    df_invalid = df[valid_pixels]
    df_valid = df[~valid_pixels]

    print("nb pixels invalid: ", df_invalid.shape[0])
    print("nb pixels valid: ", df_valid.shape[0])

    export_df_to_excel(df_valid, "Training", filename=output_file)
    export_df_to_excel(df_invalid, "Invalids_training", filename=output_file)


def mergeEvalDataset(file_source="./Data/Evaluation.xlsx", file_out="Data/results.xlsx"):
    """ Split data into valid and invalid sheet
        Used for EVALUATION dataset (same function as "mergeTrainingDataset")
        A "-1" means the method failed
    Arguments:
        :param file_source="./Data/Evaluation.xlsx": source file
        :param file_out="Data/results.xlsx": output file
    """

    df = pd.read_excel(file_source, "Evaluation")

    # Filter rows having at least one "-1" as values
    # "-1" meens the method failed
    valid_pixels = (df == -1).any(axis=1)
    df_invalid = df[valid_pixels]
    df_valid = df[~valid_pixels]

    print("nb pixels invalid: ", df_invalid.shape[0])
    print("nb pixels valid: ", df_valid.shape[0])

    export_df_to_excel(df_valid, "Evaluation", filename=file_out)
    export_df_to_excel(df_invalid, "Invalids_evaluation", filename=file_out)


#############################################
#                   Others                  #
#############################################

def add_row(df, row):
    """ Add a row at the end of the dataframe
    Arguments
        :param df: dataframe
        :param row: row to add
    """
    df.loc[-1] = row
    df.index = df.index + 1
    return df.sort_index()


def deletefile(filename):
    """ Delete the current file if existing
    Arguments
        :param filename: file to delete
    """
    import os
    if os.path.exists(filename):    # If file existing
        os.remove(filename)         # Delete file


#################################################
#                Progress bar                   #
#################################################
# Create a progress ba r in terminal
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
