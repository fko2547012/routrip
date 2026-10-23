import math

from django.http import JsonResponse
from django.db.models import Q

from routrip.models import Log, Logcard, Spot
from routrip.utils.geocode import search_places
from routrip.utils.spot import find_nearby_spots


def _login_required_json(request):
    """
    未ログインの場合は JSON の401を返す。
    リダイレクトは行わない。
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "ログインが必要です"},
            status=401,
        )

    return None


def search_spots(request):
    """
    GET /spots/search/?q=福岡市
    場所を外部サービスで検索する。
    """
    auth_error = _login_required_json(request)
    if auth_error:
        return auth_error

    if request.method != "GET":
        return JsonResponse(
            {"error": "GETリクエストを使用してください"},
            status=405,
        )

    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse(
            {"error": "検索キーワードを入力してください"},
            status=400,
        )

    result = search_places(query)

    # 検索失敗時も、ユーティリティの戻り値をJSONで返す
    if result["error"]:
        return JsonResponse(result, status=502)

    return JsonResponse(result)


def nearby_spots(request):
    """
    GET /spots/nearby/?lat=35.6812&lng=139.7671&radius=100
    登録済みスポットを近い順に返す。
    """
    auth_error = _login_required_json(request)
    if auth_error:
        return auth_error

    if request.method != "GET":
        return JsonResponse(
            {"error": "GETリクエストを使用してください"},
            status=405,
        )

    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
        radius_m = float(request.GET.get("radius", 100))

        if not all(map(math.isfinite, (lat, lng, radius_m))):
            raise ValueError

        if not -90 <= lat <= 90:
            raise ValueError

        if not -180 <= lng <= 180:
            raise ValueError

        if not 0 < radius_m <= 100_000:
            raise ValueError

    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"error": "lat、lng、radiusの値が不正です"},
            status=400,
        )

    nearby = find_nearby_spots(lat, lng, radius_m)

    results = [
        {
            "id": spot.id,
            "name": spot.name,
            "lat": spot.latitude,
            "lng": spot.longitude,
            "distance_m": round(distance_m, 1),
        }
        for spot, distance_m in nearby
    ]

    return JsonResponse({"results": results})


def suggest_spots(request):
    """
    GET /spots/suggest/?q=東京&kind=start
    既存の公開ログで使われているスポット名を候補として返す。

    kind:
        start = ログの出発スポット
        dest  = ログカードのスポット
        省略  = どちらも
    """
    if request.method != "GET":
        return JsonResponse(
            {"error": "GETリクエストを使用してください"},
            status=405,
        )

    query = request.GET.get("q", "").strip()
    kind = request.GET.get("kind", "").strip()

    if kind not in ("", "start", "dest"):
        return JsonResponse(
            {"error": "kindはstartまたはdestを指定してください"},
            status=400,
        )

    # 公開ユーザーのログで使われているスポットだけに限定する
    public_start_ids = Log.objects.filter(
        user__is_public=True
    ).values_list("start_spot_id", flat=True)

    public_dest_ids = Logcard.objects.filter(
        log__user__is_public=True
    ).values_list("spot_id", flat=True)

    spots = Spot.objects.all()

    if kind == "start":
        spots = spots.filter(id__in=public_start_ids)
    elif kind == "dest":
        spots = spots.filter(id__in=public_dest_ids)
    else:
        spots = spots.filter(
            Q(id__in=public_start_ids)
            | Q(id__in=public_dest_ids)
        )

    if query:
        spots = spots.filter(name__icontains=query)

    spots = spots.order_by("name", "id").distinct()[:10]

    results = [
        {
            "id": spot.id,
            "name": spot.name,
        }
        for spot in spots
    ]

    return JsonResponse({"results": results})

def resolve_spot(request):
    """
    ログ作成用のスポット解決API（仮版）。

    正式実装では、DB検索と座標からの逆引きを行う。
    現段階では画面側の開発用に固定値を返す。
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "ログインが必要です"},
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "GETリクエストを使用してください"},
            status=405,
        )

    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])

        if not math.isfinite(lat) or not math.isfinite(lng):
            raise ValueError

        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError

    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"error": "緯度・経度の指定が不正です"},
            status=400,
        )

    # 仮版：画面側の動作確認用の固定値
    return JsonResponse({
        "source": "reverse",
        "spot": None,
        "name": "テスト地点",
        "address": "テスト住所",
        "error": None,
    })