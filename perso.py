##########################################
#              Functions                 #
##########################################
from ee_ipl_uv_perso.parameters import *
import ee


def add_ndvi_bands(image):
    return image.addBands(image.normalizedDifference([NIR, RED]))


def add_evi_bands(image):
    # Formula : 2.5 * (NIR - RED) / ((NIR + 6*RED - 7.5*BLUE) + 1)
    L = 1
    C1 = 6
    C2 = 7.5
    red = image.select(RED)
    blue = image.select(BLUE)
    nir = image.select(NIR)
    numerateur = nir.subtract(red)
    denominateur = nir.add(red.multiply(C1)).subtract(blue.multiply(C2)).add(L)
    evi = numerateur.divide(denominateur).multiply(2.5)
    return image.addBands(evi)


def rename_bands_ft(image):
    # Rename the bands: 4 -> NDVI ; 5 -> EVI    
    old_bands = image.bandNames()
    new_bands = old_bands.set(4, 'NDVI').set(5, "EVI")
    return image.select(old_bands, new_bands)


def getImagesNeightboor(img, dataset_asc, dataset_desc, limit=10):
    """
        Selectionne les 10 images précédentes
    """
    # Select `limit` previous images
    images = dataset_asc.filter(ee.Filter.lt("system:time_start",
                                            img.get("system:time_end"))) \
                                .limit(limit)

    # If less than `limit` images selected
    size = images.size()
    if size.lt(limit):
        # calc number to add
        nbImagesToAdd = ee.Number(limit).subtract(size)
        # print("Nombre images ajoutées après: ", nbImagesToAdd)
        # Add the next `limit` images
        imagesAfter = dataset_desc.filter(ee.Filter.gt("system:time_start",
                                                        img.get("system:time_end"))) \
                                    .limit(limit)
        # Merge of both collections
        images = images.merge(imagesAfter)
    return images


def ComputeCloudCoverGeomSentinel(img, region_of_interest):
    """Compute mean cloud cover and add it as property to the image"""
    # Undefined for sentinel !
    # clouds = ee.Algorithms.Landsat.simpleCloudScore(img).gte(50)
    
    # clouds= img
    
    # clouds_original = image_predict_clouds.select("fmask").eq(2)
    # clouds_original = clouds_original.where(image_predict_clouds.select("fmask").eq(4),2)

    # Add growing to the mask

    # clouds = clouds_original.reduceNeighborhood(ee.Reducer.max(),
    #                                            ee.Kernel.circle(radius=3))
    # clouds = ee.Algorithms.Landsat.simpleCloudScore(img).select("cloud").gt(50).toFloat()

    # dictio = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
    #                             bestEffort=True)
    # numerito = ee.Number(dictio.get("CLOUDY_PIXEL_PERCENTAGE")) #.multiply(100)
    img = img.set("CC", img.get('CLOUDY_PIXEL_PERCENTAGE'))
    return img



