"""
Export collected material as a file for content production.

The bot only collects and analyzes; producing posts, scripts and captions
happens in the Claude desktop app, so the material is handed over as one
self-contained Markdown file.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings
from .logger import get_logger
from .storage import get_storage
from .utils import platform_title

logger = get_logger(__name__)

# Transcripts can be long; keep the digest readable
TRANSCRIPT_LIMIT = 4000


def _format_number(value: Optional[int]) -> str:
    if not value:
        return "—"
    return f"{value:,}".replace(",", " ")


def _post_section(post: Dict[str, Any], index: int) -> str:
    """Render one collected post."""
    lines = [
        f"## {index}. {post.get('title') or 'Без заголовка'}",
        "",
        f"- **Платформа:** {platform_title(post.get('platform'))}",
        f"- **Аккаунт:** @{post.get('account')}",
        f"- **Ссылка:** {post.get('url')}",
    ]

    if post.get("upload_date"):
        lines.append(f"- **Опубликовано:** {post['upload_date']}")
    if post.get("duration"):
        lines.append(f"- **Длительность:** {int(post['duration'])} с")

    metrics = [
        f"просмотры {_format_number(post.get('view_count'))}",
        f"лайки {_format_number(post.get('like_count'))}",
        f"комментарии {_format_number(post.get('comment_count'))}",
    ]
    lines.append(f"- **Метрики:** {', '.join(metrics)}")

    if post.get("track"):
        lines.append(f"- **Трек:** {post['track']}")

    if post.get("tags"):
        try:
            tags = json.loads(post["tags"])
            if tags:
                lines.append(f"- **Хештеги:** {', '.join(tags)}")
        except Exception:
            pass

    if post.get("frames"):
        lines.append(f"- **Разобрано кадров:** {post['frames']}")

    if post.get("description"):
        lines += ["", "### Описание публикации", "", post["description"].strip()]

    transcript = (post.get("transcript") or "").strip()
    if transcript:
        clipped = transcript[:TRANSCRIPT_LIMIT]
        if len(transcript) > TRANSCRIPT_LIMIT:
            clipped += "\n\n[…транскрипт обрезан]"
        lines += ["", "### Расшифровка", "", clipped]
    else:
        lines += ["", "### Расшифровка", "", "_Речи нет — разбор построен на кадрах._"]

    analysis = (post.get("analysis") or "").strip()
    if analysis:
        lines += ["", "### Разбор", "", analysis]

    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def build_digest(limit: int = 20, account: Optional[str] = None) -> str:
    """Build the Markdown digest of recently collected posts."""
    storage = get_storage()
    posts = storage.recent_posts(limit=limit, account=account)
    stats = storage.stats()

    header = [
        f"# Материал для производства контента — {settings.brand_name}",
        "",
        f"Сформировано: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Публикаций в выгрузке: {len(posts)}",
        f"Всего собрано в базе: {stats['ok']}",
    ]

    if stats["per_account"]:
        by_account = ", ".join(f"@{a} — {c}" for a, c in stats["per_account"].items())
        header.append(f"По аккаунтам: {by_account}")

    header += [
        "",
        "Каждая публикация ниже содержит данные площадки, расшифровку речи и разбор,",
        "включающий визуальный ряд. Используйте это как исходный материал:",
        "ищите повторяющиеся приёмы, работающие заходы и темы, а затем готовьте",
        "собственные сценарии и тексты.",
        "",
        "---",
        "",
    ]

    if not posts:
        header.append("_База пуста: сбор ещё не запускался или не нашёл публикаций._")
        return "\n".join(header)

    sections = [_post_section(post, i) for i, post in enumerate(posts, start=1)]
    return "\n".join(header) + "\n".join(sections)


def write_digest(limit: int = 20, account: Optional[str] = None) -> Path:
    """Write the digest to a file and return its path."""
    content = build_digest(limit=limit, account=account)
    filename = f"content_material_{int(time.time())}.md"
    path = settings.workdir / filename
    path.write_text(content, encoding="utf-8")
    logger.info(f"Выгрузка готова: {path.name} ({len(content)} символов)")
    return path


def export_json(limit: int = 50) -> Path:
    """Write the same material as JSON, for tooling that prefers structure."""
    posts: List[Dict[str, Any]] = get_storage().recent_posts(limit=limit)
    path = settings.workdir / f"content_material_{int(time.time())}.json"
    path.write_text(
        json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
