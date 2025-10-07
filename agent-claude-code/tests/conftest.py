"""Shared pytest fixtures for unit tests.

This module provides reusable fixtures for testing all components
with proper mocking and isolation.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from llm_service import NewsItem


# ============================================================================
# Playwright Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_playwright_page():
    """Mock Playwright page object."""
    page = AsyncMock()
    page.goto = AsyncMock(return_value=AsyncMock(status=200))
    page.content = AsyncMock(return_value="<html><body><h1>Test Page</h1></body></html>")
    page.add_init_script = AsyncMock()

    # Mock context
    context = AsyncMock()
    context.close = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    context.set_extra_http_headers = AsyncMock()
    page.context = context

    return page


@pytest.fixture
def mock_playwright_browser(mock_playwright_page):
    """Mock Playwright browser object."""
    browser = AsyncMock()

    # Mock context creation
    context = mock_playwright_page.context
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()

    return browser


@pytest.fixture
def mock_playwright(mock_playwright_browser):
    """Mock Playwright instance."""
    playwright = AsyncMock()
    playwright.chromium.launch = AsyncMock(return_value=mock_playwright_browser)
    playwright.stop = AsyncMock()
    return playwright


# ============================================================================
# OpenRouter API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_openrouter_success_response():
    """Mock successful OpenRouter API response."""
    return {
        "id": "gen-123",
        "model": "anthropic/claude-3.5-sonnet",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": """[
                        {
                            "title": "Test News Article 1",
                            "description": "This is a test news article description",
                            "publication_date": "2025-10-07"
                        },
                        {
                            "title": "Test News Article 2",
                            "description": "Another test article",
                            "publication_date": "2025-10-06"
                        }
                    ]"""
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_openrouter_empty_response():
    """Mock OpenRouter API response with no news items."""
    return {
        "id": "gen-456",
        "model": "anthropic/claude-3.5-sonnet",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "[]"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 10,
            "total_tokens": 110
        }
    }


@pytest.fixture
def mock_openrouter_invalid_json_response():
    """Mock OpenRouter API response with invalid JSON."""
    return {
        "id": "gen-789",
        "model": "anthropic/claude-3.5-sonnet",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is not valid JSON content"
                },
                "finish_reason": "stop"
            }
        ]
    }


@pytest.fixture
def mock_requests_post_success(mock_openrouter_success_response):
    """Mock successful requests.post for OpenRouter API."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_openrouter_success_response
    mock_response.text = ""

    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_post_auth_error():
    """Mock requests.post with authentication error (401)."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_post_rate_limit():
    """Mock requests.post with rate limit error (429)."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"

    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_post_server_error():
    """Mock requests.post with server error (500)."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"

    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def temp_database():
    """Create temporary in-memory SQLite database."""
    import sqlite3

    # Use in-memory database for tests
    db_path = ":memory:"

    from database import DatabaseService
    db_service = DatabaseService(db_path)
    db_service.initialize()

    yield db_service

    # Cleanup
    db_service.close()


@pytest.fixture
def temp_database_file():
    """Create temporary file-based SQLite database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    from database import DatabaseService
    db_service = DatabaseService(db_path)
    db_service.initialize()

    yield db_service

    # Cleanup
    db_service.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


# ============================================================================
# CSV Exporter Fixtures
# ============================================================================

@pytest.fixture
def temp_export_dir():
    """Create temporary directory for CSV exports."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_news_data():
    """Sample news data for testing."""
    return [
        {
            "title": "Test Article 1",
            "description": "Description for article 1",
            "publication_date": "2025-10-07",
            "url": "https://example.com",
            "created_at": "2025-10-07 12:00:00"
        },
        {
            "title": "Test Article 2",
            "description": "Description for article 2",
            "publication_date": "2025-10-06",
            "url": "https://example.com",
            "created_at": "2025-10-07 11:00:00"
        }
    ]


@pytest.fixture
def sample_news_with_special_chars():
    """Sample news data with special characters (quotes, commas, newlines)."""
    return [
        {
            "title": 'Article with "quotes" and, commas',
            "description": "Line 1\nLine 2\nLine 3",
            "publication_date": "2025-10-07",
            "url": "https://example.com/test?param=value&other=true",
            "created_at": "2025-10-07 12:00:00"
        }
    ]


# ============================================================================
# Sample NewsItem Objects
# ============================================================================

@pytest.fixture
def sample_news_items():
    """Sample NewsItem objects for testing."""
    return [
        NewsItem(
            title="First News Article",
            description="Description of first article",
            publication_date="2025-10-07"
        ),
        NewsItem(
            title="Second News Article",
            description="Description of second article",
            publication_date="2025-10-06"
        ),
        NewsItem(
            title="Third News Article",
            description="",
            publication_date=""
        )
    ]


# ============================================================================
# HTML Content Fixtures
# ============================================================================

@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing."""
    return """
    <html>
    <head><title>Test News Site</title></head>
    <body>
        <article>
            <h1>Breaking News Article</h1>
            <p>This is the article content.</p>
            <time>2025-10-07</time>
        </article>
        <article>
            <h2>Another News Story</h2>
            <p>More news content here.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def empty_html_content():
    """Empty HTML content for testing."""
    return "<html><body></body></html>"


@pytest.fixture
def html_with_bot_indicators():
    """HTML content with anti-bot indicators."""
    return """
    <html>
    <head><title>Access Denied</title></head>
    <body>
        <h1>Please verify you are human</h1>
        <p>We detected unusual traffic from your network.</p>
        <div class="captcha">Complete the CAPTCHA below</div>
    </body>
    </html>
    """


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_api_key():
    """Mock API key for testing.

    Uses valid OpenRouter format: sk-or-v1-[64 chars]
    This is a test key that passes validation but is not real.
    """
    return "sk-or-v1-test1234567890abcdef1234567890abcdef1234567890abcdef12345"


@pytest.fixture
def test_url():
    """Test URL for scraping."""
    return "https://example.com"


@pytest.fixture
def invalid_url():
    """Invalid URL for testing error handling."""
    return "not-a-valid-url"


# ============================================================================
# Async Helpers
# ============================================================================

@pytest.fixture
def event_loop_policy():
    """Configure event loop policy for async tests."""
    import asyncio
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
