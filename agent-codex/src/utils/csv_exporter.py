import csv
import logging
from src.db.database import Database


def export_to_csv(db: Database, url: str, path: str) -> int:
    rows = db.query_by_url(url)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "url",
                "title",
                "description",
                "publication_date",
                "created_at",
                "updated_at",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.id,
                    r.url,
                    r.title,
                    r.description,
                    r.publication_date or "",
                    r.created_at,
                    r.updated_at,
                ]
            )
    count = len(rows)
    logging.getLogger(__name__).info(
        "CSV exported: url=%s rows=%s path=%s", url, count, path
    )
    return count
