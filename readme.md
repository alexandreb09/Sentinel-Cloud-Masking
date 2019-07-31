# Project

**Aim**: Map vegetation productivity using Sentinel2 images. Filter cloudy pixels and interpolates masks pixels.

**Folders**:
- Build_model: build the model - all code used for building the model.
- Cloud_masking: ready to use model

## WorkFlow
  
  1. Setup the **parameters** in `Cloud_masking\parameters.py` file  (Python side).
	  - The model requires: 
		  - a date range: starting date (`date_start`) and end date (`date_end`) of the analysis. Provided in string format : "YYYY-MM-DD"
		  - Region of interest : There are two geometry for the area.
			  - `geometry`:
				- a list of list of points: [[[x0, y0], [x1, y1], ... ]]
				- This used to prevent GEE limitations. This geometry is firtly used to roughly filter the Sentinel2 imageCollection.
				- You can use the GEE Code Editor, draw a polygon on the map over the area of interest and copy past the coordinates. 
			- `land_geometry`:
				- String: a path to GEE Feature collection. Ex: `"users/ab43536/UK_border"`
				- This is used to mask data outside. Usefull for masking ocean, others country).
				- If the image do not intersect the geometry, the image is ignored.
				- This can be a feature collection with quite a high resolution. The GEE Code Editor allows to import shapefile.
	
	  - This file also includes the parameters for the model itself such as:
		  - `CUTTOF`: random forest cuttof
		  - `number_of_images`: number of images used for selecting the background
		  - `allow_future`: allow selecting image in future...



  2. Process the Cloud Masking. Process done by running the `Cloud_masking\cloud_masking_process.py` file (Python side).
	  - This script is iterating over all the image (from GEE Sentinel2 dataset) matching the time and area constraints defined in `Cloud_masking\parameters.py` file.
	  - Each image is exported to Google Earth Engine as an Asset. One task is assigned to each image.
	  - **Restrictions** : 
	    - **The number of tasks** running at the same time is limited to **3000**. The parameters `nb_task_max` defines the maximum number of tasks running at the same time (defined in `parameters.py` file). The script is updating the tasks list every 30s.
	    - **The number of assets** stockable in GEE is limited to **10 000** assets (and a total memory of 250 Go). If you want to process more than 10000 images, refers to the section [Handle limitation](#handle-gee-limitations). 
	   
  3.  Google Earth Engine Editor: example with NDVI . Run the `users/ab43536/Interpolation/SENTINEL_NDVI` file. It's plotting the the NDVI and the interpolation. The results aren't saved. I'm working on...

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