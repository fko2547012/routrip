import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# プロジェクトを識別できる User-Agent を指定する
USER_AGENT = "routrip-student-project/0.1"


def search_places(query) -> dict:
    """
    Nominatim で場所を検索する。

    戻り値:
        {
            "results": [
                {"name": "...", "lat": 33.59, "lng": 130.40}
            ],
            "error": None
        }
    """
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
    }

    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

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
