"""Fixtures for End-to-End tests.

This module provides fixtures for E2E tests that use real services
without mocks.
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


# ============================================================================
# Environment and Configuration
# ============================================================================

@pytest.fixture
def test_api_key():
    """Get API key from environment or return default test key."""
    # Default free API key from instructions.md
    default_key = "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"
    api_key = os.getenv("OPENROUTER_API_KEY", default_key)
    return api_key


@pytest.fixture
def has_valid_api_key(test_api_key):
    """Check if a valid API key is available."""
    return test_api_key and len(test_api_key) > 10


# ============================================================================
# Test Database
# ============================================================================

@pytest.fixture
def test_database_path():
    """Create temporary database file for E2E tests."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


# ============================================================================
# Test Export Directory
# ============================================================================

@pytest.fixture
def test_export_dir():
    """Create temporary export directory for E2E tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


# ============================================================================
# Test URLs
# ============================================================================

@pytest.fixture
def simple_test_url():
    """Simple test URL that should always work."""
    return "https://example.com"


@pytest.fixture
def news_test_url():
    """Real news site URL for testing."""
    return "https://www.bbc.com/news"


# ============================================================================
# Mock News Items for Testing
# ============================================================================

@pytest.fixture
def mock_news_items_for_e2e():
    """Mock news items to use when API is not available."""
    from llm_service import NewsItem
    return [
        NewsItem(
            title="Mock News Article 1",
            description="This is a mock article for testing",
            publication_date="2025-10-07"
        ),
        NewsItem(
            title="Mock News Article 2",
            description="Another mock article",
            publication_date="2025-10-06"
        )
    ]
