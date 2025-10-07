
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_url(url: str) -> str:
    """
    Scrapes a given URL and returns the sanitized text content.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('load')
        html_content = page.content()
        browser.close()

        soup = BeautifulSoup(html_content, 'lxml')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True)
