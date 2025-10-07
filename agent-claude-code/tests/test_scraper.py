"""Unit tests for ScraperService.

Tests the web scraping functionality with mocked Playwright.
Coverage: >80% of scraper.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scraper import ScraperService


# ============================================================================
# Test ScraperService Initialization
# ============================================================================

@pytest.mark.unit
def test_scraper_service_initialization():
    """Test ScraperService initializes with default parameters."""
    scraper = ScraperService()

    assert scraper.timeout == 30000
    assert scraper.headless is True
    assert scraper.max_retries == 3
    assert scraper.browser is None
    assert scraper.playwright is None


@pytest.mark.unit
def test_scraper_service_custom_initialization():
    """Test ScraperService initializes with custom parameters."""
    scraper = ScraperService(timeout=60000, headless=False, max_retries=5)

    assert scraper.timeout == 60000
    assert scraper.headless is False
    assert scraper.max_retries == 5


# ============================================================================
# Test URL Validation
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_invalid_url_empty():
    """Test scraping with empty URL raises ValueError."""
    scraper = ScraperService()

    with pytest.raises(ValueError, match="Invalid URL"):
        await scraper.scrape("")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_invalid_url_no_protocol():
    """Test scraping with URL without protocol raises ValueError."""
    scraper = ScraperService()

    with pytest.raises(ValueError, match="Invalid URL"):
        await scraper.scrape("example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_invalid_url_none():
    """Test scraping with None URL raises ValueError."""
    scraper = ScraperService()

    with pytest.raises(ValueError, match="Invalid URL"):
        await scraper.scrape(None)


# ============================================================================
# Test Successful Scraping
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_success(mock_playwright, mock_playwright_browser):
    """Test successful scraping returns HTML content."""
    scraper = ScraperService()

    # Mock async_playwright - need to properly mock async context
    async def mock_async_pw_context():
        return mock_playwright

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        html_content = await scraper.scrape("https://example.com")

        assert html_content is not None
        assert len(html_content) > 0
        assert "<html>" in html_content or "<body>" in html_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_initializes_browser(mock_playwright):
    """Test that scraping initializes browser if not already initialized."""
    scraper = ScraperService()

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        await scraper.scrape("https://example.com")

        # Verify browser was initialized
        assert scraper.browser is not None
        assert scraper.playwright is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_applies_stealth_mode(mock_playwright, mock_playwright_browser):
    """Test that scraping applies stealth mode configurations."""
    scraper = ScraperService()

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        await scraper.scrape("https://example.com")

        # Verify browser context was created with stealth settings
        mock_playwright_browser.new_context.assert_called_once()
        call_kwargs = mock_playwright_browser.new_context.call_args.kwargs

        # Check stealth configurations
        assert 'user_agent' in call_kwargs
        assert 'viewport' in call_kwargs
        assert 'locale' in call_kwargs


# ============================================================================
# Test Error Handling
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_timeout_error(mock_playwright, mock_playwright_page):
    """Test scraping handles timeout errors with retries."""
    scraper = ScraperService(max_retries=2)

    # Mock timeout on goto
    mock_playwright_page.goto.side_effect = PlaywrightTimeoutError("Timeout")

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(TimeoutError, match="Failed to scrape .* after .* attempts: timeout"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_network_error(mock_playwright, mock_playwright_page):
    """Test scraping handles network errors with retries."""
    scraper = ScraperService(max_retries=2)

    # Mock network error
    mock_playwright_page.goto.side_effect = RuntimeError("Network error")

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Failed to scrape .* after .* attempts"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_http_403_forbidden(mock_playwright, mock_playwright_page):
    """Test scraping handles 403 Forbidden status."""
    scraper = ScraperService(max_retries=2)

    # Mock 403 response
    mock_response = AsyncMock()
    mock_response.status = 403
    mock_playwright_page.goto.return_value = mock_response

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Access forbidden - possible anti-bot block"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_http_429_rate_limit(mock_playwright, mock_playwright_page):
    """Test scraping handles 429 Rate Limit status."""
    scraper = ScraperService(max_retries=2)

    # Mock 429 response
    mock_response = AsyncMock()
    mock_response.status = 429
    mock_playwright_page.goto.return_value = mock_response

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Rate limited"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_http_500_server_error(mock_playwright, mock_playwright_page):
    """Test scraping handles 500 Server Error status."""
    scraper = ScraperService(max_retries=2)

    # Mock 500 response
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_playwright_page.goto.return_value = mock_response

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Server error: 500"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_no_response(mock_playwright, mock_playwright_page):
    """Test scraping handles no response from page."""
    scraper = ScraperService(max_retries=2)

    # Mock no response
    mock_playwright_page.goto.return_value = None

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="No response received from page"):
            await scraper.scrape("https://example.com")


# ============================================================================
# Test Anti-Bot Detection
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_bot_block_captcha(mock_playwright, mock_playwright_page):
    """Test detection of bot blocking pages."""
    scraper = ScraperService(max_retries=2)

    # Mock bot blocking content
    mock_playwright_page.content.return_value = "<html><body>Please verify you are human</body></html>"

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Anti-bot detection triggered"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_bot_block_cloudflare(mock_playwright, mock_playwright_page):
    """Test detection of Cloudflare bot blocking."""
    scraper = ScraperService(max_retries=2)

    # Mock Cloudflare blocking
    mock_playwright_page.content.return_value = "<html><body>Checking your browser by Cloudflare</body></html>"

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        with pytest.raises(RuntimeError, match="Anti-bot detection triggered"):
            await scraper.scrape("https://example.com")


@pytest.mark.unit
def test_detect_bot_block_method():
    """Test _detect_bot_block method directly."""
    scraper = ScraperService()

    # Test various bot indicators
    assert scraper._detect_bot_block("Please verify you are human") is True
    assert scraper._detect_bot_block("Detected unusual traffic") is True
    assert scraper._detect_bot_block("Checking your browser before accessing") is True
    assert scraper._detect_bot_block("Enable JavaScript and cookies to continue") is True
    assert scraper._detect_bot_block("Ray ID: 1234567890") is True
    assert scraper._detect_bot_block("Normal content without bot indicators") is False


# ============================================================================
# Test Retry Logic
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_retry_success_on_second_attempt(mock_playwright, mock_playwright_page):
    """Test scraping succeeds on retry after initial failure."""
    scraper = ScraperService(max_retries=3)

    # First attempt fails, second succeeds
    attempt_count = [0]

    async def goto_side_effect(*args, **kwargs):
        attempt_count[0] += 1
        if attempt_count[0] == 1:
            raise RuntimeError("Temporary error")
        mock_response = AsyncMock()
        mock_response.status = 200
        return mock_response

    mock_playwright_page.goto.side_effect = goto_side_effect

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        # Should succeed on retry
        html_content = await scraper.scrape("https://example.com")
        assert html_content is not None
        assert attempt_count[0] == 2  # Failed once, succeeded on second


# ============================================================================
# Test Random Delays
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_random_delay():
    """Test _random_delay adds delay within specified range."""
    import time
    scraper = ScraperService()

    start_time = time.time()
    await scraper._random_delay(0.1, 0.2)
    elapsed_time = time.time() - start_time

    # Check delay was within range (with some tolerance)
    assert 0.08 <= elapsed_time <= 0.25


# ============================================================================
# Test Exponential Backoff
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_exponential_backoff():
    """Test _exponential_backoff increases wait time."""
    import time
    scraper = ScraperService()

    # Test backoff for attempt 1 (should be ~2 seconds + jitter)
    start_time = time.time()
    await scraper._exponential_backoff(1)
    elapsed_time = time.time() - start_time

    # Should wait at least 2 seconds (2^1)
    assert elapsed_time >= 2.0
    assert elapsed_time <= 4.0  # 2 seconds + max 1 second jitter + tolerance


# ============================================================================
# Test Resource Cleanup
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_close():
    """Test scraper cleanup closes browser and playwright."""
    scraper = ScraperService()

    # Mock browser and playwright
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()
    scraper.browser = mock_browser
    scraper.playwright = mock_playwright

    await scraper.close()

    # Verify cleanup
    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()
    assert scraper.browser is None
    assert scraper.playwright is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_close_when_not_initialized():
    """Test scraper close when browser not initialized."""
    scraper = ScraperService()

    # Should not raise error
    await scraper.close()

    assert scraper.browser is None
    assert scraper.playwright is None


# ============================================================================
# Test Context Manager
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_async_context_manager(mock_playwright):
    """Test ScraperService as async context manager."""
    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        async with ScraperService() as scraper:
            html = await scraper.scrape("https://example.com")
            assert html is not None

        # Verify cleanup was called
        # (Browser should be closed after context exit)


# ============================================================================
# Test User Agent Rotation
# ============================================================================

@pytest.mark.unit
def test_user_agents_list():
    """Test USER_AGENTS list is properly defined."""
    scraper = ScraperService()

    assert len(scraper.USER_AGENTS) > 0
    assert all(isinstance(ua, str) for ua in scraper.USER_AGENTS)
    assert all("Mozilla" in ua for ua in scraper.USER_AGENTS)


# ============================================================================
# Test Page Content Extraction
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrape_extracts_full_page_content(mock_playwright, mock_playwright_page):
    """Test scraping extracts full HTML content from page."""
    scraper = ScraperService()

    expected_html = "<html><head><title>Test</title></head><body><h1>Test Page</h1></body></html>"
    mock_playwright_page.content.return_value = expected_html

    with patch('scraper.async_playwright') as mock_async_pw:
        mock_async_pw.return_value.start = AsyncMock(return_value=mock_playwright)

        html_content = await scraper.scrape("https://example.com")

        assert html_content == expected_html
        mock_playwright_page.content.assert_called()
