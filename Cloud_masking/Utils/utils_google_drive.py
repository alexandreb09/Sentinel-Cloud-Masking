
import json
from datetime import datetime as dt
from shapely.geometry import Polygon

def select_image_from_json(json_file, area=None, date_start=None, date_end=None):

    with open(json_file, "r") as f:
        list_image = json.load(f)

    output = []
    if area: area = Polygon(area)
    if date_start and date_end:
        date_start = dt.strptime(date_start, '%d-%m-%Y')
        date_end = dt.strptime(date_end, '%d-%m-%Y')

    for image, values in list_image.items():
        rep = True

        # If area is specified
        if area:
            # Check if they intersect
            rep = area.intersect(Polygon(values["geometry"]))
        # If dates specified and area right
        if rep and date_start and date_end:
            # Check if image date is between date range
            rep = (date_start < dt.fromtimestamp(values['date_deb']/1000)) and (dt.fromtimestamp(values['date_end']/1000) < date_end)
        
        # If all criteria satisfied
        if rep:
            # Add image to output
            output.append(image)
    
    return output


out = select_image_from_json('Metadata_mask.json', date_start='01-06-2018', date_end='30-06-2018')
print(out)
