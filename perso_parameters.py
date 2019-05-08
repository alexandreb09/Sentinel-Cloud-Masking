################################
#       Parameters             #
################################
import ee


#Bands names for Sentinel2
SENTINEL2_BANDNAMES: list = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12', 'QA60']

RED: str = 'B4'
GREEN: str = 'B3'
BLUE: str = 'B2'
NIR: str = 'B8'
IMAGE_DIM: str = "600x600"
DATASET_INDEX: str = "COPERNICUS/S2"


PARAMS_SELECTBACKGROUND_DEFAULT: dict = {
    "number_of_images": 3,
    "method_number": 1,
    "number_preselect": 20,
}

# Default parameters for cloud clustering
PARAMS_CLOUDCLUSTERSCORE_DEFAULT: dict = {
    "method": "persistence",
    "threshold_cc": 20,
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
    "bands_thresholds": [BLUE, GREEN, RED],
}

IMAGE_NAMES: dict = {
    1: DATASET_INDEX + '/' + '20180602T113321_20180602T113333_T30VVJ',
    2: DATASET_INDEX + '/' + '20180205T114351_20180205T114345_T30VUK',
    3: DATASET_INDEX + '/' + '20180617T113319_20180617T113317_T30UVG',
    4: DATASET_INDEX + '/' + '20180610T114349_20180610T114347_T30VUJ',
    5: DATASET_INDEX + '/' + '20180116T114421_20180116T114418_T30VVH',
    6: DATASET_INDEX + '/' + '20180225T105019_20180225T105018_T31TDJ',  # Toulouse
    
}

         
GEOMETRY_PER_IMAGE: dict = {
    1: [[[-4.02762316402640, 56.93400615151729],
         [-4.02762316402640, 56.76616719378319],
         [-3.70901964840140, 56.76616719378319],
         [-3.70901964840140, 56.93400615151729]]],
    2: [[[-5.44841045644614, 57.99011987698918],
         [-5.11839032278805, 57.99011987698918],
         [-5.11836267827789, 58.15273411306219],
         [-5.44843810095630, 58.15273411306219]]],
    3: [[[-3.56845074625948, 55.38009001245041],
         [-3.26054176053912, 55.38009001245041],
         [-3.26058232538923, 55.54270424755427],
         [-3.56841018140937, 55.54270424755427]]],
    4: [[[-5.75683651637632, 57.24983172804217],
         [-5.43347287138135, 57.24983172804217],
         [-5.43346655512959, 57.41244596473666],
         [-5.75684283262808, 57.41244596473666]]],
    5: [[[-3.91213328379978, 56.20591177031853],
         [-3.59762562761181, 56.20591177031851],
         [-3.59764662404563, 56.36852600663118],
         [-3.91211228736597, 56.36852600663118]]],
    6: [[[1.991123121473725, 43.84949756757253],
         [2.233692987043468, 43.84949756757257],
         [2.233492673922910, 44.01211174031321],
         [1.991323434594278, 44.01211174031321]]],
}

VIS_PARAM: dict = {'max': 4982.217205639574, 'min': -682.5583150226744}


CC_IMAGE_TOP = .6

# Index list access
IMAGE_PATH_INDEX = 0
IMAGE_TITLE_INDEX = 1
