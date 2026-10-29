import io
import os
from django.core.files.base import ContentFile
from datetime import datetime
from PIL import Image, ExifTags, UnidentifiedImageError, ImageOps

def _to_decimal_degrees(dms, reference):
    """
    度・分・秒を10進数の緯度・経度に変換する。
    南緯・西経はマイナスにする。
    """
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])

    decimal = degrees + minutes / 60 + seconds / 3600

    if reference in ("S", "W"):
        decimal = -decimal

    return decimal


def get_photo_info(file) -> dict:
    """
    画像から GPS 座標と撮影日時を取得する。

    戻り値:
        {
            "lat": float または None,
            "lng": float または None,
            "taken_at": datetime または None
        }

    file は Django のアップロードファイルを想定する。
    """
    result = {
        "lat": None,
        "lng": None,
        "taken_at": None,
    }

    try:
        with Image.open(file) as image:
            exif = image.getexif()

            # GPS 情報の読み取り
            try:
                gps_ifd = exif.get_ifd(0x8825)

                gps_lat_ref = gps_ifd.get(1)
                gps_lat = gps_ifd.get(2)
                gps_lng_ref = gps_ifd.get(3)
                gps_lng = gps_ifd.get(4)

                if (
                    gps_lat_ref
                    and gps_lat
                    and gps_lng_ref
                    and gps_lng
                ):
                    if isinstance(gps_lat_ref, bytes):
                        gps_lat_ref = gps_lat_ref.decode("ascii")

                    if isinstance(gps_lng_ref, bytes):
                        gps_lng_ref = gps_lng_ref.decode("ascii")

                    result["lat"] = _to_decimal_degrees(
                        gps_lat, gps_lat_ref
                    )
                    result["lng"] = _to_decimal_degrees(
                        gps_lng, gps_lng_ref
                    )

            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                pass

            # 撮影日時を取得
            try:
                exif_ifd = exif.get_ifd(0x8769)
                date_string = exif_ifd.get(36867)  # DateTimeOriginal

                if not date_string:
                    date_string = exif.get(306)  # DateTime

                if isinstance(date_string, bytes):
                    date_string = date_string.decode("ascii")

                if date_string:
                    result["taken_at"] = datetime.strptime(
                        date_string,
                        "%Y:%m:%d %H:%M:%S",
                    )

            except (KeyError, TypeError, ValueError):
                pass

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        TypeError,
    ):
        # EXIFがない、画像形式に対応していないなどの場合
        pass

    finally:
        # 読み取り後にファイル位置を先頭へ戻す
        try:
            file.seek(0)
        except (AttributeError, OSError):
            pass

    return result


MAX_EDGE = 2000        # 長辺の上限（ピクセル）
JPEG_QUALITY = 85      # JPEGの品質（1〜95。大きいほど、きれいで、重い）

def shrink_photo(uploaded):
    """
    写真を、長辺 MAX_EDGE px 以内の JPEG に縮小して返す。
    うまく読めなかったときは、元のファイルを、そのまま返す。
    """
    try:
        uploaded.seek(0)
        img = Image.open(uploaded)
        img = ImageOps.exif_transpose(img)      # 向きを、見た目どおりに直す（EXIFは、消えるため）
        img.thumbnail((MAX_EDGE, MAX_EDGE))     # 縦横比を保って縮小（小さい写真は、そのまま）

        if img.mode in ('RGBA', 'LA', 'P'):     # 透明部分は、白にする
            img = img.convert('RGBA')
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    except Exception:
        uploaded.seek(0)
        return uploaded

    name = os.path.splitext(uploaded.name)[0] + '.jpg'
    return ContentFile(buffer.getvalue(), name=name)
