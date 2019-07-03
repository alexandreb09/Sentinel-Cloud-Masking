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
from ee_ipl_uv_perso.perso_luigi_utils import cleanScreen
from ee_ipl_uv_perso.perso_parameters import GEOMETRY_PER_IMAGE, IMAGE_NAMES, RED, GREEN, BLUE, IMAGE_DIM
import os
import requests
import matplotlib.pyplot as plt

cleanScreen()

ee.Initialize()

method = "percentile"





def viz_cloudscore_mask(cloudscoremask, imageRGB, region_of_interest):
    cloudscoremask_vis = cloudscoremask.updateMask(cloudscoremask)
    cloudscoremask_vis = cloudscoremask_vis.visualize(max=1,
                                                      min=0,
                                                      palette=['1f77b4', 'ff7f0e'])
    mosaic = ee.ImageCollection([imageRGB, cloudscoremask_vis]).mosaic()
    return download.MaybeDownloadThumb(mosaic.clip(region_of_interest), params={"dimensions": IMAGE_DIM})




def iterate_over_all_image():
    for image_number in IMAGE_NAMES:

        # Select image to remove clouds
        image_predict_clouds = ee.Image(IMAGE_NAMES.get(image_number))

        region_of_interest = ee.Geometry.Polygon(
            GEOMETRY_PER_IMAGE.get(image_number))

        # Get image date
        datetime_image = datetime.utcfromtimestamp(image_predict_clouds.get("system:time_start")
                                                .getInfo() / 1000).strftime("%Y-%m-%d %H:%M:%S")

        # Visualize area of interest
        imageRGB = image_predict_clouds.visualize(max=8301,
                                                min=-1655,
                                                bands=[RED, GREEN, BLUE])
        image_file_original = download.MaybeDownloadThumb(imageRGB.clip(region_of_interest),
                                                        params={"dimensions": IMAGE_DIM})

        list_images_show = [[image_file_original, "Image analyzed"]]

        for i in range(1, 6):
            cloud_score_persistence, pred_persistence = multitemporal_cloud_masking. \
                CloudClusterScore(image_predict_clouds,
                                region_of_interest,
                                method_number=i,
                                method_pred=method)
            list_images_show.append(
                [viz_cloudscore_mask(cloud_score_persistence, imageRGB, region_of_interest), "method " + str(i)])


        filename = "ee_ipl_uv_" + str(method) + "_image" + str(image_number)
        title = 'Cloud masking : ee_ipl_uv - ' + method + ' methods\n Image number: ' + \
            str(image_number) + ' - date: ' + datetime_image[:10]
        perso_display.affichage(list_images_show, graph_title=title,
                                number_of_row=2, number_of_col=3, display=True,
                                filename=filename)


iterate_over_all_image()

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
