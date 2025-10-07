"""Unit tests for OpenRouterService and NewsItem.

Tests the LLM integration functionality with mocked API calls.
Coverage: >80% of llm_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from llm_service import OpenRouterService, NewsItem


# ============================================================================
# Test NewsItem Dataclass
# ============================================================================

@pytest.mark.unit
def test_newsitem_creation():
    """Test NewsItem creation with all fields."""
    news_item = NewsItem(
        title="Test Article",
        description="Test description",
        publication_date="2025-10-07"
    )

    assert news_item.title == "Test Article"
    assert news_item.description == "Test description"
    assert news_item.publication_date == "2025-10-07"


@pytest.mark.unit
def test_newsitem_default_values():
    """Test NewsItem creation with default empty values."""
    news_item = NewsItem(title="Test Article")

    assert news_item.title == "Test Article"
    assert news_item.description == ""
    assert news_item.publication_date == ""


@pytest.mark.unit
def test_newsitem_to_dict():
    """Test NewsItem to_dict conversion."""
    news_item = NewsItem(
        title="Test Article",
        description="Test description",
        publication_date="2025-10-07"
    )

    result = news_item.to_dict()

    assert isinstance(result, dict)
    assert result["title"] == "Test Article"
    assert result["description"] == "Test description"
    assert result["publication_date"] == "2025-10-07"


# ============================================================================
# Test OpenRouterService Initialization
# ============================================================================

@pytest.mark.unit
def test_openrouter_service_initialization(mock_api_key):
    """Test OpenRouterService initializes with default parameters."""
    service = OpenRouterService(api_key=mock_api_key)

    assert service.api_key == mock_api_key
    assert service.model == "qwen/qwen3-coder:free"  # Default free model
    assert service.api_url == "https://openrouter.ai/api/v1/chat/completions"
    assert service.max_retries == 3
    assert service.timeout == 120


@pytest.mark.unit
def test_openrouter_service_custom_initialization(mock_api_key):
    """Test OpenRouterService initializes with custom parameters."""
    service = OpenRouterService(
        api_key=mock_api_key,
        model="anthropic/claude-3-opus",
        max_retries=5,
        timeout=60
    )

    assert service.api_key == mock_api_key
    assert service.model == "anthropic/claude-3-opus"
    assert service.max_retries == 5
    assert service.timeout == 60


# ============================================================================
# Test HTML Content Validation
# ============================================================================

@pytest.mark.unit
def test_extract_news_empty_html(mock_api_key):
    """Test extract_news raises ValueError for empty HTML."""
    service = OpenRouterService(api_key=mock_api_key)

    with pytest.raises(ValueError, match="HTML content is empty"):
        service.extract_news("", "https://example.com")


@pytest.mark.unit
def test_extract_news_whitespace_only_html(mock_api_key):
    """Test extract_news raises ValueError for whitespace-only HTML."""
    service = OpenRouterService(api_key=mock_api_key)

    with pytest.raises(ValueError, match="HTML content is empty"):
        service.extract_news("   \n  \t  ", "https://example.com")


# ============================================================================
# Test Successful News Extraction
# ============================================================================

@pytest.mark.unit
def test_extract_news_success(mock_api_key, sample_html_content, mock_requests_post_success):
    """Test successful news extraction from HTML."""
    service = OpenRouterService(api_key=mock_api_key)

    news_items = service.extract_news(sample_html_content, "https://example.com")

    assert len(news_items) == 2
    assert all(isinstance(item, NewsItem) for item in news_items)
    assert news_items[0].title == "Test News Article 1"
    assert news_items[1].title == "Test News Article 2"


@pytest.mark.unit
def test_extract_news_calls_api_correctly(mock_api_key, sample_html_content, mock_requests_post_success):
    """Test extract_news calls API with correct parameters."""
    service = OpenRouterService(api_key=mock_api_key)

    service.extract_news(sample_html_content, "https://example.com")

    # Verify API was called
    mock_requests_post_success.assert_called_once()

    # Verify API call parameters
    call_args = mock_requests_post_success.call_args
    assert call_args.args[0] == service.api_url
    assert call_args.kwargs["headers"]["Authorization"] == f"Bearer {mock_api_key}"
    assert call_args.kwargs["timeout"] == service.timeout


# ============================================================================
# Test API Authentication Errors
# ============================================================================

@pytest.mark.unit
def test_extract_news_auth_error_401(mock_api_key, sample_html_content, mock_requests_post_auth_error):
    """Test extract_news handles 401 authentication error."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with pytest.raises(RuntimeError, match="Authentication failed - invalid API key"):
        service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test API Rate Limiting
# ============================================================================

