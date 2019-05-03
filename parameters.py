################################
#       Parameters             #
################################

#Bands names for Sentinel2
SENTINEL2_BANDNAMES: list = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12', 'QA60']

RED: str = 'B4'
GREEN: str = 'B3'
BLUE: str = 'B2'
NIR: str = 'B8'
IMAGE_DIM: str = "400x400"


# Default parameters for cloud clustering
PARAMS_CLOUDCLUSTERSCORE_DEFAULT: dict = {"threshold_cc": 10,
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
                                        "bands_thresholds": ["B2", "B3", "B4"],
                                        }


CC_IMAGE_TOP = .6


