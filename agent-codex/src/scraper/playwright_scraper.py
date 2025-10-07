import asyncio
import logging
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


@dataclass
class ScrapeResult:
    url: str
    html: str


class PlaywrightScraper:
    def __init__(self, headless: bool = True, timeout_ms: int = 30000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.logger = logging.getLogger(__name__)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def scrape(self, url: str) -> ScrapeResult:
        self.logger.info("Scraping start: %s (headless=%s)", url, self.headless)
        html = asyncio.run(self._scrape_async(url))
        self.logger.info("Scraping done: %s, html_len=%s", url, len(html))
        return ScrapeResult(url=url, html=html)

    async def _scrape_async(self, url: str) -> str:
        from playwright.async_api import async_playwright  # lazy import

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                locale="ru-RU",
                viewport={"width": 1366, "height": 850},
            )

            # Patch navigator.webdriver to reduce detection
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = await context.new_page()

            page.set_default_navigation_timeout(self.timeout_ms)
            page.set_default_timeout(self.timeout_ms)

            headers = {
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }
            await page.set_extra_http_headers(headers)

            # Navigate and wait for network idle
            await page.goto(url, wait_until="domcontentloaded")
            await self._progressive_scroll(page)

            # Attempt to wait for main content area
            try:
                await page.wait_for_load_state("networkidle")
            except Exception:
                pass

            html = await page.content()
            await context.close()
            await browser.close()
            return html

    async def _progressive_scroll(
        self, page, step: int = 1200, pause_ms: int = 250
    ) -> None:
        height = await page.evaluate("() => document.body.scrollHeight")
        cur = 0
        sc = 0
        while cur < height:
            await page.evaluate(f"window.scrollTo(0, {cur});")
            await page.wait_for_timeout(pause_ms)
            cur += step
            sc += 1
            new_height = await page.evaluate("() => document.body.scrollHeight")
            if new_height > height:
                height = new_height
        logging.getLogger(__name__).debug(
            "Scrolled %s steps, final_height=%s", sc, height
        )
