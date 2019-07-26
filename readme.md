# Project

**Aim**: map vegetation productivity

**Folders**:
- Build_model: build the model - all code used for building the model
- Cloud_masking: ready to use model

**WorkFlow**
  1. Python code: process the Cloud Masking. Process done by running the `Cloud_masking\randomForest.py` file. 
	  - This step is done by iterating over all the image matching the time and area constraints defined in `Cloud_masking\parameters.py` file.
	  - Each image is exported to Google Earth Engine as an Asset. One task is assigned to each image.
	  - **Restrictions** : 
	    - **The number of tasks** running at the same time is limited to **3000**. 
	    - **The number of assets** stockable in GEE is limited to **10 000** (and a total memory of 250 Go). If these limitations are reached, refer section ''Handle limitation". 
	   
  2.  Google Earth Engine Editor: example with NDVI . Run the `users/ab43536/Interpolation/SENTINEL_NDVI` file. It's plotting the the NDVI and the interpolation. The results aren't saved. 

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
