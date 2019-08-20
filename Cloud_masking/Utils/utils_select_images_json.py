#####################################################
# Utils file for selecting images from json fine    #
#                                                   #
# Methods:                                          #
#       - select_image_from_json(json_file,         #
#                                area=None,         #
#                                date_start=None,   #
#                                date_end=None)     #
#                                                   #
# This file is design to help selecting images      #
# once they have been exported (outside Google      #
# Earth Engine).                                    #
# The selection relies on the `.json` file created  #
# while the exporting                               #
#####################################################


import json                                     # Handle JSON
from datetime import datetime as dt             # Handle dates
from shapely.geometry import Polygon, Point     # Handle geometries

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


if __name__ == "__main__":
    pass
    # import ee
    # ee.Initialize()

    # point_center = [-2.0264646301407083, 54.56517430780476]
    # point_south = [-1.4551755676407083, 51.69243604580755]

    # date_start = "01-01-2018"
    # date_end = "28-02-2018"

    # out_p2 = select_image_from_json("Metadata_mask.json", point_south, date_start, date_end)

    # print(out_p2[:10])

