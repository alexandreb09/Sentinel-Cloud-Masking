# Project

**Aim**: map vegetation productivity

**Folders**:
- `Build_model`: build the model - all code used for building the model
- `Cloud_masking`: ready to use model

**WorkFlow**
  1. Python code: process the Cloud Masking. Process done by running the `Cloud_masking\randomForest.py` file. 
	  - This step is done by iterating over all the image matching the time and area constraints defined in `Cloud_masking\parameters.py` file.
	  - Each image is exported to Google Earth Engine as an Asset. One task is assigned to each image.
	  Note: 
	    - The number of tasks running at the same time is limited to 3000. 
	    - The number of assets stockable in GEE is limited to 10 000. I'm currently working on the case there are more than 10 000 images.
  2.  Google Earth Engine Editor: example with NDVI . Run the `users/ab43536/Interpolation/SENTINEL_NDVI` file. It's plotting the the NDVI and the interpolation. The results aren't saved. 