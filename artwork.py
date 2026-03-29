"""
iTunes Search API ile album kapagi ve Apple Music linki alir.
Sadece stdlib kullanir. Sistem diline gore dogru magaza kodunu kullanir.
"""
import asyncio
import ctypes
import json
import urllib.request
import urllib.parse
import logging
from typing import Optional, NamedTuple

log = logging.getLogger(__name__)

ITUNES_API = "https://itunes.apple.com/search"


def _detect_storefront() -> str:
    """
    Windows sistem dilinden Apple Music magaza kodu uretir.
    ornek: tr-TR -> 'tr', en-US -> 'us', de-DE -> 'de'
    """
    try:
        buf = ctypes.create_unicode_buffer(85)
        ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)
        locale_name = buf.value  # ornek: 'tr-TR'
        if "-" in locale_name:
            country = locale_name.split("-")[-1].lower()
            log.info(f"iTunes magaza kodu: {country} (sistem dili: {locale_name})")
            return country
    except Exception:
        pass
    log.info("Sistem dili okunamadi, varsayilan: us")
    return "us"


# Uygulama baslarken bir kez tespit et
STOREFRONT: str = _detect_storefront()


class TrackInfo(NamedTuple):
    artwork_url: Optional[str]
    apple_music_url: Optional[str]


_cache: dict[str, TrackInfo] = {}


async def get_track_info(
    title: str,
    artist: str = "",
    album: str = "",
    size: int = 512,
) -> TrackInfo:
    cache_key = f"{title}|{artist}"
    if cache_key in _cache:
        return _cache[cache_key]

    # Once yereli magaza, bulamazsa global (us) ile dene
    storefronts = [STOREFRONT] if STOREFRONT != "us" else ["us"]
    if STOREFRONT != "us":
        storefronts.append("us")

    queries = []
    if artist:
        queries.append(f"{artist} {title}")
    queries.append(title)

    for storefront in storefronts:
        for query in queries:
            info = await asyncio.to_thread(_fetch_itunes, query, size, storefront)
            if info.artwork_url or info.apple_music_url:
                _cache[cache_key] = info
                return info

    empty = TrackInfo(None, None)
    _cache[cache_key] = empty
    return empty


def _fetch_itunes(query: str, size: int, country: str) -> TrackInfo:
    params = urllib.parse.urlencode({
        "term": query,
        "media": "music",
        "limit": "5",
        "entity": "song",
        "country": country,
    })
    url = f"{ITUNES_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if not results:
            return TrackInfo(None, None)
        hit = results[0]
        artwork = hit.get("artworkUrl100", "")
        if artwork:
            artwork = artwork.replace("100x100bb", f"{size}x{size}bb")
        # trackViewUrl'den uo=4 affiliate parametresini temizle
        track_url = hit.get("trackViewUrl", "").split("&uo=")[0]
        return TrackInfo(artwork or None, track_url or None)
    except Exception as e:
        log.debug(f"iTunes API hatasi ({country}): {e}")
        return TrackInfo(None, None)
