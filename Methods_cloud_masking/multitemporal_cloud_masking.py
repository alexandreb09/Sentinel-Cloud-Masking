"""
Created on June 12, 2016

@author:  Gonzalo Mateo Garcia
@contact: gonzalo.mateo-garcia@uv.es

"""

import ee
import random
from Methods_cloud_masking import kernel
from Methods_cloud_masking import converters
from Methods_cloud_masking import time_series_operations
from Methods_cloud_masking import normalization
from Methods_cloud_masking import clustering
from Methods_cloud_masking.perso_parameters import SENTINEL2_BANDNAMES, \
                                             PARAMS_CLOUDCLUSTERSCORE_DEFAULT, \
                                             PARAMS_SELECTBACKGROUND_DEFAULT, \
                                             CC_IMAGE_TOP
from Methods_cloud_masking.perso import PredictPercentile, \
                                  PreviousImagesWithCCSentinel
import logging


logger = logging.getLogger(__name__)


class ModelCloudMasking:
    def __init__(self, img, bands, cloud_mask, max_lags,
                 region, seed=None, beta=None):
        """
        Class which implements linear and kernel models on Google Earth Engine
        for image forecasting as described in XXX paper

        :param img: to apply the model
        :type img: ee.Image
        :param bands: list with the names of the bands
        :type bands: list[str]
        :param cloud_mask: cloud_mask image to mask pixels for "estimation"
        :type cloud_mask: ee.Image
        :param max_lags: number of lags of the model
        :param beta: beta of the model (ponderate estimation vs prediction)
        :param region: geom to fit the model (model will be fitted only with pixels of this geom)

        :type region: ee.Geometry
        """
        self.img = img
        self.bands = bands
        self.cloud_mask = cloud_mask
        self.max_lags = max_lags
        self.region = region
        bands_modeling_estimation = list(self.bands)
        for lag in range(1, self.max_lags):
            bands_lag = list(map(lambda x: x + "_lag_" + str(lag), self.bands))
            bands_modeling_estimation.extend(bands_lag)
        self.bands_modeling_estimation = bands_modeling_estimation

        bands_modeling_prediction = []
        for lag in range(1, self.max_lags + 1):
            bands_lag = list(map(lambda x: x + "_lag_" + str(lag), self.bands))
            bands_modeling_prediction.extend(bands_lag)

        self.bands_modeling_prediction = bands_modeling_prediction
        self.bands_modeling_estimation_input = list(filter(lambda band: band.find("lag") != -1,
                                                           self.bands_modeling_estimation))
        self.bands_modeling_estimation_output = list(filter(lambda band: band.find("lag") == -1,
                                                            self.bands_modeling_estimation))

        self.bands_modeling_prediction_input = list(filter(lambda band: band.find("lag_1") == -1,
                                                           self.bands_modeling_prediction))
        self.bands_modeling_prediction_output = list(filter(lambda band: band.find("lag_1") != -1,
                                                            self.bands_modeling_prediction))
        if seed is None:
            self.seed = random.randint(0, 36000)
        else:
            self.seed = seed

        # Calculamos CC de la imagen actual
        dictio = self.cloud_mask.select([0], ["cloud"]).reduceRegion(reducer=ee.Reducer.mean(), geometry=region,
                                                                     bestEffort=True)
        self.cc_image = ee.Number(dictio.get("cloud")).getInfo()

        self.img_est = self.img.updateMask(self.cloud_mask.eq(0))
        self.img_est = self.img_est.select(self.bands_modeling_estimation)

        self.img_pred = self.img.select(self.bands_modeling_prediction)

        # Decrease beta linearly as the amount of cc_image increases
        if beta is None:
            self.beta = .5 - .5 * self.cc_image / CC_IMAGE_TOP
            self.beta = self.beta if self.beta > 0 else 0
        else:
            self.beta = beta

        self.alpha = None
        self.kernel_rbf = None
        self.gamma = None
        self.lmbda = None

        self.omega = None
        self.intercept = None

    def _BuildDataSet(self, sampling_factor,
                      normalize):

        estimation_set = self.img_est.sample(region=self.region,
                                             factor=sampling_factor,
                                             seed=self.seed)

        prediction_set = self.img_pred.sample(region=self.region,
                                              factor=sampling_factor,
                                              seed=self.seed)
        # Add weights
        estimation_set_size = ee.Number(estimation_set.size())
        prediction_set_size = ee.Number(prediction_set.size())
        peso_estimacion = ee.Number(self.beta).divide(estimation_set_size)
        peso_prediccion = ee.Number(1 - self.beta).divide(prediction_set_size)

        bands_modeling_estimation_input_weight = list(self.bands_modeling_estimation_input)
        bmp = list(self.bands_modeling_prediction)
        bmp.append("weight")
        bme = list(self.bands_modeling_estimation)
        bme.append("weight")

        estimation_set = estimation_set.map(
            lambda ft: ee.Feature(ft).set("weight", peso_estimacion))
        prediction_set = prediction_set.map(
            lambda ft: ee.Feature(ft).set("weight", peso_prediccion))
        bands_modeling_estimation_input_weight.append("weight")

        self.estimation_set = estimation_set
        self.prediction_set = prediction_set
        if (self.beta > 0) and (self.cc_image < CC_IMAGE_TOP):
            self.datos = estimation_set.merge(prediction_set.select(bmp,
                                                                    bme))
        else:
            logger.info("Using only prediction")
            self.datos = prediction_set.select(bmp,
                                               bme)
        if normalize:
            self.datos, self.inputs_mean, self.inputs_std = normalization.ComputeNormalizationFeatureCollection(
                self.datos, self.bands_modeling_estimation_input, only_center_data=False, weight="weight")
            self.datos, self.outputs_mean, self.outputs_std = normalization.ComputeNormalizationFeatureCollection(
                self.datos, self.bands_modeling_estimation_output, only_center_data=True, weight="weight")

            self.inputs_mean = self.inputs_mean.toArray(self.bands_modeling_estimation_input)
            self.inputs_std = self.inputs_std.toArray(self.bands_modeling_estimation_input)
            self.outputs_mean = self.outputs_mean.toArray(self.bands_modeling_estimation_output)

            # if "B10" in self.bands_modeling_estimation_output:
            #    self.datos.select("B10").divide(100)
            # if "B11" in self.bands_modeling_estimation_output:
            #    output_dataset["B11"] /= 100

        self.inputs = self.datos.select(bands_modeling_estimation_input_weight)
        self.outputs = self.datos.select(self.bands_modeling_estimation_output)

        return

    def TrainRBFKernelLocal(self, lmbda=.1, gamma=.5, sampling_factor=1. / 100.,
                            with_task=False, with_cross_validation=False):
        """
        Fit Kernelized RBF Ridge Regression to the current image subsampled. It downloads the data to
        fit. It uses sklearn.kernel_ridge library.

        :param lmbda: regularization factor
        :param gamma: gamma factor to build the kernel (https://en.wikipedia.org/wiki/Radial_basis_function_kernel)
        :param sampling_factor: percentage of pixels to sample to build the model
        :param with_cross_validation: donwload the data to fit the model with a task
        :param with_task: donwload the data to fit the model with a task

        :return:
        """

        from Methods_cloud_masking import model_sklearn
        best_params = None
        if not with_cross_validation:
            best_params = {"alpha": lmbda, "gamma": gamma}

        modelo = model_sklearn.KRRModel(best_params=best_params, verbose=1)
        self._BuildDataSet(sampling_factor, normalize=False)

        ds_total = converters.eeFeatureCollectionToPandas(self.datos,
                                                          self.bands_modeling_estimation + ["weight"],
                                                          with_task=with_task)

        logger.info("Size of downloaded ds: {}".format(ds_total.shape))

        output_mean, output_std = model_sklearn.fit_model_local(ds_total, modelo,
                                                                self.bands_modeling_estimation_input,
                                                                self.bands_modeling_estimation_output)

        if with_cross_validation:
            logger.info("Best params: {}".format(modelo.named_steps["randomizedsearchcv"].best_params_))
            ridge_kernel = modelo.named_steps["randomizedsearchcv"].best_estimator_
        else:
            ridge_kernel = modelo.named_steps["kernelridge"]

        # Copy model parameters
        self.gamma = ridge_kernel.gamma
        self.lmbda = ridge_kernel.alpha
        self.alpha = ee.Array(ridge_kernel.dual_coef_.tolist())  # column vector
        self.inputs_krr = ee.Array(ridge_kernel.X_fit_.tolist())

        self.distance_krr = kernel.RBFDistance(self.gamma)
        self.kernel_rbf = kernel.Kernel(self.inputs, self.bands_modeling_estimation_input,
                                        self.distance_krr,
                                        weight_property="weight")

        # Copy normalization stuff
        self.inputs_mean = ee.Array(modelo.named_steps["standardscaler"].mean_.tolist())
        self.inputs_std = ee.Array(modelo.named_steps["standardscaler"].scale_.tolist())
        self.outputs_mean = ee.Array(output_mean.tolist())
        self.outputs_std = ee.Array(output_std.tolist())

        return

    def TrainRBFKernelServer(self, lmbda=.1, gamma=50., sampling_factor=1. / 1000.):
        """
        Fit Kernelized RBF Ridge Regression to the current image on the server
        :param lmbda:
        :param gamma: gamma factor to build the kernel (https://en.wikipedia.org/wiki/Radial_basis_function_kernel)
        :param sampling_factor: percentage of pixels to sample to build the model
        :return:
        """
        self._BuildDataSet(sampling_factor, normalize=True)
        inputs = self.inputs
        outputs = self.outputs
        labels_input = self.bands_modeling_estimation_input
        labels_output = self.bands_modeling_estimation_output

        # Train
        self.distance_krr = kernel.RBFDistance(kernel.RBFDistance(gamma))
        self.gamma = gamma
        self.lmbda = lmbda
        self.kernel_rbf = kernel.Kernel(inputs, labels_input,
                                        self.distance_krr,
                                        weight_property="weight")

        outputs_eeArray = converters.eeFeatureCollectionToeeArray(outputs, labels_output)

        self.alpha = self.kernel_rbf.getAlphaeeArray(outputs_eeArray, lmbda)

    def _NormalizeImage(self, imagearray1D):
        if self.inputs_mean is not None:
            imagearray1D = imagearray1D.subtract(self.inputs_mean)

        if self.inputs_std is not None:
            imagearray1D = imagearray1D.divide(self.inputs_std)
        return imagearray1D

    def PredictRBFKernel(self):
        """
        Fit  KRR to the (subsampled) image and apply the model to the full image
         to obtain the forecasted image

        :return: forecasted image
        :rtype ee.Image
        """

        # Test
        image_test_input = self.img.select(self.bands_modeling_estimation_input).toArray()
        image_test_input = self._NormalizeImage(image_test_input)

        image_forecast_complete = kernel.kernelMethodImage(image_test_input, self.inputs_krr, self.alpha,
                                                           self.distance_krr)

        # Convert arrayImage to Image
        image_forecast_complete = image_forecast_complete.arrayProject([1])

        # Denormalize outputs
        return self._DenormalizeAndRename(image_forecast_complete, True)

    def _DenormalizeAndRename(self, image_forecast_complete, normalize):
        if normalize:
            if self.outputs_std is not None:
                image_forecast_complete = image_forecast_complete.multiply(self.outputs_std)

            image_forecast_complete = image_forecast_complete.add(
                self.outputs_mean)

        # Rename labels
        forecast_labels = list(map(lambda prop: prop + "_forecast", self.bands_modeling_estimation_output))
        image_forecast_complete = image_forecast_complete.arrayFlatten([forecast_labels])

        return image_forecast_complete

    def TrainLinearLocal(self, lmbda=.1, sampling_factor=1. / 100.,
                         with_task=False, divide_lmbda_by_n_samples=False,
                         with_cross_validation=False):
        """
        Fit linear ridge regression to the image downloading the data and
        doing the fitting with sklearn.linear_model.

        :param lmbda:
        :param sampling_factor:
        :param divide_lmbda_by_n_samples:
        :param with_task: if the download is done using a task (require pydrive)
        :param with_cross_validation: donwload the data to fit the model with a task
        :return: forecasted image
        :rtype ee.Image
        """
        from Methods_cloud_masking import model_sklearn
        self._BuildDataSet(sampling_factor, normalize=False)

        ds_download_pd = converters.eeFeatureCollectionToPandas(self.datos, self.bands_modeling_estimation + ["weight"],
                                                                with_task=with_task)

        if divide_lmbda_by_n_samples:
            lmbda /= ds_download_pd.shape[0]

        logger.info("Size of downloaded ds: {}".format(ds_download_pd.shape))

        best_params = None
        if not with_cross_validation:
            best_params = {"alpha": lmbda}

        model = model_sklearn.LinearModel(best_params=best_params)

        output_mean, output_std = model_sklearn.fit_model_local(ds_download_pd, model,
                                                                self.bands_modeling_estimation_input,
                                                                self.bands_modeling_estimation_output)

        if with_cross_validation:
            logger.info("Best params: {}".format(model.best_params_))
            model = model.best_estimator_

        self.lmbda = model.alpha

        omega = model.coef_.T * output_std
        intercept = model.intercept_ * output_std + output_mean

        self.omega = ee.Array(omega.tolist())
        self.intercept = ee.Array([intercept.tolist()])

        return

    def TrainLinearServer(self, lmbda=.1, sampling_factor=1. / 100.):
        """
        Fit linear ridge regression to the image

        :param lmbda:
        :param sampling_factor:
        :return: forecasted image
        :rtype ee.Image
        """
        self._BuildDataSet(sampling_factor, normalize=True)
        inputs = self.inputs
        outputs = self.outputs
        labels_input = self.bands_modeling_estimation_input
        labels_output = self.bands_modeling_estimation_output

        # Train
        outputs_eeArray = converters.eeFeatureCollectionToeeArray(outputs, labels_output)
        inputs_eeArray = converters.eeFeatureCollectionToeeArray(inputs, labels_input)
        weight_eeArray = converters.eeFeatureCollectionToeeArray(inputs, ["weight"])
        weight_matrix = weight_eeArray.matrixToDiag()
        inputs_weigted = inputs_eeArray.matrixTranspose().matrixMultiply(weight_matrix)

        tikhonov = ee.Array.identity(len(labels_input)).multiply(lmbda).multiply(ee.Number(inputs.size()))

        omega = inputs_weigted.matrixMultiply(inputs_eeArray).add(tikhonov) \
            .matrixSolve(inputs_weigted.matrixMultiply(outputs_eeArray))

        array_sd = self.inputs_std.pow(-1)
        array_sd = ee.Array.cat([array_sd], 1).matrixToDiag()

        self.omega = array_sd.matrixMultiply(omega)

        prediction_mean = self.inputs_mean.matrixMultiply(self.omega)

        self.intercept = self.outputs_mean.subtract(prediction_mean)

        return

    def PredictLinear(self):
        """
        Apply the model to the current image.
        Must call before TrainLinearLocal or TrainLinearServer

        :return:
        """
        assert self.omega is not None, "Model has not been trained"

        # Test
        image_test_input = self.img.select(self.bands_modeling_estimation_input)

        array1D = image_test_input.toArray()
        array2D = array1D.toArray(1)

        # 1 x num_bands_output
        image_forecast_complete = array2D.matrixTranspose().matrixMultiply(self.omega).add(self.intercept)

        # Convert arrayImage to Image
        image_forecast_complete = image_forecast_complete.arrayProject([1])

        # Denormalize outputs
        return self._DenormalizeAndRename(image_forecast_complete, False)


