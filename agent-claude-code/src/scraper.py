"""Web Scraper Module

This module handles web scraping with JavaScript rendering and anti-bot bypass features.
Uses Playwright for robust scraping with stealth mode.
"""

from typing import Optional
import logging
import asyncio
import random
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for scraping web content with anti-bot capabilities.

    Features:
    - JavaScript rendering using Playwright
    - Stealth mode to bypass anti-bot detection
    - User-agent rotation
    - Random delays
    - Cookie handling
    - Retry logic with exponential backoff
    """

    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    def __init__(self, timeout: int = 30000, headless: bool = True, max_retries: int = 3):
        """Initialize the scraper service.

        Args:
            timeout: Page load timeout in milliseconds
            headless: Whether to run browser in headless mode
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.headless = headless
        self.max_retries = max_retries
        self.browser: Optional[Browser] = None
        self.playwright = None
        logger.info(f"ScraperService initialized (timeout={timeout}ms, headless={headless}, retries={max_retries})")

    async def _init_browser(self):
        """Initialize Playwright browser instance."""
        if self.browser is None:
            logger.info("Initializing Playwright browser (headless=%s)...", self.headless)
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                    # Removed '--disable-web-security' for security compliance
                ]
            )
            logger.info("Browser initialized successfully")

    async def _setup_stealth_page(self) -> Page:
        """Create a new page with stealth configurations.

        Returns:
            Configured page instance
        """
        logger.info("Setting up stealth page with anti-bot protection...")
        # Create new context with random user agent
        user_agent = random.choice(self.USER_AGENTS)
        logger.debug("Selected user agent: %s", user_agent[:80])

        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            # Add some common browser features
            java_script_enabled=True,
            accept_downloads=False,
            has_touch=False,
            is_mobile=False,
        )

        # Add extra headers to appear more like a real browser
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
        })
        logger.debug("Browser headers configured")

        page = await context.new_page()

        # Hide webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override the plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Override the chrome property
            window.chrome = {
                runtime: {}
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        logger.info("Stealth page created successfully")
        return page

    async def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add a random delay to mimic human behavior.

        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"Random delay: {delay:.2f}s")
        await asyncio.sleep(delay)

    async def scrape(self, url: str) -> str:
        """Scrape content from a URL with retry logic.

        Args:
            url: The URL to scrape

        Returns:
            The HTML content as a string

        Raises:
            ValueError: If the URL is invalid
            TimeoutError: If page load exceeds timeout after all retries
            RuntimeError: If scraping fails after all retries
        """
        if not url or not url.startswith(('http://', 'https://')):
            logger.error("Invalid URL provided: %s", url)
            raise ValueError(f"Invalid URL: {url}")

        logger.info("Starting scrape for URL: %s (max_retries=%d)", url, self.max_retries)

        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._scrape_attempt(url, attempt)
                logger.info("Scrape completed successfully for %s on attempt %d", url, attempt)
                return result
            except PlaywrightTimeoutError as e:
                logger.warning("Attempt %d/%d timed out for %s: %s", attempt, self.max_retries, url, str(e))
                if attempt == self.max_retries:
                    logger.error("All %d attempts failed for %s: timeout", self.max_retries, url)
                    raise TimeoutError(f"Failed to scrape {url} after {self.max_retries} attempts: timeout")
                await self._exponential_backoff(attempt)
            except Exception as e:
                logger.warning("Attempt %d/%d failed for %s: %s", attempt, self.max_retries, url, str(e))
                if attempt == self.max_retries:
                    logger.error("All %d attempts failed for %s: %s", self.max_retries, url, str(e))
                    raise RuntimeError(f"Failed to scrape {url} after {self.max_retries} attempts: {str(e)}")
                await self._exponential_backoff(attempt)

    async def _scrape_attempt(self, url: str, attempt: int) -> str:
        """Single scraping attempt.

        Args:
            url: The URL to scrape
            attempt: Current attempt number

        Returns:
            The HTML content as a string
        """
        logger.info("Scrape attempt %d/%d for %s", attempt, self.max_retries, url)

        # Initialize browser if needed
        await self._init_browser()

        # Create stealth page
        page = await self._setup_stealth_page()

        try:
            # Add random delay before navigation
            logger.debug("Adding random delay before navigation...")
            await self._random_delay(0.5, 1.5)

            # Navigate to URL - wait for network to be idle for better content loading
            logger.info("Navigating to %s (timeout=%dms)...", url, self.timeout)
            try:
                # Try networkidle first for full page load
                response = await page.goto(url, timeout=self.timeout, wait_until='networkidle')
                logger.debug("Page loaded with networkidle")
            except Exception:
                # Fallback to domcontentloaded if networkidle times out
                logger.debug("Networkidle timed out, falling back to domcontentloaded")
                response = await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')

            if response is None:
                raise RuntimeError("No response received from page")

            # Check response status
            status = response.status
            logger.info("Received response: status=%d, url=%s", status, url)

            if status >= 400:
                logger.warning("HTTP error status: %d", status)
                if status == 403:
                    raise RuntimeError("Access forbidden - possible anti-bot block")
                elif status == 429:
                    raise RuntimeError("Rate limited")
                elif status >= 500:
                    raise RuntimeError(f"Server error: {status}")

            # Check for anti-bot indicators
            logger.debug("Checking for anti-bot indicators...")
            content = await page.content()
            if self._detect_bot_block(content):
                logger.warning("Detected potential bot blocking - retrying")
                raise RuntimeError("Anti-bot detection triggered")
            logger.debug("No anti-bot indicators detected")

            # Wait for dynamic content to load (longer delay for news sites with lazy loading)
            logger.debug("Waiting for dynamic content to fully load (images, scripts, etc)...")
            await self._random_delay(3.0, 5.0)

            # Scroll down to trigger lazy-loaded content
            logger.debug("Scrolling page to trigger lazy-loaded content...")
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Scroll failed (may not be needed): {e}")

            # Get final HTML content
            logger.debug("Extracting final HTML content...")
            html_content = await page.content()

            logger.info("Successfully scraped %s (content_length=%d chars, status=%d)", url, len(html_content), status)
            return html_content

        finally:
            # Clean up page and context
            logger.debug("Cleaning up page and context...")
            await page.context.close()

    def _detect_bot_block(self, html_content: str) -> bool:
        """Detect if page contains anti-bot blocking indicators.

        Args:
            html_content: HTML content to check

        Returns:
            True if bot blocking detected
        """
        # Common anti-bot indicators - more specific patterns
        bot_indicators = [
            'checking your browser',
            'enable javascript and cookies',
            'ddos protection',
            'ray id',  # Cloudflare specific
            'cf-browser-verification',  # Cloudflare
            'please verify you are human',
            'detected unusual traffic',
            'automated requests from your',
            'unusual activity from your computer'
        ]

        html_lower = html_content.lower()
        for indicator in bot_indicators:
            if indicator in html_lower:
                logger.warning("Detected bot indicator in HTML: '%s'", indicator)
                return True

        # Check for very short content (likely a block page)
        if len(html_content) < 500 and ('access denied' in html_lower or 'forbidden' in html_lower):
            logger.warning("Detected short content with access denial keywords (length=%d)", len(html_content))
            return True

        return False

    async def _exponential_backoff(self, attempt: int):
        """Wait with exponential backoff before retry.

        Args:
            attempt: Current attempt number
        """
        wait_time = min(2 ** attempt, 30)  # Max 30 seconds
        jitter = random.uniform(0, 1)  # Add jitter
        total_wait = wait_time + jitter
        logger.info(f"Backing off for {total_wait:.2f} seconds before retry...")
        await asyncio.sleep(total_wait)

    async def close(self):
        """Clean up resources and close browser instance."""
        if self.browser:
            logger.debug("Closing browser...")
            await self.browser.close()
            self.browser = None

        if self.playwright:
            logger.debug("Stopping Playwright...")
            await self.playwright.stop()
            self.playwright = None

        logger.info("ScraperService closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
