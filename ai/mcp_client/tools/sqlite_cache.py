"""
SQLite 精确缓存

- 以问答对形式进行精确匹配缓存（key=问题全文）。
- 线程安全：使用 sqlite3 内置的串行化，简单用法足够。
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Optional
from datetime import datetime


class SqliteExactCache:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_cache (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT UNIQUE,
                  answer TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_question ON qa_cache(question)")
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)

    def get(self, question: str) -> Optional[str]:
        with self._lock, self._connect() as conn:
            cur = conn.execute("SELECT answer FROM qa_cache WHERE question = ?", (question,))
            row = cur.fetchone()
            return row[0] if row else None

    def put(self, question: str, answer: str) -> None:
        if not question or not isinstance(answer, str):
            return
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO qa_cache(question, answer, created_at) VALUES(?, ?, ?)",
                (question, answer, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def clear(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM qa_cache")
            conn.commit()


