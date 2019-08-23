#################################################################
# Parameters "interpolation" and exportation                    #
#################################################################

# Sentinel collection
sentinel_coll_name = "COPERNICUS/S2"

# Time windows interpolation
date_start = '2018-02-01'
date_end = '2018-11-30'

# Number of days subtracted before the starting date and added after the end date
day_gap_before = 30
day_gap_after = 30

# The dependent variable we are modeling(only "NDVI" is supported)
dependent = 'NDVI'

# The number of cycles on the daterange to model.
harmo_10 = 10
harmo_5 = 5
harmo_1 = 1

# Bands exported
bands = ["NDVI", "NDVI_final", "quality"]

# ROI to filter images
ROI = [[[-3.7161555256421934, 57.10487686990405],
        [-3.9139094318921934, 56.9119504742678],
        [-3.2272639240796934, 56.85943339198275],
        [-2.9855647053296934, 57.10487686990405]]]

# Provide a string to a specific land geometry
# The string is the path to a GEE feature Collection
# If no land_geometry specified (set to None), the 'ROI'
# is used to clip the output image
land_geometry = "users/ab43536/UK_border"


# JSON file of already exported images
#   - Path the json file: if some images already exported: set the path
#                         else: set it to None
#   - This argument is design to do not process already processed images
#     (after exportation)
#   - Must be set to None if ignored
JSON_FILE = None
# JSON_FILE = ".\Interpolation\Data\Metadata_NDVI_images.json"


# GEE folder where the images are stored
# The images contained in this folder are ignored (not processed again)
folder_GEE = 'users/ab43536/interpolation'


# Logging path
log_path = "./Interpolation/logs/logs.log"