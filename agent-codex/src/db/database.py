import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from src.llm.openrouter_client import NewsItem


DEFAULT_DB_PATH = os.getenv("NEWS_DB_PATH", os.path.join("data", "news.db"))


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


@dataclass
class Row:
    id: int
    url: str
    title: str
    description: str
    publication_date: Optional[str]
    created_at: str
    updated_at: str


class Database:
    def __init__(self, path: str = DEFAULT_DB_PATH) -> None:
        self.path = path
        _ensure_dir(self.path)
        self._init_db()
        logging.getLogger(__name__).info("DB initialized at %s", self.path)

    @contextmanager
    def conn(self):  # type: ignore
        con = sqlite3.connect(self.path)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_db(self) -> None:
        with self.conn() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    publication_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(url, title)
                )
                """
            )
            con.commit()

    def upsert_news(self, url: str, items: Iterable[NewsItem]) -> int:
        now = datetime.utcnow().isoformat()
        count = 0
        with self.conn() as con:
            cur = con.cursor()
            for it in items:
                try:
                    cur.execute(
                        """
                        INSERT INTO news (url, title, description, publication_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(url, title) DO UPDATE SET
                            description=excluded.description,
                            publication_date=excluded.publication_date,
                            updated_at=excluded.updated_at
                        """,
                        (url, it.title, it.description, it.publication_date, now, now),
                    )
                    count += 1
                except sqlite3.Error:
                    # If DB is older and doesn't support upsert, fallback to manual
                    cur.execute(
                        "SELECT id FROM news WHERE url=? AND title=?",
                        (url, it.title),
                    )
                    row = cur.fetchone()
                    if row:
                        cur.execute(
                            "UPDATE news SET description=?, publication_date=?, updated_at=? WHERE id=?",
                            (it.description, it.publication_date, now, row[0]),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO news (url, title, description, publication_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                url,
                                it.title,
                                it.description,
                                it.publication_date,
                                now,
                                now,
                            ),
                        )
                        count += 1
        logging.getLogger(__name__).info(
            "DB upsert completed: url=%s, items=%s", url, count
        )
        return count

    def query_by_url(self, url: str) -> List[Row]:
        with self.conn() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, url, title, description, publication_date, created_at, updated_at FROM news WHERE url=? ORDER BY id DESC",
                (url,),
            )
            rows = cur.fetchall()
            logging.getLogger(__name__).debug(
                "DB query_by_url: url=%s rows=%s", url, len(rows)
            )
            return [
                Row(
                    id=r[0],
                    url=r[1],
                    title=r[2],
                    description=r[3],
                    publication_date=r[4],
                    created_at=r[5],
                    updated_at=r[6],
                )
                for r in rows
            ]