def ComputeCloudCoverGeom(img, region_of_interest):
    """Compute mean cloud cover and add it as property to the image"""
    # Undefined for sentinel !
    clouds = ee.Algorithms.Landsat.simpleCloudScore(img).gte(50)
    # clouds= img
    
    # clouds_original = image_predict_clouds.select("fmask").eq(2)
    # clouds_original = clouds_original.where(image_predict_clouds.select("fmask").eq(4),2)

    # Add growing to the mask

    # clouds = clouds_original.reduceNeighborhood(ee.Reducer.max(),
    #                                            ee.Kernel.circle(radius=3))
    # clouds = ee.Algorithms.Landsat.simpleCloudScore(img).select("cloud").gt(50).toFloat()

    dictio = clouds.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
                                 bestEffort=True)
    numerito = ee.Number(dictio.get("cloud")).multiply(100)
    img = img.set("CC", numerito)
    return img


# _REFLECTANCE_BANDS_LANDSAT8 = ["B%d" % i for i in range(1, 12)]
_REFLECTANCE_BANDS_SENTINEL2 = SENTINEL2_BANDNAMES


"""
def ImagesWithCC(sentinel_img, start_date, end_date, region_of_interest=None, include_img=False):
    sentinel_info = sentinel_img.getInfo()
    sentinel_full_id = sentinel_info['id']
    image_index = sentinel_info['properties']['system:index']
    landsat_collection = sentinel_full_id.replace("/" + image_index, "")

    print("collection name: " + landsat_collection)

    MGRS_TILE = sentinel_info['properties']['MGRS_TILE']

    # Retrieve previous images
    if region_of_interest is None:
        region_of_interest = ee.Element.geometry(sentinel_img)
        landsat_collection = ee.ImageCollection(landsat_collection) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))
    else:
        landsat_collection = ee.ImageCollection(landsat_collection) \
            .filterBounds(region_of_interest) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))
            
        # .filter(ee.Filter.contains(leftField='.geo',
        #                           rightValue=region_of_interest))

    # landsat_collection = landsat_collection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25))
    dataset_date_asc = landsat_collection.sort("system:time_start", False)
    dataset_date_desc = landsat_collection.sort("system:time_start")

    imgColl = perso.getImagesNeightboor(sentinel_img, dataset_date_asc, dataset_date_desc, 10) \
    #    .sort("system:time_start")

    # Get rid of images with many invalid values

    def _count_valid(img):
        mascara = img.mask()
        mascara = mascara.select(_REFLECTANCE_BANDS_SENTINEL2)
        mascara = mascara.reduce(ee.Reducer.allNonZero())

        dictio = mascara.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
                                      bestEffort=True)

        img = img.set("valids", dictio.get("all"))

        return img

    imgColl = imgColl.map(_count_valid).filter(ee.Filter.greaterThanOrEquals('valids', .5))
    if not include_img:
        imgColl = imgColl.filter(ee.Filter.neq('system:index', image_index))
        
    # Compute CC for the RoI
    return imgColl.map(lambda x: ComputeCloudCoverGeom(x, region_of_interest))
"""

