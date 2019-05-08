import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import ee_ipl_uv_perso.perso_parameters as param

IMAGE_PATH_INDEX = param.IMAGE_PATH_INDEX
IMAGE_TITLE_INDEX = param.IMAGE_TITLE_INDEX


def affichage(list_images_show, graph_title=None, number_of_row = 2, number_of_col = 3, save = False, display= True, filename="dafault.png"):
    """
    Display a list of images in matplotlib windows

    Arguments
        :param list_images_show: = [[path to image, image title], ... ]
        :param number_of_row=2: 
        :param number_of_col=3: 
    """



    for i, image in enumerate(list_images_show):
        plt.subplot(number_of_row, number_of_col, i+1)
        plt.title(image[IMAGE_TITLE_INDEX])
        plt.imshow(mpimg.imread(image[IMAGE_PATH_INDEX]))
        plt.axis('off')

        if graph_title:
            plt.suptitle(graph_title, fontsize=16)

    if display:
        plt.show()
    
    if save:
        plt.savefig(filename)

