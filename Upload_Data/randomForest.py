
import ee
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from utils import addBands
from Methods_cloud_masking import download
from Methods_cloud_masking.multitemporal_cloud_masking import CloudClusterScore
from Methods_cloud_masking.perso_luigi_utils import getGeometryImage
from Methods_cloud_masking.perso_tree import getMaskTree1, getMaskTree2, getMaskTree3

ee.Initialize()

# Import training data as GEE object
fc_training = ee.FeatureCollection('ft:1XzZPz8HZMARKQ9OPTWvfuRkPaGIASzkRYMfhKT8H')


# Use these methods for prediction.
methods_name = ee.List(['percentile1', 'percentile2', 'percentile3', 'percentile4', 'percentile5',
                        'persistence1', 'persistence2', 'persistence3', 'persistence4', 'persistence4',
                        'tree1', 'tree2', 'tree3'])

# Random Forest model
numberOfTrees = 100
randomForest = ee.Classifier.randomForest(numberOfTrees=numberOfTrees)
randomForest = randomForest.train(fc_training, 'cloud' , methods_name)


# prediction = fc_eval.limit(100).classify(randomForest)

image = ee.Image("COPERNICUS/S2/20180602T113321_20180602T113333_T30VVJ")
roi = getGeometryImage(image)

persistence1 = CloudClusterScore(image, roi, method_pred="persistence", method_number=1)[0]
persistence2 = CloudClusterScore(image, roi, method_pred="persistence", method_number=2)[0]
persistence3 = CloudClusterScore(image, roi, method_pred="persistence", method_number=3)[0]
persistence4 = CloudClusterScore(image, roi, method_pred="persistence", method_number=4)[0]
persistence5 = CloudClusterScore(image, roi, method_pred="persistence", method_number=5)[0]

percentile1 = CloudClusterScore(image, roi, method_pred="percentile", method_number=1)[0]
percentile2 = CloudClusterScore(image, roi, method_pred="percentile", method_number=2)[0]
percentile3 = CloudClusterScore(image, roi, method_pred="percentile", method_number=3)[0]
percentile4 = CloudClusterScore(image, roi, method_pred="percentile", method_number=4)[0]
percentile5 = CloudClusterScore(image, roi, method_pred="percentile", method_number=5)[0]

tree1 = getMaskTree1(image)
tree2 = getMaskTree2(image)
tree3 = getMaskTree3(image)

# print(percentile1.bandNames().getInfo())
# print(percentile2.bandNames().getInfo())
# print(percentile3.bandNames().getInfo())
# print(percentile4.bandNames().getInfo())
# print(percentile5.bandNames().getInfo())
# print(persistence1.bandNames().getInfo())
# print(persistence2.bandNames().getInfo())
# print(persistence3.bandNames().getInfo())
# print(persistence4.bandNames().getInfo())
# print(persistence5.bandNames().getInfo())
# print(tree1.bandNames().getInfo())
# print(tree2.bandNames().getInfo())
# print(tree3.bandNames().getInfo())


final_image = persistence1.addBands([persistence2, persistence3, persistence4, persistence5])
print(final_image.bandNames().getInfo())
final_image = final_image.addBands([percentile1, percentile2, percentile3, percentile4, percentile5])
print(final_image.bandNames().getInfo())
final_image = final_image.addBands([tree1, tree2, tree3])
print(final_image.bandNames().getInfo())

imageRGB = image.visualize(max=8301, min=-1655, bands=["B4", "B3", "B2"])
# image_file_original = download.MaybeDownloadThumb(imageRGB.clip(roi),
#                                                   params={"dimensions": "600x600"})

def viz_cloudscore_mask(cloudscoremask):
    cloudscoremask_vis = cloudscoremask.updateMask(cloudscoremask)
    cloudscoremask_vis = cloudscoremask_vis.visualize(max=1,
                                                      min=0,
                                                      palette=['1f77b4', 'ff7f0e'])
    mosaic = ee.ImageCollection([imageRGB, cloudscoremask_vis]).mosaic()
    return download.MaybeDownloadThumb(mosaic.clip(roi), params={"dimensions": "600x600"})

print("Before classifier: ", image.bandNames().getInfo())
masked_image = final_image.classify(randomForest)

viz_cloudscore_mask(masked_image)
