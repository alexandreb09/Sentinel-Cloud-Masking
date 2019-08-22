## Model

**Aim**: This folder contains the scripts to reproduce the results from the notebook. This also contains the scripts to reproduce the dataset used building and evaluating the model.

**Folders**: 
 - Methods_cloud_masking: all the script to proceed the cloud mask
 - Notebook: folder explaining how we build the model. It includes the following files:
     - `Notebook_build_model.ipynb` to reproduce the results
     - `notebook_methods.py`: all the methods used in the notebook itself (most of them are plot function)
     - `Notebook_model.html`: html version of the notebook
     - Images of some trees...

**Reproduce results**:
  1. Download the classified data from [GitLab](https://gitext.gfz-potsdam.de/EnMAP/sentinel2_manual_classification_clouds/blob/19cfa1de66d3a5c7f382a2670f9c8759074a372b/20160914_s2_manual_classification_data.h5)
  2. Edit the `create_dataset.py` file:
        - Set at the top of the file the path to the downloaded file in step 1 (`.h5` file).
        - Set path for two temporary files (created during the process)
        - Set the path to the output file (excel file).
        - Set the number of desired points for `training` and `test` set.
    3. Run the `create_dataset.py` file. The script is following the below steps:
        - Split the .h5 file into two subfiles (same size). This is to facilitate data
            manipulation with smaller files
        - For each image in these files: add the GEE image ID based on Sentinel image ID
        - Remove useless data
        - Merge these 2 files as 1 dataframe
        - Filter images in order that each image has the same number of  "cloudy" / "not cloudy" pixels
        - Add empty feature columns to training and test set
        - Export the results in the ".xlsx" file
    4. Run the `run_methods.py` file. This script will fill the results for each methods from the excel file.
        The script is following the below steps:

        - Iterate over all the images in the excel file 
        according the "ig_GEE" columns
        -  Iterate over the 13 cloud masking methods(percentile 1 to 5, persistence 1 to 5 and tree 1 to 3). For each method:
            - Apply the cloud mask the GEE image
            - Extract the values from the result image
        - Save the results in the excel file
    
    5. Run the notebook `Notebook/Notebook_build_model.ipynb`.