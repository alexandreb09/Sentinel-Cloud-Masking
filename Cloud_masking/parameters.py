#################################################
#                PARAMETER FILE                 #
# Contains all the parameters of the model      #
#################################################

# Parameters of the study
# Define date range for the given analysis
date_start = "2018-01-01"
date_end = "2018-12-31"

# Define the area of interest. Change these values according the area
# of interest (EPSG:3857). The type can be:
#       - a list of points: [[[x0, y0], [x1, y1], ... ]]
#       - a string: a path to GEE Feature collection. This is usefull when using 
#                   country border. The border shapefile can be added to GEE Assets
#                   and then used by providing the path.
#                   Ex: geometry = "users/ab43536/UK_border"
# NOTE: providing a border is high consuming. It's

# geometry = [[[-0.18968822276610808, 61.70499236376784],
#              [-3.193305499581811, 59.73284719869931],
#              [-5.325089620808512, 59.58951641493764],
#              [-9.399354237873467, 57.845320092643185],
#              [-14.171772687416706, 57.82138467870956],
#              [-13.730329864317127, 57.34881400936257],
#              [-8.08648643189997, 57.30233012037025],
#              [-7.8217005199061305, 56.48359136715814],
#              [-6.763478605070759, 55.74630611995712],
#              [-8.614580937646224, 54.485756439010636],
#              [-7.468376415417879, 53.606034092022945],
#              [-4.639521093380836, 53.899696486437676],
#              [-6.7627523108039895, 49.728249042563874],
#              [-3.85768905856321, 49.954131633679516],
#              [1.5250388211492236, 50.85347177630827],
#              [2.1398276005526213, 52.76026102525827],
#              [-0.7924843140583562, 55.15337275817801],
#              [-1.9974803995539787, 56.29351938965108],
#              [-1.2901782736278165, 57.59091361215057],
#              [-2.8291194066866865, 58.05226927668464],
#              [-1.1716770318516865, 59.54786251775706],
#              [0.38660793514554825, 61.46785022032127]]]

# Land geometry (use to mask the ocean)
land_geometry = "users/ab43536/UK_border"

# Geometry that roughly overlays the UK (hands points)
geometry = [[[-1.5005188188386,  60.863047140476894],
             [-5.2798156938386,  58.92387273299673],
             [-8.0923156938386,  58.143979050956126],
             [-11.2563781938386, 53.4055338391001],
             [-10.7290344438386, 51.53191367679566],
             [-5.8071594438386,  49.63483372807331],
             [1.0483093061614,   50.537100502005416],
             [2.4545593061614,   52.34466616042596],
             [-0.9731750688386,  56.724942443535866],
             [-0.6216125688386,  60.648360105306814]]]



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


#########################################
#               Others                  #
#########################################
# Bands names for Sentinel2
SENTINEL2_BANDNAMES: list = ['B1', 'B2', 'B3', 'B4', 'B5',
                             'B6', 'B7', 'B8', 'B8A', 'B9',
                             'B10', 'B11', 'B12', 'QA60']

# Log File name
LOG_FILE: str = "logs.log"