@pytest.mark.unit
def test_extract_news_rate_limit_429(mock_api_key, sample_html_content, mock_requests_post_rate_limit):
    """Test extract_news handles 429 rate limit error."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with pytest.raises(RuntimeError, match="Rate limit exceeded - too many requests"):
        service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test API Server Errors
# ============================================================================

@pytest.mark.unit
def test_extract_news_server_error_500(mock_api_key, sample_html_content, mock_requests_post_server_error):
    """Test extract_news handles 500 server error."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with pytest.raises(RuntimeError, match="Server error: 500"):
        service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test Invalid JSON Responses
# ============================================================================

@pytest.mark.unit
def test_extract_news_invalid_json_response(mock_api_key, sample_html_content):
    """Test extract_news handles invalid JSON in response."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is not valid JSON for news extraction"
                }
            }
        ]
    }

    with patch('requests.post', return_value=mock_response):
        with pytest.raises(RuntimeError, match="Failed to extract news after"):
            service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test Empty Responses
# ============================================================================

@pytest.mark.unit
def test_extract_news_empty_response(mock_api_key, sample_html_content, mock_openrouter_empty_response):
    """Test extract_news handles empty news list response."""
    service = OpenRouterService(api_key=mock_api_key)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_openrouter_empty_response

    with patch('requests.post', return_value=mock_response):
        news_items = service.extract_news(sample_html_content, "https://example.com")

        assert len(news_items) == 0
        assert isinstance(news_items, list)


# ============================================================================
# Test Retry Logic
# ============================================================================

@pytest.mark.unit
def test_extract_news_retry_on_failure(mock_api_key, sample_html_content):
    """Test extract_news retries on failure."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=3)

    attempt_count = [0]

    def post_side_effect(*args, **kwargs):
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            # First attempt fails
            raise requests.exceptions.ConnectionError("Connection failed")
        else:
            # Second attempt succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '[{"title": "Test", "description": "", "publication_date": ""}]'
                        }
                    }
                ]
            }
            return mock_response

    with patch('requests.post', side_effect=post_side_effect):
        with patch('time.sleep'):  # Skip actual sleep delays
            news_items = service.extract_news(sample_html_content, "https://example.com")

            assert len(news_items) == 1
            assert attempt_count[0] == 2  # Failed once, succeeded on second


@pytest.mark.unit
def test_extract_news_max_retries_exceeded(mock_api_key, sample_html_content):
    """Test extract_news fails after max retries exceeded."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection failed")):
        with patch('time.sleep'):  # Skip actual sleep delays
            with pytest.raises(RuntimeError, match="Failed to extract news after .* attempts"):
                service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test HTML Cleaning
# ============================================================================

@pytest.mark.unit
def test_clean_html_removes_scripts(mock_api_key):
    """Test _clean_html removes script tags."""
    service = OpenRouterService(api_key=mock_api_key)

    html = """
    <html>
        <head><script>alert('test');</script></head>
        <body>
            <h1>Content</h1>
            <script>console.log('test');</script>
        </body>
    </html>
    """

    cleaned = service._clean_html(html)

    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "Content" in cleaned


@pytest.mark.unit
def test_clean_html_removes_styles(mock_api_key):
    """Test _clean_html removes style tags."""
    service = OpenRouterService(api_key=mock_api_key)

    html = """
    <html>
        <head><style>.test { color: red; }</style></head>
        <body><h1>Content</h1></body>
    </html>
    """

    cleaned = service._clean_html(html)

    assert "<style>" not in cleaned
    assert "color: red" not in cleaned
    assert "Content" in cleaned


@pytest.mark.unit
def test_clean_html_truncates_long_content(mock_api_key):
    """Test _clean_html truncates very long content."""
    service = OpenRouterService(api_key=mock_api_key)

    # Create HTML with 100000 characters (exceeds 80000 limit)
    long_content = "A" * 100000
    html = f"<html><body>{long_content}</body></html>"

    cleaned = service._clean_html(html)

    # Should be truncated to around 80000 chars
    assert len(cleaned) <= 80150  # 80000 + truncation message
    assert "truncated" in cleaned.lower()


# ============================================================================
# Test Response Validation
# ============================================================================

@pytest.mark.unit
def test_validate_response_valid(mock_api_key, mock_openrouter_success_response):
    """Test _validate_response accepts valid response."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response(mock_openrouter_success_response)

    assert result is True


@pytest.mark.unit
def test_validate_response_not_dict(mock_api_key):
    """Test _validate_response rejects non-dict response."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response("not a dict")

    assert result is False


@pytest.mark.unit
def test_validate_response_missing_choices(mock_api_key):
    """Test _validate_response rejects response without choices."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response({"id": "123"})

    assert result is False


@pytest.mark.unit
def test_validate_response_empty_choices(mock_api_key):
    """Test _validate_response rejects response with empty choices."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response({"choices": []})

    assert result is False


@pytest.mark.unit
def test_validate_response_missing_message(mock_api_key):
    """Test _validate_response rejects response without message."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response({"choices": [{}]})

    assert result is False


