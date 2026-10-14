
import math

from routrip.models import Spot


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    """
    2地点間の距離をハバースイン公式で計算する。
    戻り値はメートル。
    """
    earth_radius = 6_371_000  # 地球の半径（m）

    # 緯度・経度をラジアンに変換
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # 緯度・経度の差
    delta_lat = lat2_rad - lat1_rad
    delta_lng = lng2_rad - lng1_rad

    # ハバースイン公式
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lng / 2) ** 2
    )

    # 浮動小数点誤差によって a が範囲外になるのを防ぐ
    a = max(0.0, min(1.0, a))

    central_angle = 2 * math.asin(math.sqrt(a))

    return earth_radius * central_angle


def find_nearby_spots(lat, lng, radius_m=100) -> list:
    """
    指定された緯度・経度から半径 radius_m 以内にある
    Spot を取得し、距離の近い順に返す。

    戻り値:
        [(spot, distance_m), ...]
    """
    # 緯度1度あたりの距離を約111,000mとして、
    # まず検索対象を矩形範囲に絞り込む
    lat_delta = radius_m / 111_000

    # 経度1度あたりの距離は緯度によって変わる
    cos_lat = math.cos(math.radians(lat))

    # 極付近では経度方向の距離が非常に小さくなる
    if abs(cos_lat) < 1e-12:
        lng_delta = 180
    else:
        lng_delta = min(180, radius_m / (111_000 * abs(cos_lat)))

    candidates = Spot.objects.filter(
        latitude__gte=lat - lat_delta,
        latitude__lte=lat + lat_delta,
        longitude__gte=lng - lng_delta,
        longitude__lte=lng + lng_delta,
    )

    # 矩形範囲に入った候補に対して、正確な距離を計算する
    nearby_spots = []

    for spot in candidates:
        distance_m = haversine_m(
            lat,
            lng,
            spot.latitude,
            spot.longitude,
        )

        if distance_m <= radius_m:
            nearby_spots.append((spot, distance_m))

    # 距離の近い順に並べる
    nearby_spots.sort(key=lambda item: item[1])

    return nearby_spots


def delete_unused_spots(spot_ids) -> int:
    """
    ログ、ログカード、区間から参照されていない Spot だけを削除する。

    戻り値:
        削除した Spot の件数
    """
    deleted_count = 0

    for spot in Spot.objects.filter(pk__in=spot_ids).distinct():
        # Log.start_spot から参照されているか
        is_used_as_start = spot.start_logs.exists()

        # Logcard.spot から参照されているか
        is_used_by_cards = spot.log_cards.exists()

        # Section.from_spot から参照されているか
        is_used_as_departure = spot.departing_sections.exists()

        # Section.to_spot から参照されているか
        is_used_as_arrival = spot.arriving_sections.exists()

        # どこからも参照されていなければ削除
        if not (
            is_used_as_start
            or is_used_by_cards
            or is_used_as_departure
            or is_used_as_arrival
        ):
            spot.delete()
            deleted_count += 1

    return deleted_count
