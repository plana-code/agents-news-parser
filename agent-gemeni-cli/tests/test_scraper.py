
from src.scraper import scrape_url

def test_scrape_url():
    """Tests if the scrape_url function returns a non-empty string for a valid URL."""
    url = "https://www.gazeta.ru/"
    html_content = scrape_url(url)
    assert isinstance(html_content, str)
    assert len(html_content) > 0
