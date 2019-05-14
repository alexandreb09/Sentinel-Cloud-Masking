import pandas as pd
import h5py

filename = 'D:\\Users\\AB43536\\Python\\sentinel2_manual_classification_clouds\\20160914_s2_manual_classification_data.h5'
f = h5py.File(filename, 'r')

keys =  list(f.keys())
print( keys)

nb_rows = 20

"""
print("%6s %22s %5s" % ("Number", "key", "Type"))
for i, key in enumerate(keys):
    size = ""
    print("%2s: %25s %5s" % (str(i),  key, type(f[key][()]) ))
"""


data = f["class_names"]

print(data[:nb_rows])


df = pd.DataFrame({"class_id": f["classes"][:nb_rows],
                   "latitude": f["latitude"][:nb_rows],
                   "longitude": f["longitude"][:nb_rows],
                   })

def getNameClassFromId(row):
    return data[row / 10].decode("utf-8")
    
df["class_name"] = df["class_id"].apply(getNameClassFromId)

print(f["spectra"][()].shape)

bands = f["spectra"]

for i, band in enumerate(f["band"][:nb_rows]):
    df["B" + band.decode("utf-8")] = f["spectra"][:nb_rows, i]


print(df)
print(df.columns)