from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_photo_location(image):

    exif = image.getexif()

    if not exif:
        return None

    gps_info = None

    for key, value in exif.items():
        tag = TAGS.get(key)

        if tag == "GPSInfo":
            gps_info = value
            break

    if not gps_info:
        return None

    gps_data = {}

    for key, value in gps_info.items():
        tag = GPSTAGS.get(key, key)
        gps_data[tag] = value

    return gps_data