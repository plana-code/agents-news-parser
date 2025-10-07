"""Unit tests for API key validation in OpenRouterService.

Tests the new validation logic added in Phase 9 - Bug Fixes.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from llm_service import OpenRouterService


@pytest.mark.unit
def test_api_key_validation_empty_key():
    """Test that empty API key raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="")

    assert "required but not provided" in str(exc_info.value)


@pytest.mark.unit
def test_api_key_validation_none_key():
    """Test that None API key raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key=None)

    assert "required but not provided" in str(exc_info.value)


@pytest.mark.unit
def test_api_key_validation_invalid_prefix():
    """Test that API key with wrong prefix raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="invalid-key-format-12345678901234567890")

    assert "Invalid OPENROUTER_API_KEY format" in str(exc_info.value)
    assert "sk-or-v1-" in str(exc_info.value)


@pytest.mark.unit
def test_api_key_validation_too_short():
    """Test that API key shorter than 50 chars raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="sk-or-v1-short")

    assert "incomplete or invalid" in str(exc_info.value)
    assert "60+ characters" in str(exc_info.value)


@pytest.mark.unit
def test_api_key_validation_valid_key():
    """Test that valid API key passes validation."""
    # This should not raise any exception
    valid_key = "sk-or-v1-" + "x" * 60
    service = OpenRouterService(api_key=valid_key)

    assert service.api_key == valid_key
    assert service.model == "qwen/qwen3-coder:free"  # Default free model


@pytest.mark.unit
def test_api_key_validation_exact_50_chars():
    """Test that API key with exactly 50 chars passes validation."""
    # Edge case: exactly 50 characters total
    valid_key = "sk-or-v1-" + "a" * 41  # 9 + 41 = 50 chars
    service = OpenRouterService(api_key=valid_key)

    assert service.api_key == valid_key


@pytest.mark.unit
def test_api_key_validation_error_message_helpful():
    """Test that error messages provide helpful guidance."""
    # Test empty key
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="")
    assert "https://openrouter.ai/" not in str(exc_info.value)

    # Test wrong format
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="wrong-format-12345678901234567890")
    assert "https://openrouter.ai/" in str(exc_info.value)
    assert "Expected format: sk-or-v1-" in str(exc_info.value)

    # Test too short
    with pytest.raises(ValueError) as exc_info:
        OpenRouterService(api_key="sk-or-v1-short")
    assert "https://openrouter.ai/" in str(exc_info.value)
    assert "check your key" in str(exc_info.value)


@pytest.mark.unit
def test_api_key_validation_realistic_key():
    """Test with realistic OpenRouter API key format."""
    # Realistic format based on OpenRouter's actual key format
    realistic_key = "sk-or-v1-abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234"
    service = OpenRouterService(api_key=realistic_key)

    assert service.api_key == realistic_key
    assert len(service.api_key) >= 50
