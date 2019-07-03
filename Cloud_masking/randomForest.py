import ee
import sys, os          # Set file path
from geetools import batch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'Tree_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Background_methods'))
sys.path.append(os.path.join(BASE_DIR, 'Utils'))


from Utils.utils import getGeometryImage
from Tree_methods.tree_methods import getMaskTree1, getMaskTree2, getMaskTree3
from Background_methods.multitemporal_cloud_masking import CloudClusterScore

ee.Initialize()


def computeCloudMasking(image_name, numberOfTrees=100, threshold=0.5, asset_id="default"):
    """ Compute the Cloud masking 
    Arguments:
        :param image_name: string image name
        :param numberOfTrees=100: Size of forest in randomForest model
        :param threshold=0.5: RandomForest model cuttof
        :param asset_id="default": Default asset id 
    """

    # Import training data as GEE object
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
    print(image.bandNames().getInfo())
    print(roi.getInfo())

    # Apply the different methods
    tree1 = getMaskTree1(image, roi)
    tree2 = getMaskTree2(image, roi)
    tree3 = getMaskTree3(image, roi)

    percentile1 = CloudClusterScore(image, roi, method_number=1)[0]
    percentile5 = CloudClusterScore(image, roi, method_number=5)[0]

    # Add each result as a band of the final image
    final_image = tree3.addBands([tree1, tree2, percentile1, percentile5])

    # Apply the random Forest classification
    masked_image = final_image.classify(randomForest).gt(threshold)

    export_image(masked_image, roi, name)

    return masked_image

def export_image(image, roi=None, name= None):
    if roi == None: roi = getGeometryImage(image)
    if name == None: name = image.id().getInfo()
    assetId = ee.String("users/ab43536/test_imgCol/").cat(name)
    # Create a task : export the result as image asset
    task = ee.batch.Export.image.toAsset(image=image.clip(roi),
                                         description="export image collection",
                                         assetId=assetId,
                                         scale=30,
                                         region=roi.coordinates().getInfo(),
                                         )
    task.start()




def toAsset(imageCol, assetPath, scale=30,
            verbose=False, **kwargs):
    """ Upload all images from one collection to a Earth Engine Asset.
    You can use the same arguments as the original function ee.batch.export.image.toDrive
    Arguments:
        :param imageCol: Collection to upload
        :type imageCol: ee.ImageCollection
        :param assetPath: path of the asset where images will go
        :type assetPath: str
        :param scale: scale of the image (side of one pixel). Defults to 30
            (Landsat resolution)
        :type scale: int
        :return: list of tasks
        :rtype: list
    """

    # size = imageCol.size().getInfo()
    alist = imageCol.toList(imageCol.size())
    tasklist = []

    for idx in range(0, 2):
        img = ee.Image(alist.get(idx))

        image_id = img.id().getInfo()
        assetId = "users/ab43536/mask_5_methods_collection/" + image_id
        
        region = getGeometryImage(img)

        task = ee.batch.Export.image.toAsset(image=img.clip(region),
                                             assetId="users/ab43536/mask_5_methods_collection/" + image_id,
                                             description=image_id.getInfo(),
                                             region=region.coordinates().getInfo(),
                                             scale=scale, **kwargs)
        task.start()
        tasklist.append(task)

        if verbose:
            print('Exporting {} to {}'.format(img.id(), assetId))

    return tasklist


# computeCloudMasking("COPERNICUS/S2/20180602T113321_20180602T113333_T30VVJ")

images_names = [
    'COPERNICUS/S2/20180602T113321_20180602T113333_T30VVJ',
    'COPERNICUS/S2/20180205T114351_20180205T114345_T30VUK',
    'COPERNICUS/S2/20180617T113319_20180617T113317_T30UVG',
    'COPERNICUS/S2/20180610T114349_20180610T114347_T30VUJ',
    'COPERNICUS/S2/20180116T114421_20180116T114418_T30VVH',
    'COPERNICUS/S2/20180225T105019_20180225T105018_T31TDJ',  # Toulouse
]


image_collection = ee.ImageCollection("COPERNICUS/S2").limit(2)

for name in images_names[1]:
    computeCloudMasking(ee.Image())

# image_collection_mask = image_collection.map(computeCloudMasking)

# for key, image_name in IMAGE_NAMES.items():
#     image_collection.merge(ee.ImageCollection(
#         computeCloudMasking(image_name, threshold=0.29, asset_id=key).clip(roi)))


# Create a task : export the result as image asset
# batch.imagecollection.toAsset(image_collection_mask,
#                      assetPath='users/ab43536/test',
#                     scale=30,
#                     )
