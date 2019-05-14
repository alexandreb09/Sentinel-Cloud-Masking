##########################################
#           Module import                #
##########################################

import ee
from datetime import datetime
from IPython.display import Image, display, HTML
from ee_ipl_uv_perso import multitemporal_cloud_masking
from ee_ipl_uv_perso import download
from ee_ipl_uv_perso import perso
from ee_ipl_uv_perso import perso_display
from ee_ipl_uv_perso import perso_tree
from ee_ipl_uv_perso.perso_parameters import *
from ee_ipl_uv_perso.perso_luigi_utils import cleanScreen
import os
import requests
import matplotlib.pyplot as plt

cleanScreen()

ee.Initialize()



##########################################
#            Data imports                #
##########################################

# Image Number analyzed
image_number = 1

# Define area of interest
region_of_interest = ee.Geometry.Polygon(GEOMETRY_PER_IMAGE.get(image_number))

# Select image to remove clouds
image_predict_clouds = ee.Image(IMAGE_NAMES.get(image_number))

# Get image date
datetime_image = datetime.utcfromtimestamp(image_predict_clouds.get("system:time_start") \
                                                                .getInfo() / 1000) \
                                                                .strftime("%Y-%m-%d %H:%M:%S")

"""
# Ajout NDVI
image_predict_clouds = add_ndvi_bands(image_predict_clouds)
image_predict_clouds = add_evi_bands(image_predict_clouds)
image_predict_clouds = rename_bands_ft(image_predict_clouds)
"""


# Visualize area of interest
imageRGB = image_predict_clouds.visualize(max=8301,
                                          min=-1655,
                                          bands=[RED, GREEN, BLUE])


image_file_original = download.MaybeDownloadThumb(imageRGB.clip(region_of_interest),
                                                  params={"dimensions": IMAGE_DIM})
                                                  
#################################
#     Visualization Image       #
#################################
def viz_cloudscore_mask(cloudscoremask):
    cloudscoremask_vis = cloudscoremask.updateMask(cloudscoremask)
    cloudscoremask_vis = cloudscoremask_vis.visualize(max=1,
                                                      min=0,
                                                      palette=['1f77b4', 'ff7f0e'])
    mosaic = ee.ImageCollection([imageRGB, cloudscoremask_vis]).mosaic()
    return download.MaybeDownloadThumb(mosaic.clip(region_of_interest),params={"dimensions": "400x400"})

##############################
#     Persistence method     #
##############################
"""
cloud_score_persistence, pred_persistence = multitemporal_cloud_masking. \
                            CloudClusterScore(image_predict_clouds, \
                                                region_of_interest, \
                                                method_pred="percentile")
"""

##############################
#       Tree Methods         #
##############################
tree_mask1 = perso_tree.getMaskTree1(image_predict_clouds)
tree_mask2 = perso_tree.getMaskTree2(image_predict_clouds)
tree_mask3 = perso_tree.getMaskTree3(image_predict_clouds)
GEE_mask4 = perso.getMaskGEE(image_predict_clouds)


##############################
#         Display            #
##############################
"""
persistence_pred_file = download.MaybeDownloadThumb(pred_persistence.clip(region_of_interest),
                                                   params={"dimensions": "400x400",
                                                           "bands":"B4_forecast,B3_forecast,B2_forecast",
                                                           "max":8301,
                                                           "min":-1655})
"""

list_images_show = [[ image_file_original, "Image analyzed"],
                   # [ viz_cloudscore_mask(cloud_score_persistence), "Percentile"],
                    [ viz_cloudscore_mask(tree_mask1), "Tree mask 1"],
                    [ viz_cloudscore_mask(tree_mask2), "Tree mask 2"],
                    [ viz_cloudscore_mask(tree_mask3), "Tree mask 3"],
                   # [ viz_cloudscore_mask(GEE_mask4), "Google Earth Engine Mask"]
                   ]


title = 'Cloud masking : tree methods\n Image number: ' + \
    str(image_number) + ' - date: ' + datetime_image[:10]
perso_display.affichage(list_images_show, graph_title=title, number_of_row=2, number_of_col=2)

