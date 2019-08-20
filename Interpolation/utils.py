################################################
# Convert data from JS code Editor
# Clean up and summarize data in one excel file
################################################

import glob
from itertools import groupby
import pandas as pd


def keyf(text):
    return "_".join(text.split("\\")[-1].split("_")[:3])


list_file = glob.glob(r"Interpolation/Sample_data_Actual_fitted_NDVI/*.csv")
list_file_grouped = [list(items)
                     for gr, items in groupby(sorted(list_file), key=keyf)]

with pd.ExcelWriter('Interpolation/sample_data.xlsx') as writer:
    i = 0
    for filename in list_file_grouped:
        df = pd.read_csv(filename[0])
        df = pd.DataFrame()
        for sheet in filename:
            # print(sheet)
            col_name = sheet.split("_")[-1][:-4]
            df_cur = pd.read_csv(sheet)
            df_cur = pd.DataFrame({"NDVI" + col_name: eval(df_cur.NDVI.values[0]),
                                   col_name: eval(df_cur.fitted_name.values[0])})
            # print(df_cur)
            df = pd.concat([df, df_cur], axis=1)
        i += 1
        # print(df)
        df.to_excel(writer, sheet_name=keyf(filename[0]), index=False)
