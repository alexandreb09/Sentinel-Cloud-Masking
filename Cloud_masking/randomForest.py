
import ee
import sys, os          # Set file path
# from geetools import batch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))


from Utils.utils import getGeometryImage, get_name_collection, export_image
from Tree_methods.tree_methods import getMaskTree1, getMaskTree2, getMaskTree3
from Background_methods.multitemporal_cloud_masking import CloudClusterScore
from parameters import NUMBER_TREES, CUTTOF

ee.Initialize()


def computeCloudMasking(image_name, numberOfTrees=NUMBER_TREES, threshold=CUTTOF):
    """ Compute the Cloud masking 
    Arguments:
        :param image_name: string image name
        :param numberOfTrees=NUMBER_TREE: Size of forest in randomForest model
        :param threshold=CUTTOF: RandomForest model cuttof
    """

    # Import training data as GEE object
    # Build randomForest model at each run
    fc_training = ee.FeatureCollection('ft:1XzZPz8HZMARKQ9OPTWvfuRkPaGIASzkRYMfhKT8H')

    # Use these methods for prediction.
    methods_name = ee.List(['percentile1', 'percentile5', 'tree2', 'tree3'])  

    # Random Forest model
    randomForest = ee.Classifier.randomForest(numberOfTrees=numberOfTrees)
    randomForest = randomForest.train(fc_training, 'cloud', methods_name)

    # Image + region of interest
    image = ee.Image(image_name)
    roi = getGeometryImage(image)

    # Apply the different methods
    # tree1 = getMaskTree1(image, roi)
    tree2 = getMaskTree2(image, roi)
    tree3 = getMaskTree3(image, roi)
    percentile1, percentile5 = CloudClusterScore(image, roi)

    # Add each result as a band of the final image
    final_image = tree3.addBands([tree2, percentile1, percentile5])

    # Apply the random Forest classification
    masked_image = final_image.classify(randomForest).gt(threshold)

    # Add meta data
    masked_image = masked_image.set("system:footprint", image.get('system:footprint'))
    masked_image = masked_image.set("system:time_end", image.get('system:time_end'))
    masked_image = masked_image.set("system:time_start", image.get('system:time_start'))

    return masked_image


date_start = "2018-01-01"
date_end = "2018-12-31"
geometry = ee.Geometry.Polygon(
        [[[-1.5005188188386, 60.863047140476894],
          [-5.2798156938386, 58.92387273299673],
          [-8.0923156938386, 58.143979050956126],
          [-11.2563781938386, 53.4055338391001],
          [-10.7290344438386, 51.53191367679566],
          [-5.8071594438386, 49.63483372807331],
          [1.0483093061614, 50.537100502005416],
          [2.4545593061614, 52.34466616042596],
          [-0.9731750688386, 56.724942443535866],
          [-0.6216125688386, 60.648360105306814]]])


col = ee.ImageCollection("COPERNICUS/S2") \
        .filterDate(date_start, date_end) \
        .filterBounds(geometry)
        

# col = ee.ImageCollection(col.toList(col.size(), 1059))

# number image skipped
skipped = 10000

col = ee.ImageCollection(col.toList(col.size().getInfo() - skipped, skipped ))

image_names = get_name_collection(col).getInfo()
total = len(image_names) + skipped

folder = "users/ab43536/masks_4_methods"
if folder not in [elt["id"] for elt in ee.data.getList({"id": "users/ab43536"})]:
    ee.data.createAsset({'type': "ImageCollection"}, folder)

for k, name in enumerate(image_names):
    i = k + skipped
    print("{:4d}/{} = {:05.2f}%   Image {}".format(i, total, i / total * 100, name))
    mask = computeCloudMasking(name)
    mask = mask.set('number', i)
    export_image(image=mask, asset_id=folder, roi=getGeometryImage(ee.Image(name)),
                 name=name.split('/')[-1], num=i, total=total)