def PreviousImagesWithCCSentinel(sentinel_img, region_of_interest=None, NUMBER_IMAGES=30,
                         include_img=False, threshold_cc=10):
    """
    Return the NUMBER_IMAGES previous images with cloud cover

    :param sentinel_img:
    :param region_of_interest:
    :param REVISIT_DAY_PERIOD:
    :param NUMBER_IMAGES:
    :param include_img: if the current image (sentinel_img) should be included in the series
    :return:
    """
    # Get collection id


    sentinel_info = sentinel_img.getInfo()                                  # Sentinel infos
    sentinel_full_id = sentinel_info['id']                                  # full image ID
    image_index = sentinel_info['properties']['system:index']               # Imafe index
    sentinel_collection = sentinel_full_id.replace("/" + image_index, "")   # Sentinel collection (base for background) 

    MGRS_TILE = sentinel_info['properties']['MGRS_TILE']                    # Tile the image analyzed

    # Retrieve previous images
    # Filter per area
    if region_of_interest is None:
        region_of_interest = ee.Element.geometry(sentinel_img)
        sentinel_collection = ee.ImageCollection(sentinel_collection) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))
    else:
        sentinel_collection = ee.ImageCollection(sentinel_collection) \
            .filterBounds(region_of_interest) \
            .filter(ee.Filter.eq("MGRS_TILE", MGRS_TILE))


    # Method 1
    # Filter :
    #   - 20 previous images

    # Peut être factorisé
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                    dataset_date_desc, 20)
    """

    # Method 2
    # Filter :
    #   - CC < 10%
    #   - 20 previous iamges

    # Filter CC ThreShold
    
    
    threshold_cc = 10
    # sentinel_collection = sentinel_collection.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", threshold_cc))
    sentinel_collection = sentinel_collection.filter(ee.Filter.gt("CLOUDY_PIXEL_PERCENTAGE", threshold_cc))

    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc,
                                        dataset_date_desc, 20)
    

    # Method 3
    # Filter CC : the 5 best over all the date
    """
    imgColl = sentinel_collection.sort("CLOUDY_PIXEL_PERCENTAGE")
    imgColl = imgColl.limit(20)
    """

    # Method 4
    # Filter:
    #   - 20 previous images
    #   - 5 least cloudy
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc, dataset_date_desc, 20)
    imgColl = imgColl.sort("CLOUDY_PIXEL_PERCENTAGE", False).limit(5)
    """


    # Method 5
    # Filter:
    #   - 20 previous images
    #   - 5 most cloudy
    """
    dataset_date_asc = sentinel_collection.sort("system:time_start", False)
    dataset_date_desc = sentinel_collection.sort("system:time_start")
    imgColl = getImagesNeightboor(sentinel_img, dataset_date_asc, dataset_date_desc, 20)
    imgColl = imgColl.sort("CLOUDY_PIXEL_PERCENTAGE").limit(5)
    """
    
    # imgColl = imgColl.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    

    # Get rid of images with many invalid values
    def _count_valid(img):
        mascara = img.mask()
        mascara = mascara.select(SENTINEL2_BANDNAMES)
        mascara = mascara.reduce(ee.Reducer.allNonZero())

        dictio = mascara.reduceRegion(reducer=ee.Reducer.mean(), geometry=region_of_interest,
                                      bestEffort=True)

        img = img.set("valids", dictio.get("all"))

        return img

    imgColl = imgColl.map(_count_valid).filter(ee.Filter.greaterThanOrEquals('valids', .5))
    if not include_img:
        imgColl = imgColl.filter(ee.Filter.neq('system:index', image_index))
        
    # Compute CC for the RoI
    # imgColl = imgColl.map(lambda x: ComputeCloudCoverGeomSentinel(x, region_of_interest))

    return imgColl


def PredictPercentile(img, region_of_interest, num_images=3, threshold_cc=5):
    imgColl = PreviousImagesWithCCSentinel(img, region_of_interest)

    img_percentile = imgColl.reduce(reducer=ee.Reducer.percentile(percentiles=[50]))
    return img_percentile




# Region of interest
ROI = image.get("system:footprint").getInfo().coordinates;
ROI = ee.Geometry.Polygon(ROI);

# Map Center
lineRing = image.getInfo()['properties']['system:footprint'];
center = ee.Array(lineRing.coordinates);
center = center.reduce(ee.Reducer.mean(), [0]).getInfo()['0'];
zoom = 8;

# Normalization image according to article
coef_standard = 10000;
coef_32k = 32758; # 2**15;
image_standard = image.divide(coef_standard);
image_32k = image.divide(coef_32k);

/**********************************/
/* Compute Decision Tree filter 1 */
/**********************************/
function getMaskTree1(image_normalized){
  # Criteria 1 : Cirrus
  expr1 = image_normalized.expression(
    '( (b("B3") < 0.325) & (b("B8A") < 0.166) & (b("B10") > 0.011)) ? 1 : 0' 
  );
  # Criteria 2 : Cirrus
  expr2 = image_normalized.expression(
    '( (b("B3") > 0.325) & (b("B11") < 0.267) & (b("B4") < 0.674)) ? 1 : 0' 
  );
  # Criteri 3 : Clouds
  expr3 = image_normalized.expression(
    '( (b("B3") > 0.325) & (b("B11") > 0.267) & (b("B7") < 1.544)) ? 1 : 0' 
  );
  # full criteria = Clouds + Cirrus
  return expr1.or(expr2.or(expr3));
}


/**********************************/
/* Compute Decision Tree filter 2 */
/**********************************/
function getMaskTree2(image_normalized){
  # Criteria 1 : Cirrus
  expr1 = image_normalized.expression(
    '( (b("B8A") > 0.156) & (b("B3") < 0.333) & (b("B10")/b("B2") > 0.065)) ? 1 : 0' 
  );
  # Criteria 2 : Cloud
  expr2 = image_normalized.expression(
    '( (b("B8A") > 0.156) & (b("B3") > 0.333) & (b("B6")/b("B11") < 4.292)) ? 1 : 0' 
  );
  # full criteria = Clouds + Cirrus
  return expr1.or(expr2);
}


/*********************************/
/* GEE Cloud Mask                */
/*********************************/
def getMaskGEE(image):
    qa = image.select('QA60');

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloudBitMask = 1 << 10;
    cirrusBitMask = 1 << 11;

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

    return mask.not()


