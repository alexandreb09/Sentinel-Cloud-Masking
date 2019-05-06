import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import ee_ipl_uv_perso.perso_parameters as param

IMAGE_PATH_INDEX = param.IMAGE_PATH_INDEX
IMAGE_TITLE_INDEX = param.IMAGE_TITLE_INDEX


def affichage(list_images_show, graph_title=None, number_of_row = 2, number_of_col = 3):
    """
    Display a list of images in matplotlib windows

    Arguments
        :param list_images_show: = [[path to image, image title], ... ]
        :param number_of_row=2: 
        :param number_of_col=3: 
    """

    fig = plt.figure()
    for i, image in enumerate(list_images_show):
        a = fig.add_subplot(number_of_row, number_of_col, i+1)
        plt.imshow(mpimg.imread(image[IMAGE_PATH_INDEX]))
        a.set_title(image[IMAGE_TITLE_INDEX])
        plt.axis('off')

    if graph_title:
        fig.suptitle(graph_title, fontsize=16)

    plt.show()
