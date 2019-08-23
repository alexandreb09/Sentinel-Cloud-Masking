# Project

**Aim**: Map vegetation productivity using Sentinel2 images. Filter cloudy pixels and interpolates missing pixels.

This repository only contains scripts for Cloud masking. All the interpolations methods are on Google Earth Engine platform.

**Folders**:
- Build_model: build the model - all code used for building the model.
- Cloud_masking: ready to use cloud masking model

## WorkFlow Cloud masking
  
  1. Setup the **parameters** in `Cloud_masking\parameters.py` file (Python side).
	  - The model requires: 
		  - a date range: starting date (`date_start`) and end date (`date_end`) of the analysis. Provided in string format : "YYYY-MM-DD".
			**NOTE**: the `nb_days_before` and `nb_days_after` will add extra days in the date range. This is usefull for the interpolation (adding some extra images around the date range).
		  - Region of interest : There are two geometry for the area.
			  - `geometry`:
				- a list of list of points: \[\[[x0, y0], [x1, y1], ... ]]
				- This is used to prevent GEE limitations. This geometry is firstly used to roughly filter the Sentinel2 imageCollection.
				- You can use the GEE Code Editor, draw a polygon on the map over the area of interest and copy past the coordinates. 
			- `land_geometry`:
				- String: a path to GEE Feature collection. Ex: `"users/ab43536/UK_border"` for the UK border (source: https://www.eea.europa.eu/data-and-maps/data/eea-reference-grids-2/gis-files/great-britain-shapefile)
				- This is used to mask data outside the geometry. It's usefull for masking ocean, others country.
				- If the image do not intersect the geometry, the image is ignored.
				- This can be a feature collection with quite a high resolution. The GEE Code Editor allows to import shapefile. See these [explanations](https://developers.google.com/earth-engine/importing)
	
	  - This file also includes the parameters for the model itself such as:
		  - `CUTTOF`: random forest cuttof
		  - `number_of_images`: number of images used for selecting the background
		  - `allow_future`: allow selecting image in future...

  2. Process the Cloud Masking process  by running the `Cloud_masking\cloud_masking_process.py` file (Python side).
	  - This script is iterating over all the image (from GEE Sentinel2 dataset) matching the time and area constraints defined in `Cloud_masking\parameters.py` file.
	  - Each image is exported to **Google Earth Engine storage as an Asset**. One task is assigned to each image.
	  - **Restrictions** : 
	    - **The number of tasks** running at the same time is limited to **3000**. The parameters `nb_task_max` (in parameters file) defines the maximum number of tasks running at the same time. The script is updating the tasks list every 30s.
	    - **The number of assets** stockable in GEE is limited to **10 000** assets (and a total memory of 250 Go). If you want to process more than 10000 images, refers to the section [Handle limitation](#handle-gee-limitations). 
	
**NOTE**: If the script fails or is stoped for any reasons (GEE restrictions, user stops process...), the `logs\logs.log` file provides informations on which images have been proceeded. 
 - At the same time the `Cloud_masking\cloud_masking_process.py` script is running, a `xlsx` file is creating saving all the images proceeded. The default location is `Cloud_masking\current_status.xlsx`. This file contains for each rows (image) the current state (task running, completed, waiting...). This file is important to avoid looping over images that do not intersect the `land_geometry`.
 - If the script fails, the currrent state of the task is lost. The `.xlsx` file becomes **inconsistent**. The safer way to repare it is do one of the below:
 	- wait till the current tasks finish and, then,  set the "`Result`" column to `COMPLETED`. The script can then be rerun.
	- cancel all the current running tasks. Then, the cloud masking process could be run again. To cancel all the running task, you can cancel them from the Web interface (tab task) or by running the `cancelAllTask()` methods from the `Cloud_masking/Utils/utils_tasks.py` file.
- Some specific images might be ignored using the `image_to_exclude` argument in `process_and_store_to_GEE` function from `Cloud_masking\cloud_masking_process.py` file. This parameters is useful to ignore images exported outside GEE.

## Handle GEE limitations
- Number of asset restriction: 
    1. **Export all the images to the drive** with the `exportImageListToDrive` function from `Cloud_masking/Utils/utils_tasks` file. It requires a list of images to exports. To easily get all the images from one folder or `imageCollection`, the output from the `getAllImagesInColl(path)` function can be use . 
    	
	    **Meta data management:**
    	 Because the metadata are lost during the exportation, this process will create a dictionary in `.json` file that is storing the metadata. Each key is the GEE path to the image (ex. `users/ab43536/masks_4_methods/20180101T105441_20180101T105435_T31UDT`. The metadata are structured as below:
			- `geometry`: geometry of the image (where there is data)
			- `system:time_start`: image date
			These metadatas are extracted from the original image from Sentinel2 collection ("COPERNICUS/S2").
    2. **Download** all the image from the drive **to a local storage**. This step is assumed to be done manually from the Google Drive website.
    3. Upload the image back to GEE: working on...


## Interpolation

This Python folder only contains the script for interpolating missing data using the harmonic model. 

**Workflow**:
- The script is loading the cloud masks available on GEE storage
- The Sentinel Images matching the cloud mask image (same id) are loaded and filtered according the region and the date range.
- The interpolation process is performed according:
	- The missing data (labelled cloudy) are replace by values interpolated with 10 harmonics. The missing points remaining (values greater below -1 or greater 1) are interpolated with 5 harmonics. The missing values remaining are interpolated with 1 harmonic. 
- A *quality* band is added: this bands is an integer band where the value per pixel is the number of harmonics used in the interpolation. For the actual NDVI bands, the value is equal to -1.
- The script images are exported one by one:

NOTE:
- This script doesn't handle the number of active   
 task. This is a problem if more than 3000 images are processed.
- This script is exporting images to GEE storage This destination might become a problem because of restricted number of assets allowed by GEE. Also, the number of images will increase in GEE storage however, the bigger the number of images used for the interpolation, the better it is.
	- One solution might be to change to export to the DRIVE using "ee.batch.Export.image.toDrive" 
	- The function 'export_image_to_drive' in Cloud_masking/Utils/utils_assets performs this task..     


**Google Earth Engine Editor**: example with NDVI . Run the `users/ab43536/Interpolation/SENTINEL_NDVI` file. It's plotting the NDVI and the interpolation. 
The results aren't saved in GEE web interface.