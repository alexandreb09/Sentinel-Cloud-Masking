#####################################################
# File: Cloud masking model                         #
# Methods:                                          #
#   - computeCloudMasking(image_name,               #
#                         numberOfTrees,            #
#                         threshold)                #
# This mdethod is computing the full cloud mask     #
# for one image. This function can be run on one    #
# independant image                                 #
#####################################################

# Import modules
import ee               # GEE
import sys, os          # Set file path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))

from Utils.utils import getGeometryImage
from Tree_methods.tree_methods import getMaskTree1, getMaskTree2, getMaskTree3
from Background_methods.multitemporal_cloud_masking import CloudClusterScore
from parameters import NUMBER_TREES, CUTTOF
import parameters


def computeCloudMasking(image_name, numberOfTrees=NUMBER_TREES, threshold=CUTTOF):
    """ Compute the Cloud masking for a given image
        Methods used: 'percentile1', 'percentile5', 'tree2', 'tree3'
    Arguments:
        :param image_name: string image name
        :param numberOfTrees=NUMBER_TREE: Size of forest in randomForest model
        :param threshold=CUTTOF: RandomForest model cuttof
        :return: one binary image: 0 cloud free, 1 cloudy
    """

    # Import training data as GEE object
    # Build randomForest model at each run
    fc_training = ee.FeatureCollection(
        'ft:1XzZPz8HZMARKQ9OPTWvfuRkPaGIASzkRYMfhKT8H')

    # Use these methods for prediction.
    methods_name = ee.List(['percentile1', 'percentile5', 'tree2', 'tree3'])

    # Random Forest model
    randomForest = ee.Classifier.randomForest(numberOfTrees=numberOfTrees)
    randomForest = randomForest.train(fc_training, 'cloud', methods_name)

    # Image + region of interest
    image = ee.Image(image_name)
    roi = getGeometryImage(image)

    # UK BORDER <=> mask sea
    land_geometry = ee.FeatureCollection(parameters.land_geometry)
    # image = image.clip(land_geometry)

    # Apply the different methods
    # tree1 = getMaskTree1(image, roi)
    tree2 = getMaskTree2(image, roi)
    tree3 = getMaskTree3(image, roi)
    percentile1, percentile5 = CloudClusterScore(image, roi)

    # Add each result as a band of the final image
    final_image = tree3.addBands([tree2, percentile1, percentile5]) \
                        .clip(land_geometry)

    # Apply the random Forest classification
    masked_image = final_image.classify(randomForest) \
                              .gt(threshold)

    # Add meta data: geometry + date
    masked_image = masked_image.set("system:footprint", image.get('system:footprint'))
    masked_image = masked_image.set("system:time_start", image.get('system:time_start'))
    masked_image = masked_image.set("system:time_end", image.get('system:time_end'))

    return masked_image


