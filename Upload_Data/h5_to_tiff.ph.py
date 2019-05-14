import os
import gdal
from osgeo import osr
import numpy
import h5py

number_rows_kept = 1000
training_ratio = 0.8


# Loading data - read file
with h5py.File('20170412_s2_manual_classification_data.h5', 'r') as f:
    keys = list(f.keys())
    bands = f["spectra"][:number_rows_kept]
    classes_pixel = f["classes"][:number_rows_kept]
    classes_ids = f["class_ids"][:number_rows_kept]
    longitude = f["longitude"][:number_rows_kept]
    latitude = f["latitude"][:number_rows_kept]
    class_names = f["class_names"][()].astype('U13')       # Decode class names
    # Decode bands names
    bands_name = ["B" + bd.astype('U13') for bd in f["band"]]


def printClassNames():
    print("\nid names")
    for id, name in zip(classes_ids, class_names):
        print("%2d %s" % (id, name))

printClassNames()


# config
GDAL_DATA_TYPE = gdal.GDT_Int32 
GEOTIFF_DRIVER_NAME = r'GTiff'
NO_DATA = 15
SPATIAL_REFERENCE_SYSTEM_WKID = 4326

def create_raster(output_path,
                  columns,
                  rows,
                  nband = 1,
                  gdal_data_type = GDAL_DATA_TYPE,
                  driver = GEOTIFF_DRIVER_NAME):
    """
    returns gdal data source raster object
    """ 

    # create driver
    driver = gdal.GetDriverByName(driver)

    output_raster = driver.Create(output_path,
                                  int(columns),
                                  int(rows),
                                  nband,
                                  eType = gdal_data_type)    
    return output_raster

def numpy_array_to_raster(output_path,
                          numpy_array,
                          upper_left_tuple,
                          cell_resolution,
                          nband = 1,
                          no_data = NO_DATA,
                          gdal_data_type = GDAL_DATA_TYPE,
                          spatial_reference_system_wkid = SPATIAL_REFERENCE_SYSTEM_WKID,
                          driver = GEOTIFF_DRIVER_NAME):
    """
    returns a gdal raster data source

    keyword arguments:

    output_path -- full path to the raster to be written to disk
    numpy_array -- numpy array containing data to write to raster
    upper_left_tuple -- the upper left point of the numpy array (should be a tuple structured as (x, y))
    cell_resolution -- the cell resolution of the output raster
    nband -- the band to write to in the output raster
    no_data -- value in numpy array that should be treated as no data
    gdal_data_type -- gdal data type of raster (see gdal documentation for list of values)
    spatial_reference_system_wkid -- well known id (wkid) of the spatial reference of the data
    driver -- string value of the gdal driver to use

    """
    

    print ('UL: (%s, %s)' % (upper_left_tuple[0],
                            upper_left_tuple[1]))

    rows, columns = numpy_array.shape
    print ('ROWS: %s\n COLUMNS: %s\n' % (rows,
                                        columns))

    # create output raster
    output_raster = create_raster(output_path,
                                  int(columns),
                                  int(rows),
                                  nband,
                                  gdal_data_type) 

    geotransform = (upper_left_tuple[0],
                    cell_resolution,
                    upper_left_tuple[1] + cell_resolution,
                    -1 *(cell_resolution),
                    0,
                    0)

    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(spatial_reference_system_wkid)
    output_raster.SetProjection(spatial_reference.ExportToWkt())
    output_raster.SetGeoTransform(geotransform)
    output_band = output_raster.GetRasterBand(1)
    output_band.SetNoDataValue(no_data)
    output_band.WriteArray(numpy_array)          
    output_band.FlushCache()
    output_band.ComputeStatistics(False)

    if os.path.exists(output_path) == False:
        raise Exception('Failed to create raster: %s' % output_path)

    return  output_raster
