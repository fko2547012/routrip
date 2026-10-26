import hashlib
import json
import threading
import time

import requests
from django.core.cache import cache


NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "routrip-student-project/0.1"

# キャッシュの有効期間：24時間
CACHE_TIMEOUT = 60 * 60 * 24

# 外部サービスへの問い合わせ間隔（秒）
REQUEST_INTERVAL = 1.0

# このプロセス内で、検索と逆引きの通信を共通管理する
_request_lock = threading.Lock()
_last_request_time = 0.0


def _make_cache_key(kind, value):
    """検索内容からキャッシュキーを生成する。"""
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"routrip:geocode:{kind}:{digest}"


def _request_nominatim(endpoint, params, cache_key):
    """
    キャッシュに結果がなければNominatimへ問い合わせる。

    同じプロセス内では通信を直列化し、問い合わせ開始時刻の
    間隔を1秒以上空ける。
    """
    global _last_request_time

    # まずキャッシュを確認
    data = cache.get(cache_key)
    if data is not None:
        return data

    with _request_lock:
        # ロックを待っている間にキャッシュされた可能性がある
        data = cache.get(cache_key)
        if data is not None:
            return data

        # 前回の問い合わせ開始から1秒以上空ける
        elapsed = time.monotonic() - _last_request_time
        remaining = REQUEST_INTERVAL - elapsed

        if remaining > 0:
            time.sleep(remaining)

        # 問い合わせ開始時刻を記録
        _last_request_time = time.monotonic()

        response = requests.get(
            f"{NOMINATIM_URL}/{endpoint}",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        # 正常に取得できた結果をキャッシュ
        cache.set(cache_key, data, timeout=CACHE_TIMEOUT)

        return data


def search_places(query) -> dict:
    """Nominatimで場所を検索する。"""
    query = (query or "").strip()

    if not query:
        return {
            "results": [],
            "error": "検索キーワードを入力してください",
        }

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 5,
        "accept-language": "ja",
        "addressdetails": 1,
    }

    try:
        data = _request_nominatim(
            "search",
            params,
            _make_cache_key("search", query.casefold()),
        )

        results = []

        for item in data:
            display_name = item.get("display_name", "")
            name = item.get("name") or display_name.split(",")[0].strip()

            try:
                latitude = float(item["lat"])
                longitude = float(item["lon"])
            except (KeyError, TypeError, ValueError):
                continue

            results.append({
                "name": name,
                "lat": latitude,
                "lng": longitude,
                "address": display_name,
            })

        return {
            "results": results,
            "error": None,
        }

    except (requests.RequestException, ValueError):
        return {
            "results": [],
            "error": "検索できませんでした",
        }


def reverse_place(lat, lng) -> dict:
    """緯度・経度から場所の名前と住所を取得する。"""
    error_message = "場所の名前を取得できませんでした"

    try:
        latitude = float(lat)
        longitude = float(lng)

        if (
            not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError("緯度・経度が範囲外です")

        # 小数点以下4桁に丸めた座標をキャッシュキーに使う
        rounded_coordinates = [
            round(latitude, 4),
            round(longitude, 4),
        ]

        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "accept-language": "ja",
            "zoom": 18,
        }

        data = _request_nominatim(
            "reverse",
            params,
            _make_cache_key("reverse", rounded_coordinates),
        )

        display_name = data.get("display_name", "")
        if not display_name:
            return {
                "place": None,
                "error": error_message,
            }

        name = data.get("name") or display_name.split(",")[0].strip()

        try:
            result_lat = float(data["lat"])
            result_lng = float(data["lon"])
        except (KeyError, TypeError, ValueError):
            return {
                "place": None,
                "error": error_message,
            }

        return {
            "place": {
                "name": name,
                "address": display_name,
                "lat": result_lat,
                "lng": result_lng,
            },
            "error": None,
        }

    except (requests.RequestException, ValueError, TypeError):
        return {
            "place": None,
            "error": error_message,
        }
