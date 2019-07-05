import normalization
from parameters import PARAMS_CLOUDCLUSTERSCORE_DEFAULT
import ee

BANDS_MODEL = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']


def SelectClusters(image,
                   background_prediction,
                   result_clustering,
                   n_clusters,
                   bands_thresholds=["B2", "B3", "B4"],
                   region_of_interest=None,
                   tileScale=PARAMS_CLOUDCLUSTERSCORE_DEFAULT['tileScale']):
    """
    Function that contains the logic to create the cluster score mask. given the clustering result.

    :param bands_thresholds:
    :param background_prediction:
    :param image:
    :param result_clustering:
    :param n_clusters:
    :param region_of_interest:
    :return:
    """
    bands_norm_difference = [b + "_difference" for b in bands_thresholds]

    img_joined = image.subtract(background_prediction)\
                      .select(bands_thresholds, bands_norm_difference)\
                      .addBands(image.select(bands_thresholds))

    bands_and_difference_bands = bands_thresholds + bands_norm_difference

    multitemporal_score = None
    reflectance_score = None

    for i in range(n_clusters):
        img_diff_clus = img_joined.updateMask(
            result_clustering.eq(i)).select(bands_and_difference_bands)

        clusteri = img_diff_clus.reduceRegion(ee.Reducer.mean(),
                                              geometry=region_of_interest,
                                              bestEffort=True,
                                              scale=30,
                                              tileScale=tileScale
                                              )
        
        # print(clusteri.getInfo())
        # clusteri = ee.Algorithms.If(ee.Algorithms.IsEqual(clusteri, None), 0, clusteri)
        clusteri_diff = clusteri.toArray(bands_norm_difference)
        clusteri_refl = clusteri.toArray(bands_thresholds)
        
        clusteri_refl_norm = clusteri_refl.multiply(clusteri_refl).reduce(ee.Reducer.mean(),
                                                                          axes=[0]).sqrt().get([0])

        clusteridiff_mean = clusteri_diff.reduce(ee.Reducer.mean(), axes=[0]).get([0])
        clusteridiff_norm = clusteri_diff.multiply(clusteri_diff).reduce(ee.Reducer.mean(),
                                                                         axes=[0]).sqrt().get([0])

        multitemporal_score_clusteri = ee.Algorithms.If(clusteridiff_mean.gt(0),
                                                        clusteridiff_norm,
                                                        clusteridiff_norm.multiply(-1))

        multitemporal_score_clusteri = result_clustering.eq(
            i).toFloat().multiply(ee.Number(multitemporal_score_clusteri))
        reflectance_score_clusteri = result_clustering.eq(
            i).toFloat().multiply(ee.Number(clusteri_refl_norm))

        if multitemporal_score is None:
            multitemporal_score = multitemporal_score_clusteri
            reflectance_score = reflectance_score_clusteri
        else:
            multitemporal_score = multitemporal_score.add(
                multitemporal_score_clusteri)
            reflectance_score = reflectance_score.add(
                reflectance_score_clusteri)

    return multitemporal_score, reflectance_score


def ClusterClouds(image,
                  background_prediction,
                  threshold_dif_cloud=.045,
                  do_clustering=True, numPixels=1000,
                  threshold_reflectance=.175,
                  bands_thresholds=["B2", "B3", "B4"],
                  growing_ratio=2,
                  n_clusters=10, region_of_interest=None,
                  tileScale=PARAMS_CLOUDCLUSTERSCORE_DEFAULT['tileScale'],
                  band_name= None):
    """
    Function that compute the cloud score given the differences between the real and predicted image.

    :param growing_ratio:
    :param bands_thresholds:
    :param threshold_reflectance:
    :param do_clustering:
    :param background_prediction:
    :param image:
    :param img_differences: image_real - image_pred
    :param threshold_dif_cloud: Threshold over the cloud score to be considered clouds
    :param threshold_dif_shadow:Threshold over the cloud score to be considered shadows
    :param n_clusters: number of clusters
    :param numPixels:  to be considered by the clustering algorithm
    :param region_of_interest:  region of interest within the image
    :param band_name: name of output band (optional)
    :return: ee.Image with 0 for clear pixels, 1 for shadow pixels and 2 for cloudy pixels
    """

    img_differences = image.subtract(background_prediction)
    img_differences = img_differences.select(BANDS_MODEL)

    if do_clustering:
        training = img_differences.sample(region=region_of_interest,
                                        scale=30, numPixels=numPixels,
                                        tileScale=tileScale
                                        )

        training, mean, std = normalization.ComputeNormalizationFeatureCollection(training,
                                                                                BANDS_MODEL)
        clusterer = ee.Clusterer.wekaKMeans(n_clusters).train(training)
        # print("mean: ", mean.getInfo())
        # print("std: ", std.getInfo())
        img_differences_normalized = normalization.ApplyNormalizationImage(img_differences,
                                                                           BANDS_MODEL,
                                                                           mean, std)
        # print(img_differences_normalized.getInfo())
        result = img_differences_normalized.cluster(clusterer)


        multitemporal_score, reflectance_score = SelectClusters(image, background_prediction,
                                                                result, n_clusters, bands_thresholds,
                                                                region_of_interest,
                                                                tileScale=tileScale
                                                                )

    else:
        arrayImageDiff = img_differences.select(bands_thresholds).toArray()
        arrayImage = image.select(bands_thresholds).toArray()

        arrayImageDiffmean = arrayImageDiff.arrayReduce(ee.Reducer.mean(), axes=[0])\
                                           .gte(0).arrayGet([0])
        arrayImageDiffnorm = arrayImageDiff.multiply(arrayImageDiff)\
                                           .arrayReduce(ee.Reducer.mean(), axes=[0])\
                                           .sqrt().arrayGet([0])

        arrayImagenorm = arrayImage.multiply(arrayImage) \
                                   .arrayReduce(ee.Reducer.mean(), axes=[0])\
                                   .sqrt().arrayGet([0]) \

        reflectance_score = arrayImagenorm

        multitemporal_score = arrayImageDiffnorm.multiply(arrayImageDiffmean)

    # Apply thresholds
    if threshold_reflectance <= 0:
        cloud_score_threshold = multitemporal_score.gt(threshold_dif_cloud)
    else:
        cloud_score_threshold = multitemporal_score.gt(threshold_dif_cloud)\
                                                   .multiply(reflectance_score.gt(threshold_reflectance))

    # apply opening
    kernel = ee.Kernel.circle(radius=growing_ratio)
    cloud_score_threshold = cloud_score_threshold.focal_min(kernel=kernel).\
        focal_max(kernel=kernel)

    # Rename band name
    if band_name:
        cloud_score_threshold = cloud_score_threshold.select(
            [cloud_score_threshold.bandNames().get(0)], [band_name])
    return cloud_score_threshold
