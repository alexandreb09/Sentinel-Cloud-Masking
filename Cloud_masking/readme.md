# Cloud masking model

**Goal**: create a cloud detection model. The model is a random Forest model. Each feature in the randomForest is a cloud detection model. 

To run the model:

1. From the `parameters.py` file, specify:
	- The area of interest with the `geometry` variable
	- The date range with the variables `date_start` and `date_end`
2. Run the `randomForest.py` file. The methods used is `process_and_store_to_GEE()`

---
There are two kinds of method used in two folders: 
- `Background_methods`: cloud masking on Sentinel 2 data. This work is based on the [ee_ipl_uv](https://github.com/IPL-UV/ee_ipl_uv) repository. There are 2 methods implemented: `method1` and `method5`. 
- `Tree_methods`: decision tree models from [this article](https://www.mdpi.com/2072-4292/8/8/666). There are 3 decision trees implemented: `decision_tree1`, `decision_tree2` and `decision_tree3`. 
**Note**: The `decision_tree1` is **not used** in the randomForest model. 

See the `Build_model` folder for details. 

The `utils` folder provides some utils functions to handle:
- GEE task management
- GEE exportation to drive