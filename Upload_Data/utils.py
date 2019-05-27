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


def startProgress(title, i=1):
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
        key_copy_part = ['latitude', 'longitude', 'granule_id', 'product_id',
                         'classes']

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
                    f_new.create_dataset(key, data=f_old[key][nb_rows//2:])


def export_df_to_excel(df, sheetname, filename="Data/results.xlsx"):
    """
    Export the dataframe to excel in two sheets
    Arguments:
        :param df: dataframe to export
    """
    from openpyxl import load_workbook 
    book = load_workbook(filename)
    with pd.ExcelWriter(filename, engine = 'openpyxl') as writer:
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        # df.to_excel(writer, "Main", cols=['Diff1', 'Diff2'])
        df.to_excel(writer, sheet_name=sheetname, index=False)
        # writer.save()

def export_df_train_eval_to_excel(df_training, df_evaluation , filename="Data/results.xlsx"):
    """
    Export the dataframe to excel in two sheets
    Arguments:
        :param df: dataframe to export
    """
    import xlsxwriter
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_training.to_excel(writer, sheet_name="Training", index=False)
        df_evaluation.to_excel(writer, sheet_name="Evaluation", index=False)
        writer.save()
