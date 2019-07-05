#################################
#          Modules              #
#################################

import ee
from datetime import datetime
from IPython.display import Image, display,HTML
from ee_ipl_uv import multitemporal_cloud_masking
from ee_ipl_uv import download
import os
import requests

ee.Initialize()



#################################
#            DATA               #
#################################

# Image & dataset name 
image_index = "LC08_204020_20180704"          # Image to remove clouds
dataset_index = 'LANDSAT/LC08/C01/T1_TOA'     # Dataset containing picture

# Import Image from Google Earth Data
image_predict_clouds = ee.Image(dataset_index + '/' + image_index)  

# Area analyzed
region_of_interest = ee.Geometry.Polygon(
    [[[-2.775208282272615,57.01860739003285],
        [-2.453858184616365,57.01860739003285],
        [-2.453858184616365,57.18122162676308],
        [-2.775208282272615,57.18122162676308]]])

# Date of image analyzed
datetime_image = datetime.utcfromtimestamp(image_predict_clouds.get("system:time_start") \
                                                                .getInfo()/1000) \
                                                                .strftime("%Y-%m-%d %H:%M:%S")

#################################
#     Visualization Image       #
#################################
imageRGB = image_predict_clouds.visualize(max=.3,bands=["B4","B3","B2"])
image_file_original = download.MaybeDownloadThumb(imageRGB.clip(region_of_interest),params={"dimensions": "400x400"})

def viz_cloudscore_mask(cloudscoremask):
    cloudscoremask_vis = cloudscoremask.updateMask(cloudscoremask)
    cloudscoremask_vis = cloudscoremask_vis.visualize(max=1,min=0,palette=['1f77b4', 'ff7f0e'])
    mosaic = ee.ImageCollection([imageRGB, cloudscoremask_vis]).mosaic()
    return download.MaybeDownloadThumb(mosaic.clip(region_of_interest),params={"dimensions": "400x400"})


#################################
#     Méthod persistence        #
#################################
cloud_score_persistence, pred_persistence = multitemporal_cloud_masking.CloudClusterScore(image_predict_clouds,
                                                                                         region_of_interest,
                                                                                         method_pred="persistence")
persistence_pred_file = download.MaybeDownloadThumb(pred_persistence.clip(region_of_interest),
                                                   params={"dimensions": "400x400",
                                                           "bands":"B4_forecast,B3_forecast,B2_forecast",
                                                           "max":.3})
