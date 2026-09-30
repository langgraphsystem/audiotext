"""
Photo posts: TikTok photomode and Instagram image carousels.

Such a post has no video stream at all, so the key-frame extractor has nothing
to work with. The slides *are* the content here — they are downloaded and go to
the model in place of frames, together with the caption.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yt_dlp
from yt_dlp.networking import Request

from .config import settings
from .logger import get_logger
from .utils import (
    USER_AGENT,
    base_ydl_opts,
    detect_platform,
    extract_raw_info,
    is_photo_post_url,
    resolve_short_link,
    safe_filename,
)
from .vision import normalize_image

logger = get_logger(__name__)

# TikTok keeps the slide list in the page's rehydration blob
TIKTOK_DATA_REGEX = re.compile(
    r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(\{.*?\})</script>',
    re.DOTALL,
)

REFERERS = {
    'instagram': 'https://www.instagram.com/',
    'tiktok': 'https://www.tiktok.com/',
}


def looks_like_photo_post(url: str, info: Optional[Dict[str, Any]] = None) -> bool:
    """Whether the post carries slides instead of a video track."""
    if is_photo_post_url(url):
        return True

    if not info:
        return False

    # A processed video result always has formats or a direct url
    if info.get('formats') or info.get('requested_formats') or info.get('url'):
        return False

    return bool(info.get('thumbnails') or info.get('thumbnail'))


def _best_thumbnail(entry: Dict[str, Any]) -> Optional[str]:
    """Pick the largest still image of a carousel entry."""
    thumbnails = [t for t in (entry.get('thumbnails') or []) if t.get('url')]
    if thumbnails:
        return max(thumbnails, key=lambda t: t.get('width') or 0)['url']
    return entry.get('thumbnail')


def _instagram_slide_urls(url: str) -> List[str]:
    """Slide images of an Instagram post, one per carousel item."""
    info = extract_raw_info(url)
    if not info:
        return []

    entries = info.get('entries') if info.get('_type') == 'playlist' else [info]
    urls: List[str] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        image_url = _best_thumbnail(entry)
        if image_url and image_url not in urls:
            urls.append(image_url)

    return urls


def _tiktok_slide_urls(url: str, ydl: yt_dlp.YoutubeDL) -> List[str]:
    """Slide images of a TikTok photomode post.

    yt-dlp exposes the slideshow's music but not its images, so the page's own
    data blob is the only source.
    """
    try:
        request = Request(url, headers={
            'User-Agent': USER_AGENT,
            'Referer': REFERERS['tiktok'],
        })
        with ydl.urlopen(request) as response:
            html = response.read().decode('utf-8', 'replace')
    except Exception as e:
        logger.warning(f"Страницу поста прочитать не удалось: {e}")
        return []

    match = TIKTOK_DATA_REGEX.search(html)
    if not match:
        logger.warning("В странице нет данных о слайдах")
        return []

    try:
        data = json.loads(match.group(1))
        item = (data.get('__DEFAULT_SCOPE__', {})
                    .get('webapp.video-detail', {})
                    .get('itemInfo', {})
                    .get('itemStruct', {}))
        images = item.get('imagePost', {}).get('images') or []
    except Exception as e:
        logger.warning(f"Данные о слайдах не разобрались: {e}")
        return []

    urls: List[str] = []
    for image in images:
        candidates = (image.get('imageURL') or {}).get('urlList') or []
        if candidates:
            urls.append(candidates[0])

    return urls


def slide_image_urls(url: str, ydl: yt_dlp.YoutubeDL) -> List[str]:
    """Every slide image of a photo post, in order."""
    platform = detect_platform(url)
    if platform == 'instagram':
        return _instagram_slide_urls(url)
    if platform == 'tiktok':
        # The slide data lives on the post's own /photo/ page
        return _tiktok_slide_urls(resolve_short_link(url), ydl)
    return []


def download_slides(
    url: str, limit: Optional[int] = None
) -> Tuple[List[Path], List[Path]]:
    """Download the slides of a photo post as JPEGs ready for the model.

    Returns (slides for the model, every file created) so the caller can clean
    up the raw downloads as well.
    """
    limit = limit or settings.vision_max_slides
    if limit <= 0:
        return [], []

    workdir = settings.workdir
    workdir.mkdir(parents=True, exist_ok=True)
    platform = detect_platform(url) or 'media'
    stem = safe_filename(f"{platform}_{url.rstrip('/').split('/')[-1]}")

    created: List[Path] = []
    slides: List[Path] = []

    try:
        with yt_dlp.YoutubeDL(base_ydl_opts(url)) as ydl:
            image_urls = slide_image_urls(url, ydl)
            if not image_urls:
                return [], []

            logger.info(f"Слайдов в публикации: {len(image_urls)}")

            for index, image_url in enumerate(image_urls[:limit]):
                raw_path = workdir / f"{stem}_raw{index:02d}"
                try:
                    request = Request(image_url, headers={
                        'User-Agent': USER_AGENT,
                        'Referer': REFERERS.get(platform, ''),
                    })
                    with ydl.urlopen(request) as response:
                        raw_path.write_bytes(response.read())
                except Exception as e:
                    logger.warning(f"Слайд {index + 1} не скачался: {e}")
                    continue

                created.append(raw_path)
                prepared = normalize_image(raw_path, index)
                if prepared:
                    if prepared not in created:
                        created.append(prepared)
                    slides.append(prepared)
    except Exception as e:
        logger.warning(f"Слайды скачать не удалось: {e}")

    logger.info(f"Готовых слайдов: {len(slides)}")
    return slides, created
