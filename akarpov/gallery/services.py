from PIL import ExifTags, Image


def _get_if_exist(data, key):
    if key in data:
        return data[key]
    return None


def _convert_to_dec_degrees(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to decimal degress"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_image_coordinate(path):
    try:
        exif = load_image_meta(path)
        gps_info = exif["GPSInfo"]
    except Exception:
        return {}
    try:
        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, "GPSLatitudeRef")
        gps_longitude = _get_if_exist(gps_info, "GPSLongitude")
        gps_longitude_ref = _get_if_exist(gps_info, "GPSLongitudeRef")

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_dec_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_dec_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon
            # check if coordinates are sane and if not....
        if lat > 90 or lat < -90 or lon > 180 or lon < -180:
            raise Exception("No usable coordinates stored in photo")

        gps_altitude = _get_if_exist(gps_info, "GPSAltitude")
        try:
            z = [float(x) / float(y) for x, y in gps_altitude]
        except Exception:
            z = None

        gps_mapdatum = _get_if_exist(gps_info, "GPSMapDatum")
        if gps_mapdatum:
            gps_mapdatum = gps_mapdatum.rstrip()

        gps_imgdirection = _get_if_exist(gps_info, "GPSImgDirection")
        try:
            bearing = [float(x) / float(y) for x, y in gps_imgdirection]
        except Exception:
            bearing = None

        coordinates = {
            "mapdatum": gps_mapdatum,
            "lon": lon,
            "lat": lat,
            "bearing": bearing,
            "z": z,
        }
        return coordinates
    except Exception:
        return {}


def load_image_meta(image_path: str) -> dict:
    img = Image.open(image_path)
    img_exif = img.getexif()
    data = {}
    if img_exif is not None:
        for key, val in img_exif.items():
            if key in ExifTags.TAGS:
                data[key] = val
    return data