@pytest.mark.unit
def test_validate_response_missing_content(mock_api_key):
    """Test _validate_response rejects response without content."""
    service = OpenRouterService(api_key=mock_api_key)

    result = service._validate_response({"choices": [{"message": {}}]})

    assert result is False


# ============================================================================
# Test LLM Response Parsing
# ============================================================================

@pytest.mark.unit
def test_parse_llm_response_success(mock_api_key, mock_openrouter_success_response):
    """Test _parse_llm_response successfully parses response."""
    service = OpenRouterService(api_key=mock_api_key)

    news_items = service._parse_llm_response(mock_openrouter_success_response)

    assert len(news_items) == 2
    assert news_items[0].title == "Test News Article 1"
    assert news_items[1].title == "Test News Article 2"


@pytest.mark.unit
def test_parse_llm_response_with_markdown_code_blocks(mock_api_key):
    """Test _parse_llm_response handles markdown code blocks."""
    service = OpenRouterService(api_key=mock_api_key)

    response = {
        "choices": [
            {
                "message": {
                    "content": """```json
[
    {
        "title": "Test Article",
        "description": "Description",
        "publication_date": "2025-10-07"
    }
]
```"""
                }
            }
        ]
    }

    news_items = service._parse_llm_response(response)

    assert len(news_items) == 1
    assert news_items[0].title == "Test Article"


@pytest.mark.unit
def test_parse_llm_response_skips_items_without_title(mock_api_key):
    """Test _parse_llm_response skips items without title."""
    service = OpenRouterService(api_key=mock_api_key)

    response = {
        "choices": [
            {
                "message": {
                    "content": """[
                        {"title": "Valid Article", "description": "", "publication_date": ""},
                        {"description": "No title", "publication_date": ""},
                        {"title": "", "description": "Empty title", "publication_date": ""}
                    ]"""
                }
            }
        ]
    }

    news_items = service._parse_llm_response(response)

    assert len(news_items) == 1
    assert news_items[0].title == "Valid Article"


@pytest.mark.unit
def test_parse_llm_response_handles_non_list_with_news_key(mock_api_key):
    """Test _parse_llm_response handles dict response with 'news' key."""
    service = OpenRouterService(api_key=mock_api_key)

    response = {
        "choices": [
            {
                "message": {
                    "content": """{"news": [{"title": "Test Article", "description": "", "publication_date": ""}]}"""
                }
            }
        ]
    }

    news_items = service._parse_llm_response(response)

    assert len(news_items) == 1
    assert news_items[0].title == "Test Article"


@pytest.mark.unit
def test_parse_llm_response_handles_non_list_with_articles_key(mock_api_key):
    """Test _parse_llm_response handles dict response with 'articles' key."""
    service = OpenRouterService(api_key=mock_api_key)

    response = {
        "choices": [
            {
                "message": {
                    "content": """{"articles": [{"title": "Test Article", "description": "", "publication_date": ""}]}"""
                }
            }
        ]
    }

    news_items = service._parse_llm_response(response)

    assert len(news_items) == 1
    assert news_items[0].title == "Test Article"


# ============================================================================
# Test API Request Errors
# ============================================================================

@pytest.mark.unit
def test_extract_news_timeout_error(mock_api_key, sample_html_content):
    """Test extract_news handles request timeout."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with patch('requests.post', side_effect=requests.exceptions.Timeout("Timeout")):
        with patch('time.sleep'):
            with pytest.raises(RuntimeError, match="API request timed out"):
                service.extract_news(sample_html_content, "https://example.com")


@pytest.mark.unit
def test_extract_news_connection_error(mock_api_key, sample_html_content):
    """Test extract_news handles connection error."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection failed")):
        with patch('time.sleep'):
            with pytest.raises(RuntimeError, match="Failed to connect to OpenRouter API"):
                service.extract_news(sample_html_content, "https://example.com")


@pytest.mark.unit
def test_extract_news_invalid_api_response_json(mock_api_key, sample_html_content):
    """Test extract_news handles invalid JSON in API response."""
    service = OpenRouterService(api_key=mock_api_key, max_retries=2)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

    with patch('requests.post', return_value=mock_response):
        with patch('time.sleep'):
            with pytest.raises(RuntimeError, match="Failed to parse API response as JSON"):
                service.extract_news(sample_html_content, "https://example.com")


# ============================================================================
# Test Prompt Building
# ============================================================================

@pytest.mark.unit
def test_build_extraction_prompt(mock_api_key):
    """Test _build_extraction_prompt generates valid prompt."""
    service = OpenRouterService(api_key=mock_api_key)

    cleaned_html = "Test content"
    url = "https://example.com"

    prompt = service._build_extraction_prompt(cleaned_html, url)

    assert isinstance(prompt, str)
    prompt_data = json.loads(prompt)
    assert "system" in prompt_data
    assert "user" in prompt_data
    assert url in prompt_data["user"]
    assert cleaned_html in prompt_data["user"]
