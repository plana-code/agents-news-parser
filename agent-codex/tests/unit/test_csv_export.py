import csv
import os
import tempfile

from src.db.database import Database
from src.llm.openrouter_client import NewsItem
from src.utils.csv_exporter import export_to_csv


def test_export_to_csv_creates_file_with_rows():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "db.sqlite")
        out_csv = os.path.join(td, "out.csv")
        db = Database(path=db_path)
        url = "https://example.com"
        db.upsert_news(
            url,
            [
                NewsItem(title="T1", description="D1", publication_date="2024-01-01"),
                NewsItem(title="T2", description="D2", publication_date=None),
            ],
        )
        count = export_to_csv(db, url, out_csv)
        assert count == 2
        assert os.path.exists(out_csv)
        with open(out_csv, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        # header + 2 rows
        assert len(rows) == 3
        assert rows[0][:4] == ["id", "url", "title", "description"]
