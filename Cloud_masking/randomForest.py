

# Import modules
import ee               # GEE
import sys, os          # Set file path
import time             # Sleep between task running

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))


from Utils.utils import getGeometryImage, get_name_collection, export_image
from Utils.utils_tasks import getNumberActiveTask
from Tree_methods.tree_methods import getMaskTree1, getMaskTree2, getMaskTree3
from Background_methods.multitemporal_cloud_masking import CloudClusterScore
from parameters import date_start, date_end, geometry, NUMBER_TREES, CUTTOF

ee.Initialize()


# number image skipped
skipped = 10000



def computeCloudMasking(image_name, numberOfTrees=NUMBER_TREES, threshold=CUTTOF):
    """ Compute the Cloud masking 
        Methods used: 'percentile1', 'percentile5', 'tree2', 'tree3'
    Arguments:
        :param image_name: string image name
        :param numberOfTrees=NUMBER_TREE: Size of forest in randomForest model
        :param threshold=CUTTOF: RandomForest model cuttof
        :return: one binary image: 0 cloud free, 1 cloudy
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


def process_and_store_to_GEE(date_start=date_start, date_end=date_end, geometry=geometry,
                             folder='users/ab43536/default_name', skipped=0,
                             nb_task_max=2):
    # Cast to GEE object
    geometry = ee.Geometry.Polygon(geometry)

    # Get Sentinel ImageCollection according to filters
    col = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(date_start, date_end) \
            .filterBounds(geometry)

    # Remove the `skipped` first image if specified
    if skipped > 0:
        col = ee.ImageCollection(col.toList(col.size().getInfo() - skipped, skipped ))

    # Get all image name as a python list (string)
    image_names = get_name_collection(col).getInfo()
    total = len(image_names) + skipped

    # If imageCollection do not exist: create one
    if folder not in [elt["id"] for elt in ee.data.getList({"id":'/'.join(folder.split('/')[:-1])})]:
        ee.data.createAsset({'type': "ImageCollection"}, folder)

    k = 0
    while len(image_names) > 0:
        nb_task_pending = getNumberActiveTask()

        if nb_task_pending < nb_task_max:
            new_images = nb_task_max - nb_task_pending
            # Select the n first images
            image_running = image_names[:new_images]
            # Remove them from image to run
            image_names = image_names[new_images:]

            for name in image_running:
                i = k + skipped
                print("{:4d}/{} = {:05.2f}%   Image {}".format(i, total, i / total * 100, name))
                mask = computeCloudMasking(name)
                mask = mask.set('number', i)
                export_image(image=mask, asset_id=folder, roi=getGeometryImage(ee.Image(name)),
                                name=name.split('/')[-1], num=i, total=total)
                
                k += 1
                
        time.sleep(30)


if __name__ == "__main__":
    process_and_store_to_GEE()
