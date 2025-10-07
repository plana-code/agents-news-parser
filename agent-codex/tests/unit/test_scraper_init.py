from src.scraper.playwright_scraper import PlaywrightScraper, DEFAULT_USER_AGENT


def test_scraper_init_defaults():
    s = PlaywrightScraper()
    assert s.headless is True
    assert isinstance(s.timeout_ms, int)
    assert "Mozilla/5.0" in DEFAULT_USER_AGENT
