# from Methods_cloud_masking.perso_tree import getMaskTree1
from Upload_Data.linkh5_to_image import getDataFromH5File
import ee

ee.Initialise()

filename = 'Upload_Data/Data/20170523_s2_manual_classification_data.h5'


if __name__ == "__main__":

    data, df = getDataFromH5File(filename)

    list_image_id_df = np.unique(df[["id_GEE"]])
    print(list_image_id_df)
