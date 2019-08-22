import ee
import interpolatation_model as harmo_model

import load_dataset

ee.Initialize()

#################################
#          VARIABLES            #
#################################
# Sentinel collection
sentinel_coll_name = "COPERNICUS/S2"

# Time windows interpolation
date_start = '2018-02-01'
date_end = '2018-11-30'

# Number of days used before the starting date and after the end date
day_gap_before = 30
day_gap_after = 30

# The dependent variable we are modeling(only "NDVI" is supported)
dependent = 'NDVI'

# The number of cycles on the daterange to model.
harmo_10 = 10
harmo_5 = 5
harmo_1 = 1

roi = ee.Geometry.Polygon(
            [[[-3.7161555256421934, 57.10487686990405],
            [-3.9139094318921934, 56.9119504742678],
            [-3.2272639240796934, 56.85943339198275],
            [-2.9855647053296934, 57.10487686990405]]])



#################################
#    LOAD MASK FUNCTIONS        #
#################################

# Date used for fitting the model
date_start_fit = ee.Date(date_start).advance(-day_gap_before, "day")
date_end_fit = ee.Date(date_end).advance(-day_gap_after, "day")

# create bands names
fitted_band = "fitted_" + str(harmo_10)
recovered_band = "NDVI_final_" + str(harmo_10)

maskCollection = load_dataset.loadMaskCollection('users/ab43536/masks_4_methods',
                                    sentinel_coll_name, roi,
                                    date_start_fit, date_end_fit)


#####################################
#       INTERPOLATION               #
#####################################
# Filter to the area of interest, mask clouds, add variables.
sentinel = load_dataset.build_sentinel_dataset(maskCollection, sentinel_coll_name) \
                        .filterDate(date_start_fit, date_end_fit) \
                        .filterBounds(roi)


fittedHarmonic = harmo_model.fit(sentinel, dependent)


# Remove image date gap before and after
fittedHarmonic = fittedHarmonic.filterDate(date_start, date_end)

print(fittedHarmonic.first().bandNames().getInfo())
