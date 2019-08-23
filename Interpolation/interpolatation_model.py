#####################################################
#        HARMONIC REGRESSION CODE                   #
#####################################################

import ee
import math

bands = ['B1', 'B2', 'B3', 'B4', 'B5',
         'B6', 'B7', 'B8', 'B8A', 'B9',
         'B10', 'B11', 'B12', 'QA60',
         'NDVI', 'fitted', 'NDVI_recovered']


#####################################################
#                   FUNCTIONS                       #
#####################################################
def add_fit(sentinel_coll, n_harmonics, dependent):
    def addNDVI(image):
        """ Function to add an NDVI band.
        Arguments
            :param image: GEE image
        """
        return image.addBands(image.normalizedDifference(['B8', 'B4']) \
                                   .rename(dependent)) \
                    .float()
        

    def addConstant(image):
        """ Add a constant band equals 1
        Arguments:
            :param image: 
        """   
        return image.addBands(ee.Image.constant(1))
  

    def addTime(image):
        """ Function to add a time band.
            Compute time in fractional years
        Arguments:
            :param image: 
        """   
        date = ee.Date(image.get('system:time_start'))
        years = date.difference("1970-01-01", 'year')
        timeRadians = ee.Image(years.multiply(2 * math.pi))
        return image.addBands(timeRadians.rename('t').float())
    
 
    def get_names(base, list_):
        """ Function to get a sequence of band names for harmonic terms.
        Arguments:
            :param base: python string
            :param list: list of number
        """   
        return ee.List(["{}{}".format(base, i) for i in list_])


    def addHarmonics(freqs):
        """ Function to compute the specified number of harmonics and add
            them as bands. Assumes the time band is present.
        Arguments:
            :param freqs: harmonic frequencies e.g. GEE list of integer
        """   
        def wrapped(image):
            # Make an image of frequencies.
            frequencies = ee.Image.constant(freqs)
            # This band should represent time in radians.
            time = ee.Image(image).select('t')
            # Get the cos - sin terms.
            cosines = time.multiply(frequencies).cos().rename(cosNames)
            sines = time.multiply(frequencies).sin().rename(sinNames)
            # add bands
            return image.addBands(cosines).addBands(sines)
        return wrapped
    

    def add_fitted(harmonicTrendCoefficients, independents):
        """ Create the fiited bands from coefficients and add it to the image band
        Arguments:
            :param harmonicTrendCoefficients: list of coefficients (beta_0, beta_1, ...)
            :param independents: independent variables
        """
        def wrapped(image):
            return image.addBands(image.select(independents)
                                  .multiply(harmonicTrendCoefficients)
                                  .reduce('sum')
                                  .rename('fitted_' + str(n_harmonics))
                                  .clip(image.geometry())
                                  .float())
        return wrapped


    def add_recovered(dependent):
        """ Add recovered band: 
                - original data where there is
                - fitted data where there isn't
        Arguments:
            :param image: 
        """
        def wrapped(image):
            return image.addBands(image.select('fitted_' + str(n_harmonics))
                                  .blend(image.select(dependent))
                                  .rename('NDVI_final_' + str(n_harmonics))
                                  .clip(image.geometry())
                                  .float())
        return wrapped


    def select_used_bands(independents):
        """ Remove independents bands
        Argument:
            :param image: 
        """
        def wrapped(image):
            image = ee.Image(image)
            return image.select(image.bandNames().removeAll(independents))
        return wrapped

    
    def mask_values_1(image):
        output = image.select('fitted_' + str(n_harmonics))
        mask_ndvi = output.gt(-1).And(output.lt(1))
        return image.addBands(srcImg=output.updateMask(mask_ndvi),
                              overwrite=True)
        
    
    # Make a list of harmonic frequencies to model.  
    # These also serve as band name suffixes.
    harmonicFrequencies = [i for i in range(1, n_harmonics + 1)]
    
    # Construct lists of names for the harmonic terms.
    cosNames = get_names('cos_', harmonicFrequencies)
    sinNames = get_names('sin_', harmonicFrequencies)

    # Independent variables.
    independents = ee.List(['constant', 't']).cat(cosNames) \
                                             .cat(sinNames)
                                             
    # Add variables
    sentinel_harmo = sentinel_coll.map(addNDVI) \
                                .map(addTime)   \
                                .map(addConstant)   \
                                .map(addHarmonics(harmonicFrequencies))
  
    # The output of the regression reduction is a 4x1 array image.
    harmonicTrendCoefficients = sentinel_harmo  \
                    .select(independents.add(dependent))    \
                    .reduce(ee.Reducer.linearRegression(independents.length(), 1))  \
                    .select('coefficients') \
                    .arrayProject([0])  \
                    .arrayFlatten([independents])
       
    # Compute fitted values.
    fittedHarmonic = sentinel_harmo.map(add_fitted(harmonicTrendCoefficients, independents))
  
    # If number of harmonic != 1
    if n_harmonics > 1:
        # Mask values greater 1 and below -1
        fittedHarmonic = fittedHarmonic.map(mask_values_1)
    
    fittedHarmonic = fittedHarmonic.map(add_recovered(dependent))   \
                                    .map(select_used_bands(independents))
  
    return fittedHarmonic