"""
def NextImagesWithCC(sentinel_img, region_of_interest=None,
                     REVISIT_DAY_PERIOD=15, NUMBER_IMAGES=30,
                     include_img=False):
    return ImagesWithCC(sentinel_img,
                        ee.Date(sentinel_img.get("system:time_start")),
                        ee.Date(ee.Number(sentinel_img.get("system:time_start")).add(
                            REVISIT_DAY_PERIOD * NUMBER_IMAGES * 24 * 60 * 60 * 1000)),
                        region_of_interest=region_of_interest,
                        include_img=include_img)
"""

# LANDSAT8_BANDNAMES = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'BQA']


def SelectImagesTraining(method_number, sentinel_img, region_of_interest,
                         number_of_images, number_preselect,
                         threshold_cc):
    """
    Given a landsat image, it returns the number_of_images previous images together with the current image with CC lower than
    THRESHOLD_CC. The returned image contains previous images in bands. It will have num_bands*(number_of_images+1) bands

        :param method_number: Number of the method used
        :param sentinel_img: image to analyzed
        :param region_of_interest: 
        :type region_of_interest: ee.Geometry
        :param number_of_images: 
        :param number_preselect: 
        :param threshold_cc:
        :return:
        :rtype ee.Image
    """                    

    band_names = SENTINEL2_BANDNAMES

    imgColl = PreviousImagesWithCCSentinel(method_number,
                                            sentinel_img,
                                            number_of_images,
                                            threshold_cc,
                                            number_preselect,
                                            region_of_interest)

    # print("Nb previous images (imageCollection): ", imgColl.size().getInfo())
    
    size_img_coll = ee.Number(imgColl.size())

    offset = ee.Number(0).max(size_img_coll.subtract(number_of_images))
    imagenes_training = imgColl.toList(count=number_of_images, offset=offset)

    # join images into a single image
    # band_names = landsat_img.bandNames()
    for lag in range(1, number_of_images + 1):
        image_add = ee.Image(imagenes_training.get(number_of_images - lag))
        new_band_names = time_series_operations.GenerateBandNames(band_names, "_lag_" + str(lag))
        
        image_add = image_add.select(band_names, new_band_names)
        sentinel_img = sentinel_img.addBands(image_add)
        sentinel_img = sentinel_img.set("system:time_start_lag_" + str(lag), image_add.get("system:time_start"))
        sentinel_img = sentinel_img.set("CC_lag_" + str(lag), image_add.get("CC"))
        
    return sentinel_img

