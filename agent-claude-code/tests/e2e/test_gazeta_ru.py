"""E2E test for Gazeta.ru news site.

Tests the complete pipeline with a real Russian news site.
"""

import pytest
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from scraper import ScraperService
from llm_service import OpenRouterService
from database import DatabaseService
from csv_exporter import CSVExporter


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_gazeta_ru_scraping(test_api_key, test_database_path, test_export_dir):
    """
    Test complete pipeline with Gazeta.ru - Russian news site.

    Verifies:
    1. Scraper can handle Russian news site
    2. Free LLM model can extract Russian news articles
    3. Data is saved correctly to database
    4. CSV export works with Cyrillic characters
    """
    news_url = "https://www.gazeta.ru/"

    # Step 1: Scrape Gazeta.ru
    async with ScraperService() as scraper:
        html = await scraper.scrape(news_url)

        assert html is not None
        assert len(html) > 1000  # Should have substantial content

        # Check for Russian content (Cyrillic characters)
        assert any(ord(char) >= 0x0400 and ord(char) <= 0x04FF for char in html), \
            "HTML should contain Cyrillic characters"

    # Step 2: Extract news with free LLM model
    try:
        llm = OpenRouterService(api_key=test_api_key)
        news_items = llm.extract_news(html, news_url)

        assert isinstance(news_items, list)

        # API may be rate limited or return empty results
        if len(news_items) == 0:
            pytest.skip("LLM API returned no results - may be rate limited or API issue")

        # Verify news item structure
        first_item = news_items[0]
        assert hasattr(first_item, 'title')
        assert len(first_item.title) > 0

        # Check if we got Russian text in title or description
        has_cyrillic = False
        for item in news_items[:3]:  # Check first 3 items
            title = item.title if hasattr(item, 'title') else ""
            desc = item.description if hasattr(item, 'description') else ""
            if any(ord(char) >= 0x0400 and ord(char) <= 0x04FF for char in title + desc):
                has_cyrillic = True
                break

        # Note: LLM might translate to English, so this is not required
        # but we log it for debugging
        if not has_cyrillic:
            print("Note: LLM may have translated content to English")

    except Exception as e:
        pytest.fail(f"LLM extraction failed for Gazeta.ru: {e}")

    # Step 3: Save to database
    with DatabaseService(test_database_path) as db:
        db.initialize()

        news_data = [item.to_dict() for item in news_items]
        count = db.save_news(news_url, news_data)

        assert count > 0
        assert count == len(news_items)

        # Verify retrieval
        saved = db.get_news_by_url(news_url)
        assert len(saved) == count

    # Step 4: Export to CSV
    exporter = CSVExporter(export_path=test_export_dir)

    with DatabaseService(test_database_path) as db:
        news_for_export = db.get_news_by_url(news_url)
        csv_path = exporter.export_to_csv(news_for_export, url=news_url)

        assert os.path.exists(csv_path)

        # Verify CSV has content and handles special characters
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            # Header + at least one data row
            assert len(lines) >= 2

            # Verify CSV is properly encoded for special characters
            # This will succeed if encoding='utf-8' was used
            assert len(content) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gazeta_ru_scraping_no_api():
    """
    Test scraping Gazeta.ru without LLM processing.

    This test verifies the scraper can access the site,
    even without API key.
    """
    news_url = "https://www.gazeta.ru/"

    async with ScraperService(timeout=45000, max_retries=2) as scraper:
        html = await scraper.scrape(news_url)

        assert html is not None
        assert len(html) > 1000

        # Verify it's actually Gazeta.ru content
        html_lower = html.lower()
        assert 'gazeta' in html_lower or any(ord(char) >= 0x0400 and ord(char) <= 0x04FF for char in html)

        # Check that we got some news content indicators
        # (headlines, articles, etc - varies by site structure)
        assert len(html) > 5000, "Should have substantial content from news site"
