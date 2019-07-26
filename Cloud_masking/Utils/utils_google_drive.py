
import json
from datetime import datetime as dt
from shapely.geometry import Polygon, Point

def select_image_from_json(json_file, area=None, date_start=None, date_end=None):
    """ Select image matching dates and area from json file (return json list)
    Arguments:
        :param json_file: meta data file (generated after exporting images)
        :param area=None: area to filter (list of point coordinates)
        :param date_start=None: starting date (format: dd-mm-yyyy)
        :param date_end=None: end date (format: dd-mm-yyyy)
        :return: list of images (string id)
    """
    # read file
    with open(json_file, "r") as f:
        list_image = json.load(f)

    # create polygon object
    is_poly = isinstance(area[0], list)
    if is_poly: area = Polygon(area)
    else: area = Point(area)
    
    # Create datetime object
    if date_start and date_end:
        date_start = dt.strptime(date_start, '%d-%m-%Y')
        date_end = dt.strptime(date_end, '%d-%m-%Y')

    output = []
    # For each images in the file
    for image, values in list_image.items():
        rep = True

        # If area is specified
        if area:
            # Check if they intersect
            if is_poly: rep = area.intersects(Polygon(values["geometry"]))
            else: rep = area.within(Polygon(values["geometry"]))
        # If dates specified and area right
        if rep and date_start and date_end:
            # Check if image date is between date range
            rep = (date_start < dt.fromtimestamp(values['date_deb']/1000)) and (dt.fromtimestamp(values['date_deb']/1000) < date_end)
        # If all criteria satisfied
        if rep:
            # Add image to output
            output.append(image)
    
    return output


import ee
ee.Initialize()

area = [-3.4733135998687885, 57.090152154809864]
area = [[-4.1379864514312885, 57.39924721397613],
        [-4.1379864514312885, 57.27176253119143],
        [-3.9072735608062885, 57.27176253119143],
        [-3.9072735608062885, 57.39924721397613]]

out = select_image_from_json('Metadata_mask.json', area=area,  date_start='01-01-2018', date_end='31-12-2018')
print(out[0])
out = [o.split('/')[-1] for o in out]
print(len(out))

with open('Metadata_mask.json', "r") as f:
    list_image = json.load(f)

names = [name.split('/')[-1] for name in list(list_image.keys())]
print(len(names))

image_delete = ["users/ab43536/masks_4_methods/" + name for name in names if name not in out]

import utils_assets

utils_assets.delete_assets(image_delete)