def add_quality_band(harmo_10, harmo_5, harmo_1):
    def wrapped(image):
        image = ee.Image(image)
        return image.addBands(ee.Image.constant(1).updateMask(image.select('fitted_' + str(harmo_1)).mask())
                .blend(ee.Image.constant(5).updateMask(image.select('fitted_' + str(harmo_5)).mask()))
                .blend(ee.Image.constant(10).updateMask(image.select('fitted_' + str(harmo_10)).mask()))
                .blend(ee.Image.constant(-1).updateMask(image.select('NDVI').mask()))
                .clip(image.geometry())
                .rename('quality'))
    return wrapped


def add_final_bands(dependent, harmo_10, harmo_5, harmo_1):
    """ Add the output bands where the original NDVI is completed with:
            1. The 10 harmonics interpolations
            2. If some values are missing, completed with the 5 harmonic interpolation
            3. If some values are missing, completed with the 1 harmonic interpolation
    Arguments:
        :param dependent: dependent varaible (NDVI)
        :param harmo_10: integer = 10
        :param harmo_5: integer = 5
        :param harmo_1: integer = 1
    """
    def wrapped(image):
        return image.addBands(image.select(dependent)
                                .blend(image.select('fitted_' + str(harmo_1)))
                                .blend(image.select('fitted_' + str(harmo_5)))
                                .blend(image.select('fitted_' + str(harmo_10)))
                                .rename(dependent + '_final')
                                .clip(image.geometry())
                                .float())
    return wrapped


def fit(sentinel_coll, dependent):
    """ Function co compute the whole interpolation (for harmonic model)
        This model is applying an interpolation with 1, 5 and 10 harmonics
        The output is the actual NDVI values interpolated where there
        are missing values (cloud) by:
            1. The 10 harmonics interpolations
            2. If some values are missing, completed with the 5 harmonic interpolation
            3. If some values are missing, completed with the 1 harmonic interpolation

        A "quality" band is added containing the number of pixels used for 
        the interpolations: 
            - 10 for 10 harmonics,
            - 5 for 5 harmonics
            - 1 for 1 harmonic
            - '-1' for the actual value (not interpolated)

    NOTE: In any case, the 3 interpolations (with 1,5,10 harmonics) are computed

    Arguments:
        :param sentinel_coll: sentinel collection to proceed
        :param dependent: dependents varaibales used
    """
    harmo_10 = 10
    harmo_5 = 5
    harmo_1 = 1
  
    fittedHarmonic = add_fit(sentinel_coll, harmo_10, dependent)
    fittedHarmonic = add_fit(fittedHarmonic, harmo_5, dependent)
    fittedHarmonic = add_fit(fittedHarmonic, harmo_1, dependent)

    fittedHarmonic = fittedHarmonic.map(add_final_bands(dependent,harmo_10, harmo_5, harmo_1)) \
                                   .map(add_quality_band(harmo_10, harmo_5, harmo_1))
    return fittedHarmonic
