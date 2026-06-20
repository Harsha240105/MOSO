from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Optional

from moso_core.realtime.models import FetchResult

logger = logging.getLogger(__name__)

DEFAULT_TTL: dict[str, int] = {
    "news": 300,
    "ai": 600,
    "security": 300,
    "market": 300,
    "crypto": 300,
    "open_source": 900,
    "software": 1800,
    "hardware": 3600,
    "documentation": 7200,
    "general": 600,
}


class ResponseCache:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, ".moso")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "realtime_cache.db")
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self):
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                url TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                parsed_text TEXT NOT NULL,
                status_code INTEGER DEFAULT 200,
                content_type TEXT DEFAULT 'text/plain',
                redirect_chain TEXT DEFAULT '[]',
                tls_verified INTEGER DEFAULT 0,
                cached_at REAL NOT NULL,
                ttl INTEGER NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_expiry
            ON response_cache(cached_at)
        """)
        self._conn.commit()

    def get(self, url: str) -> Optional[FetchResult]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM response_cache WHERE url = ?", (url,)
            ).fetchone()
        if row is None:
            return None
        row = dict(row)
        elapsed = time.time() - row["cached_at"]
        if elapsed > row["ttl"]:
            self.invalidate(url)
            logger.debug("Cache expired for %s", url)
            return None
        return FetchResult(
            url=row["url"],
            source_name=row["source_name"],
            raw_text=row["raw_text"],
            parsed_text=row["parsed_text"],
            status_code=row["status_code"],
            content_type=row["content_type"],
            redirect_chain=json.loads(row["redirect_chain"]),
            tls_verified=bool(row["tls_verified"]),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(row["cached_at"])),
        )

    def set(self, url: str, result: FetchResult, ttl: Optional[int] = None):
        if ttl is None:
            ttl = DEFAULT_TTL.get("general", 600)
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO response_cache
                   (url, source_name, raw_text, parsed_text, status_code,
                    content_type, redirect_chain, tls_verified, cached_at, ttl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    url, result.source_name, result.raw_text, result.parsed_text,
                    result.status_code, result.content_type,
                    json.dumps(result.redirect_chain),
                    int(result.tls_verified),
                    time.time(), ttl,
                ),
            )
            self._conn.commit()

    def invalidate(self, url: str):
        with self._lock:
            self._conn.execute("DELETE FROM response_cache WHERE url = ?", (url,))
            self._conn.commit()

    def clear_expired(self):
        with self._lock:
            now = time.time()
            deleted = self._conn.execute(
                "DELETE FROM response_cache WHERE ? - cached_at > ttl", (now,)
            ).rowcount
            self._conn.commit()
            if deleted:
                logger.info("Cleared %d expired cache entries", deleted)

    def clear_all(self):
        with self._lock:
            self._conn.execute("DELETE FROM response_cache")
            self._conn.commit()
            logger.info("Cleared all cached responses")

    def size(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM response_cache").fetchone()[0]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
