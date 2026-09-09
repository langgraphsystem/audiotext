"""
SQLite storage for collected posts.

Keeps what the collector already processed (so nothing is downloaded or
analyzed twice) and holds the material that later gets exported for
content production.
"""
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    url           TEXT PRIMARY KEY,
    platform      TEXT,
    account       TEXT,
    video_id      TEXT,
    title         TEXT,
    description   TEXT,
    uploader      TEXT,
    duration      REAL,
    view_count    INTEGER,
    like_count    INTEGER,
    comment_count INTEGER,
    upload_date   TEXT,
    track         TEXT,
    tags          TEXT,
    transcript    TEXT,
    analysis      TEXT,
    frames        INTEGER DEFAULT 0,
    status        TEXT DEFAULT 'ok',
    error         TEXT,
    processed_at  REAL
);
CREATE INDEX IF NOT EXISTS idx_posts_account ON posts(account);
CREATE INDEX IF NOT EXISTS idx_posts_processed ON posts(processed_at);
"""


class Storage:
    """Thread-safe SQLite wrapper (the bot writes from worker threads)."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or settings.database_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        logger.info(f"Хранилище готово: {self.path}")

    def is_known(self, url: str) -> bool:
        """Whether this post was already collected."""
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM posts WHERE url = ?", (url,)
            ).fetchone()
        return row is not None

    def known_urls(self, urls: List[str]) -> set:
        """Subset of the given URLs that is already stored."""
        if not urls:
            return set()
        placeholders = ",".join("?" for _ in urls)
        with self._lock:
            rows = self._conn.execute(
                f"SELECT url FROM posts WHERE url IN ({placeholders})", urls
            ).fetchall()
        return {r["url"] for r in rows}

    def save_post(
        self,
        url: str,
        platform: str,
        account: str,
        metadata: Optional[Dict[str, Any]] = None,
        transcript: str = "",
        analysis: str = "",
        frames: int = 0,
        status: str = "ok",
        error: Optional[str] = None,
    ) -> None:
        """Insert or replace a collected post."""
        metadata = metadata or {}
        tags = metadata.get("tags")

        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO posts (
                    url, platform, account, video_id, title, description, uploader,
                    duration, view_count, like_count, comment_count, upload_date,
                    track, tags, transcript, analysis, frames, status, error,
                    processed_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    url,
                    platform,
                    account,
                    metadata.get("id"),
                    metadata.get("title"),
                    metadata.get("description"),
                    metadata.get("uploader"),
                    metadata.get("duration"),
                    metadata.get("view_count"),
                    metadata.get("like_count"),
                    metadata.get("comment_count"),
                    metadata.get("upload_date"),
                    metadata.get("track"),
                    json.dumps(tags, ensure_ascii=False) if tags else None,
                    transcript,
                    analysis,
                    frames,
                    status,
                    error,
                    time.time(),
                ),
            )
            self._conn.commit()

    def recent_posts(self, limit: int = 20, account: Optional[str] = None) -> List[Dict[str, Any]]:
        """Most recently collected posts, newest first."""
        query = "SELECT * FROM posts WHERE status = 'ok'"
        params: List[Any] = []
        if account:
            query += " AND account = ?"
            params.append(account)
        query += " ORDER BY processed_at DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        """Counts for the status command."""
        with self._lock:
            total = self._conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
            ok = self._conn.execute(
                "SELECT COUNT(*) c FROM posts WHERE status = 'ok'"
            ).fetchone()["c"]
            per_account = self._conn.execute(
                "SELECT account, COUNT(*) c FROM posts WHERE status = 'ok' "
                "GROUP BY account ORDER BY c DESC"
            ).fetchall()
            last = self._conn.execute(
                "SELECT MAX(processed_at) t FROM posts"
            ).fetchone()["t"]

        return {
            "total": total,
            "ok": ok,
            "failed": total - ok,
            "per_account": {r["account"]: r["c"] for r in per_account if r["account"]},
            "last_processed_at": last,
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()


_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """Process-wide storage singleton."""
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
