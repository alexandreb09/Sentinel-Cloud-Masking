##########################################
#           Module import                #
##########################################

import ee
from datetime import datetime
from IPython.display import Image, display, HTML
from Methods_cloud_masking import multitemporal_cloud_masking
from Methods_cloud_masking import download
from Methods_cloud_masking import perso
from Methods_cloud_masking import perso_display
from Methods_cloud_masking import perso_tree
from Methods_cloud_masking.perso_luigi_utils import cleanScreen, getGeometryImage
from Methods_cloud_masking.perso_parameters import GEOMETRY_PER_IMAGE, PARAMS_SELECTBACKGROUND_DEFAULT, \
                                            IMAGE_NAMES, RED, GREEN, BLUE, IMAGE_DIM
import os
import requests

# cleanScreen()

ee.Initialize()


##########################################
#            Data imports                #
##########################################

# Image Number analyzed
image_number = 1
method = "percentile"


# Select image to remove clouds
# image_predict_clouds = ee.Image(IMAGE_NAMES.get(image_number))
image_predict_clouds = ee.Image(
    "COPERNICUS/S2/20151209T111442_20151209T111442_T30UWB")
# image_predict_clouds = ee.Image("COPERNICUS/S2/20160205T103556_20160205T174515_T32TLR")

# Define area of interest
# region_of_interest = ee.Geometry.Polygon(GEOMETRY_PER_IMAGE.get(image_number))
region_of_interest = getGeometryImage(image_predict_clouds)

# Get image date
datetime_image = datetime.utcfromtimestamp(image_predict_clouds.get("system:time_start")
                                           .getInfo() / 1000).strftime("%Y-%m-%d %H:%M:%S")

list_images_show =[]
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


# image_file_original = download.MaybeDownloadThumb(imageRGB.clip(region_of_interest),
#                                                   params={"dimensions": IMAGE_DIM})

# list_images_show.append([image_file_original, "Image analyzed"])

#################################
#     Visualization Image       #
#################################


def viz_cloudscore_mask(cloudscoremask):
    cloudscoremask_vis = cloudscoremask.updateMask(cloudscoremask)
    cloudscoremask_vis = cloudscoremask_vis.visualize(max=1,
                                                      min=0,
                                                      palette=['1f77b4', 'ff7f0e'])
    mosaic = ee.ImageCollection([imageRGB, cloudscoremask_vis]).mosaic()
    return download.MaybeDownloadThumb(mosaic.clip(region_of_interest),
                                        params={"dimensions": IMAGE_DIM})


##############################
#     Persistence method     #
##############################

for i in range(3, 6):
    print("Method used : {0}_{1}".format(method, i))
    cloud_score_persistence, pred_persistence = multitemporal_cloud_masking. \
        CloudClusterScore(image_predict_clouds,
                          region_of_interest,
                          method_number=i,
                          method_pred=method)
    list_images_show.append(
        [viz_cloudscore_mask(cloud_score_persistence), "method " + str(i)])

"""
cloud_score_persistence, pred_persistence = multitemporal_cloud_masking. \
    CloudClusterScore(image_predict_clouds,
                      region_of_interest,
                      method_number=1,
                      method_pred="persistence")
"""

##############################
#       Tree Methods         #
##############################
"""
tree_mask1 = perso_tree.getMaskTree1(image_predict_clouds)
tree_mask2 = perso_tree.getMaskTree2(image_predict_clouds)
tree_mask3 = perso_tree.getMaskTree3(image_predict_clouds)
GEE_mask4 = perso.getMaskGEE(image_predict_clouds)

list_images_show.append([ viz_cloudscore_mask(tree_mask1), "Tree mask 1"])
list_images_show.append([ viz_cloudscore_mask(tree_mask2), "Tree mask 2"])
list_images_show.append([ viz_cloudscore_mask(tree_mask3), "Tree mask 3"])
list_images_show.append([ viz_cloudscore_mask(GEE_mask4), "Google Earth default mask"])
"""

##############################
#         Display            #
##############################
"""
persistence_pred_file = download.MaybeDownloadThumb(pred_persistence.clip(region_of_interest),
                                                   params={"dimensions": IMAGE_DIM,
                                                           "bands":"B4_forecast,B3_forecast,B2_forecast",
                                                           "max":8301,
                                                           "min":-1655})
"""

filename = "ee_ipl_uv_" + str(method) + "_image" + str(image_number)

title = 'Cloud masking : ee_ipl_uv - ' + method + ' methods\n Image number: ' + \
    str(image_number) + ' - date: ' + \
    datetime_image[:10] + "\nBackground built with " + \
    str(PARAMS_SELECTBACKGROUND_DEFAULT["number_of_images"]) + " images"
perso_display.affichage(list_images_show, graph_title=title,
                        number_of_row=2, number_of_col=3,
                        display=True)



        
