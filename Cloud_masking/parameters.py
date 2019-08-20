#################################################
#                PARAMETER FILE                 #
# Contains all the parameters of the model      #
#                                               #
# Parameters:                                   #
#       - date_start                            #
#       - date_end                              #
#       - nb_days_before                        #
#       - nb_days_after                         #
#       - land_geometry                         #
#       - geometry                              #            
#       - COEF_NORMALISATION                    #
#       - NUMBER_TREES                          #
#       - CUTTOF                                #
#       - PARAMS_CLOUDCLUSTERSCORE_DEFAULT      #
#       - PARAMS_SELECTBACKGROUND_DEFAULT       #
#       - NUMBER_HOURS                          #
#       - COMMON_AREA                           #
#       - folder_GEE                            #
#       - nb_task_max                           #
#       - excel_file                            #
#       - SENTINEL2_BANDNAMES                   #
#       - LOG_FILE                              #
#################################################


# Parameters of the study
# Define DATE RANGE for the given analysis
date_start = "2018-01-01"
date_end = "2018-12-31"

# Define additional image in the date range
nb_days_before = 30
nb_days_after = 30

# Define the area of interest. Change these values according the area
# of interest (EPSG:3857). There are two parameters for the ROI:
#   - GEOMETRY: 
#       - a list of list of points: [[[x0, y0], [x1, y1], ... ]]
#       - This used to prevent GEE limitations. This geometry is firtly used to roughly
#         filter the Sentinel2 imageCollection according to the ROI. 
#         You can use the GEE Code Editor, draw a polygon on the map over 
#         the area of interest and copy past the coordinates.
#   - land_geometry:
#       - a string: a path to GEE Feature collection. Ex: "users/ab43536/UK_border"
#       - This is used to mask data outside. Usefull for masking ocean,
#         others country).
#       - If the image do not intersect the geometry, the image is ignored
#       - This can be a feature collection with quite a high resolution. The GEE Code Editor 
#         allows to import shapefile.

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
# https://www.mdpi.com/2072-4292/8/8/666
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
    # Pre filtering
    "number_preselect": 40,
    # Allow select background image in futur 
    "allow_future": True,
}

# Default parameters for cloud clustering
# Sames as used in this article: https://www.mdpi.com/2072-4292/10/7/1079
# The only change is the tileScale (counter GEE restriction)
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
# allowed images | -18h prohibited | IMAGE | 18h prohibited | allowed images
# Number of hours:
NUMBER_HOURS: int = 18

# Filter image with differents shapes
# Ratio of commun area used in the background selection
# (avoid having area with no data)
COMMON_AREA: int = 0.95


#########################################
#            Exportation                #
#########################################
# GEE folder where the images are stored
# The images contained in this folder are ignored (not processed again)
folder_GEE = 'users/ab43536/default_name'

# Number of GEE tasks running at the same time
# GEE restriction: must be below 3000
# Providing a high number is adding task in pending list
# but might be really boring to handle if the script fails
# The actual number of task processing at the same time is below 10
nb_task_max = 30

# Excel file create during the export process
# This file is used to avoid process images already processed
excel_file = "Interpolation/current_status.xlsx"

# JSON file of already processed images
#   - Path the json file created during the call of 'exportImageListToDrive'
#     from 'Cloud_masking/Utils/utils_assets.py' file
#   - This argument is design to do not process already processed images 
#     (after exportation)
#   - Must be set to None if ignored
JSON_FILE = ".\Cloud_masking\Data\Metadata_mask.json"

#########################################
#               Others                  #
#########################################
# Bands names for Sentinel2
SENTINEL2_BANDNAMES: list = ['B1', 'B2', 'B3', 'B4', 'B5',
                             'B6', 'B7', 'B8', 'B8A', 'B9',
                             'B10', 'B11', 'B12', 'QA60']

# Log File name
LOG_FILE: str = "logs/logs.log"
