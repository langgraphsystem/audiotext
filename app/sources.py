"""
Tracked accounts: turning an account spec into a list of recent posts.

yt-dlp can enumerate a profile as a playlist, so a flat listing gives the
recent post URLs without downloading anything.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

import yt_dlp

from .config import settings
from .logger import get_logger
from .utils import base_ydl_opts, detect_platform, platform_title

logger = get_logger(__name__)

PROFILE_TEMPLATES = {
    'tiktok': "https://www.tiktok.com/@{handle}",
    'instagram': "https://www.instagram.com/{handle}/",
}


@dataclass
class Account:
    """A tracked account."""
    platform: str
    handle: str
    url: str

    @property
    def label(self) -> str:
        return f"{platform_title(self.platform)} @{self.handle}"


@dataclass
class PostRef:
    """A post discovered on an account, before any downloading."""
    url: str
    post_id: str
    title: str


def parse_account(spec: str) -> Optional[Account]:
    """Parse "tiktok:@user", "instagram:user" or a full profile URL."""
    spec = spec.strip()
    if not spec:
        return None

    # Prefixed form
    match = re.match(r'^(tiktok|instagram)\s*:\s*@?([\w.\-]+)$', spec, re.IGNORECASE)
    if match:
        platform = match.group(1).lower()
        handle = match.group(2)
        return Account(platform, handle, PROFILE_TEMPLATES[platform].format(handle=handle))

    # URL form
    platform = detect_platform(spec)
    if not platform:
        logger.warning(f"Не понял аккаунт: {spec}")
        return None

    url = spec if '://' in spec else f"https://{spec}"
    if platform == 'tiktok':
        m = re.search(r'@([\w.\-]+)', url)
    else:
        m = re.search(r'instagram\.com/([\w.\-]+)', url)

    handle = m.group(1) if m else url.rstrip('/').split('/')[-1]
    return Account(platform, handle, url)


def tracked_accounts() -> List[Account]:
    """Every account listed in SOURCE_ACCOUNTS."""
    accounts = [parse_account(spec) for spec in settings.accounts]
    return [a for a in accounts if a]


def list_recent_posts(account: Account, limit: Optional[int] = None) -> List[PostRef]:
    """List the account's most recent posts without downloading them."""
    limit = limit or settings.source_max_items_per_account

    opts = {
        **base_ydl_opts(account.url),
        'skip_download': True,
        'extract_flat': 'in_playlist',
        'playlistend': limit,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(account.url, download=False)
    except Exception as e:
        logger.error(f"Не удалось получить ленту {account.label}: {e}")
        return []

    entries = (info or {}).get('entries') or []
    posts: List[PostRef] = []

    for entry in entries[:limit]:
        if not entry:
            continue
        url = entry.get('url') or entry.get('webpage_url')
        post_id = str(entry.get('id') or '')
        if not url and post_id and account.platform == 'tiktok':
            url = f"{account.url}/video/{post_id}"
        if not url:
            continue
        posts.append(PostRef(url=url, post_id=post_id, title=entry.get('title') or ''))

    logger.info(f"{account.label}: найдено {len(posts)} последних публикаций")
    return posts
