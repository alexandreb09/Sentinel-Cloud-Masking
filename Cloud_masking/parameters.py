#################################################
#                PARAMETER FILE                 #
# Contains all the parameters of the model      #
#################################################

#Bands names for Sentinel2
SENTINEL2_BANDNAMES: list = ['B1' , 'B2' , 'B3' , 'B4'  , 'B5',
                             'B6' , 'B7' , 'B8' , 'B8A' , 'B9',
                             'B10', 'B11', 'B12', 'QA60']


#########################
# Tree methods          #
#########################
# Reduction coefficient used to normalized the sentinel band values
# according to the article values (coeff 10 000)
COEF_NORMALISATION: int = 10000


#########################
# RandomForest Model    #
#########################
# Number of tree in the forest
NUMBER_TREES: int = 500
# random forest model cuttof
CUTTOF: int = 0.29


#########################
# Background methods    #
#########################
# Parameter Background selection
PARAMS_SELECTBACKGROUND_DEFAULT: dict = {
    # Number of image used to build the background
    "number_of_images": 20,
    # Number of image for candicate images (method 5)
    "number_preselect": 40,
    # Allow select background image in futur 
    "allow_future": True,
}

# Default parameters for cloud clustering
# Sames as used in this article: https://www.mdpi.com/2072-4292/10/7/1079
PARAMS_CLOUDCLUSTERSCORE_DEFAULT: dict = {
    "sampling_factor": .05,
    "lmbda": 1e-6,
    "gamma": 0.01,
    "trainlocal": True,
    "with_task": True,
    "with_cross_validation": False,
    "threshold_dif_cloud": .04,
    "threshold_reflectance": .175,
    "do_clustering": True,
    "numPixels": 5000,
    "n_clusters": 10,
    "growing_ratio": 2,
    "bands_thresholds": ["B4", "B3", "B2"],
    "tileScale": 2,
}


# Filter date from same date e.g. remove dates between image date + or - n hours
# Number of hours:
NUMBER_HOURS: int = 18

# Filter image with differents shapes
# Ratio of commun area
COMMON_AREA: int = 0.95
