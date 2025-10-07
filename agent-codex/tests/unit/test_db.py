import os
import tempfile

from src.db.database import Database
from src.llm.openrouter_client import NewsItem


def test_db_insert_and_query():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "test.db")
        db = Database(path=db_path)
        url = "https://example.com"

        items = [
            NewsItem(title="T1", description="D1", publication_date="2024-01-01"),
            NewsItem(title="T2", description="D2", publication_date=None),
        ]
        count = db.upsert_news(url, items)
        assert count == 2

        # Upsert same title updates, not duplicates
        items2 = [NewsItem(title="T1", description="D1-updated", publication_date=None)]
        count2 = db.upsert_news(url, items2)
        assert count2 >= 1

        rows = db.query_by_url(url)
        titles = [r.title for r in rows]
        assert "T1" in titles and "T2" in titles
