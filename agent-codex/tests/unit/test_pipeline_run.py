import os
import tempfile

from src.db.database import Database
from src.llm.openrouter_client import NewsItem
from src.services import pipeline as pl


class DummyScrapeResult:
    def __init__(self, url, html):
        self.url = url
        self.html = html


def test_run_pipeline_monkeypatched(monkeypatch):
    # Patch scraper.scrape to avoid Playwright
    def fake_scrape(self, url):
        return DummyScrapeResult(
            url, "<html><article>Title AAA long text for extraction</article></html>"
        )

    monkeypatch.setattr(pl.PlaywrightScraper, "scrape", fake_scrape)

    # Patch LLM to avoid network
    def fake_extract(html):
        return [NewsItem(title="AAA", description="BBB", publication_date=None)]

    monkeypatch.setattr(pl, "extract_news_from_html", lambda html: fake_extract(html))

    with tempfile.TemporaryDirectory() as td:
        db = Database(path=os.path.join(td, "db.sqlite"))
        url = "https://example.com"
        items = pl.run_pipeline(url, db)
        assert len(items) == 1
        rows = db.query_by_url(url)
        assert len(rows) == 1
        assert rows[0].title == "AAA"
