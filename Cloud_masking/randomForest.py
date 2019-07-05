import ee
import sys, os          # Set file path
from geetools import batch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))


from Utils.utils import getGeometryImage, get_name_collection
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
    fc_training = ee.FeatureCollection(
        'ft:1XzZPz8HZMARKQ9OPTWvfuRkPaGIASzkRYMfhKT8H')

    # Use these methods for prediction.
    methods_name = ee.List(['percentile1', 'percentile5', 'tree2', 'tree3'])  #

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

    return masked_image


def export_image(image, asset_id="users/ab43536/", roi=None, name=None, num=None, total=None):
    """ Export one image to asset
    Arguments
        :param image: image to export
        :param roi=None:  specify the roi, default compute from image dimension
        :param name=None: name of the image
    """
    if roi == None:
        roi = getGeometryImage(image)
    if name == None:
        name = image.id().getInfo()
    description = "Default export"
    if num != None and total != None:
        description = "Image {} on {} equal {:05.2f} pourcent".format(num, total, num / total * 100)
    # print(description)
    assetId = asset_id + name
    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toAsset(image=image.clip(roi),
                                         description=description,
                                         assetId=assetId,
                                         scale=30,
                                         region=roi.coordinates().getInfo(),
                                         )
    task.start()



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

image_names = get_name_collection(col).getInfo()
total = len(image_names)

folder = "users/ab43536/masks_4_methods"
if folder not in [elt["id"] for elt in ee.data.getList({"id": "users/ab43536"})]:
    ee.data.createAsset({'type': "ImageCollection"}, folder)

for i, name in enumerate(image_names):
    print("{:4d}/{} = {:05.2f}%   Image {}".format(i, total, i / total * 100, name))
    mask = computeCloudMasking(name)
    mask = mask.set('number', i)
    export_image(mask, folder, getGeometryImage(ee.Image(name)),
                 name.split('/')[-1], num=i, total=total)