"""
def PredictPercentile(img, region_of_interest, num_images=3, threshold_cc=5):
    imgColl = perso.PreviousImagesWithCCSentinel(img, region_of_interest)
    # imgColl = imgColl.filter(ee.Filter.lt("CC", threshold_cc)).limit(num_images)

    img_percentile = imgColl.reduce(reducer=ee.Reducer.percentile(percentiles=[50]))
    return img_percentile
"""

def CloudClusterScore(img, region_of_interest,
                      method_pred= PARAMS_CLOUDCLUSTERSCORE_DEFAULT["method"],
                      threshold_cc=PARAMS_CLOUDCLUSTERSCORE_DEFAULT["threshold_cc"],
                      method_number=PARAMS_SELECTBACKGROUND_DEFAULT['method_number'],
                      number_of_images=PARAMS_SELECTBACKGROUND_DEFAULT['number_of_images'],
                      number_preselect=PARAMS_SELECTBACKGROUND_DEFAULT['number_preselect'],
                      params=None):
    """
    Function to obtain the cloud cluster score in one shot.
    Params are defined in parameters.py file
        :param img: 
        :param region_of_interest: 
        :param method_pred=PARAMS_CLOUDCLUSTERSCORE_DEFAULT["method"]: 
        :param threshold_cc=PARAMS_CLOUDCLUSTERSCORE_DEFAULT["threshold_cc"]: 
        :param method_number=PARAMS_SELECTBACKGROUND_DEFAULT['method_number']: 
        :param number_of_images=PARAMS_SELECTBACKGROUND_DEFAULT['number_of_images']: 
        :param number_preselect=PARAMS_SELECTBACKGROUND_DEFAULT['number_preselect']: 
        :param params=None: 
        :return:  cloud mask (2: cloud,1: shadow, 0: clear)
    """

    
    # print("_" * 60 + "\n")
    # print(" " * 5 + "- Clustering method used: " + method_pred)
    print(" " * 5 + "- Method used: " + method_pred + " " + str(method_number))
    # print("_" * 60)


    if params is None:
        params = dict(PARAMS_CLOUDCLUSTERSCORE_DEFAULT)
    else:
        temp = dict(params)
        params = dict(PARAMS_CLOUDCLUSTERSCORE_DEFAULT)
        params.update(temp)

    image_with_lags = SelectImagesTraining(method_number, img, region_of_interest,
                                            number_of_images, number_preselect,
                                            threshold_cc)
    
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    # clouds_original = img.select('QA60').bitwiseAnd(int('1010000000000000', 2)).gt(0)
    clouds_original = img.select('QA60').bitwiseAnd(cloudBitMask).eq(0)
    clouds_original = img.select('QA60').bitwiseAnd(cirrusBitMask).eq(0)
    clouds = clouds_original.reduceNeighborhood(ee.Reducer.max(),
                                                ee.Kernel.circle(radius=3))

    # reflectance_bands_landsat8 = ["B%d" % i for i in range(1, 12)]
    reflectance_bands_sentinel2 = SENTINEL2_BANDNAMES

    # forecast_bands_landsat8 = [i + "_forecast" for i in reflectance_bands_sentinel2]
    forecast_bands_sentinel2 = [i + "_forecast" for i in reflectance_bands_sentinel2]

    if method_pred == "persistence":
        reflectance_bands_sentinel2_lag_1 = [i + "_lag_1" for i in reflectance_bands_sentinel2]
        img_forecast = image_with_lags.select(reflectance_bands_sentinel2_lag_1, forecast_bands_sentinel2)

    elif method_pred == "percentile":
        img_percentile = PredictPercentile(method_number, img, region_of_interest,
                                             number_of_images, number_preselect, threshold_cc)
        reflectance_bands_sentinel2_perc50 = [i + "_p50" for i in reflectance_bands_sentinel2]
        img_forecast = img_percentile.select(reflectance_bands_sentinel2_perc50,
                                        forecast_bands_sentinel2)

    elif method_pred == "linear":
        modelo = ModelCloudMasking(image_with_lags, reflectance_bands_sentinel2,
                                   clouds, number_of_images, region_of_interest)
        if params["trainlocal"]:
            modelo.TrainLinearLocal(sampling_factor=params["sampling_factor"],
                                    lmbda=params["lmbda"], with_task=params["with_task"])
        else:
            modelo.TrainLinearServer(sampling_factor=params["sampling_factor"],
                                     lmbda=params["lmbda"])

        img_forecast = modelo.PredictLinear()

    elif method_pred == "kernel":
        modelo = ModelCloudMasking(image_with_lags, reflectance_bands_sentinel2,
                                   clouds, number_of_images, region_of_interest)
        if params["trainlocal"]:
            modelo.TrainRBFKernelLocal(sampling_factor=params["sampling_factor"],
                                       lmbda=params["lmbda"], gamma=params["gamma"],
                                       with_task=params["with_task"],
                                       with_cross_validation=params["with_cross_validation"])
        else:
            modelo.TrainRBFKernelServer(sampling_factor=params["sampling_factor"],
                                        lmbda=params["lmbda"], gamma=params["gamma"])

        img_forecast = modelo.PredictRBFKernel()

    else:
        raise NotImplementedError("method %s is not implemented" % method_pred)

    clusterscore = clustering.ClusterClouds(image_with_lags.select(reflectance_bands_sentinel2),
                                            img_forecast.select(forecast_bands_sentinel2),
                                            region_of_interest=region_of_interest,
                                            threshold_dif_cloud=params["threshold_dif_cloud"],
                                            do_clustering=params["do_clustering"],
                                            threshold_reflectance=params["threshold_reflectance"],
                                            numPixels=params["numPixels"],
                                            bands_thresholds=params["bands_thresholds"],
                                            growing_ratio=params["growing_ratio"],
                                            n_clusters=params["n_clusters"])

    return clusterscore, img_forecast
