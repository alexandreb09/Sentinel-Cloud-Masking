## Contents
---
The folders contains 1 *folder* and 1 *file*:
- `sample_data.xlsx`: sheet file where each sheet contains sampled values from the image in `Images_example` folder.
   - Each sheet has data from a given image
   - The fitted value are sampled from the fitted band where the cloud mask predicts **non cloud**.
- `Images_example` folder contains a set of 9 images. Each image has the following bands:
 `[RED, BLUE, GREEN, NDVI, fitted, NDVI_recovered]`. The `NDVI` bands is original NDVI, the `fitted` bands is the predicted `NDVI` from harmonic model with a number of harmonic equal to `1`. The `NDVI_recovered` is the `NDVI` bands where the pixels masked with the Cloud Mask is replaced by the fitted values. 
  - Image_north_1:
    - ID: `20180101T114459_20180101T114453_T30VVJ`
    - Region: North UK
    - Date: `01-01-2018`
  - Image_north_2:
    - ID: `20180615T114351_20180615T114348_T30VVJ`
    - Region: North UK
    - Date: `15-06-2018`
  - Image_north_3:
    - ID: `20180905T113309_20180905T113450_T30VVJ`
    - Region: North UK
    - Date: `05-09-2018`
  - Image_center_1:
    - ID: `20180108T113439_20180108T113443_T30UWF`
    - Region: Center UK
    - Date: `08-01-2018`
  - Image_center_2:
    - ID: `20180629T112111_20180629T112537_T30UWF`
    - Region: Center UK
    - Date: `29-06-2018`
  - Image_center_3:
    - ID: `20180902T112109_20180902T112104_T30UWF`
    - Region: North UK
    - Date: `02-09-2018`
  - Image_south_1:
    - ID: `20180110T112431_20180110T112427_T30UWC`
    - Region: South UK
    - Date: `10-01-2018`
  - Image_south_2:
    - ID: `20180711T110619_20180711T111139_T30UWC`
    - Region: South UK
    - Date: `11-07-2018`
  - Image_south_3:
    - ID: `20180904T110621_20180904T110820_T30UWC`
    - Region: North UK
    - Date: `04-09-2018`

The areas are defined as points:
  - Point north: `[-3.8282224426407083, 56.93849356662374]`
  - Point center: `[-2.0264646301407083, 54.56517430780476]`
  - Point south: `[-1.4551755676407083, 51.69243604580755]`
     

Note:
  - The data can be downloaded from [Google Drive](https://drive.google.com/drive/folders/1L3T-BTQSL35onJnWf3eBuyDvYw1-Nj_A?usp=sharing)