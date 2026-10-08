import math
from models import Spot

SEARCH_RADIUS = 100

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371000

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def find_nearby_spots(latitude, longitude):

    spots = Spot.objects.all()

    nearby_spots = []

    for spot in spots:
        distance = calculate_distance(
            latitude,
            longitude,
            spot.latitude,
            spot.longitude
        )

        if distance <= SEARCH_RADIUS:
            nearby_spots.append({
                "spot": spot,
                "distance": distance,
            })

    return nearby_spots