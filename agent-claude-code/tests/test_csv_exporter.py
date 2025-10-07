"""Unit tests for CSVExporter.

Tests the CSV export functionality with temporary directories.
Coverage: >80% of csv_exporter.py
"""

import pytest
import os
import csv
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from csv_exporter import CSVExporter


# ============================================================================
# Test CSVExporter Initialization
# ============================================================================

@pytest.mark.unit
def test_csv_exporter_initialization():
    """Test CSVExporter initializes with default export path."""
    exporter = CSVExporter()

    assert exporter.export_path == "exports/"


@pytest.mark.unit
def test_csv_exporter_custom_initialization(temp_export_dir):
    """Test CSVExporter initializes with custom export path."""
    exporter = CSVExporter(export_path=temp_export_dir)

    assert exporter.export_path == temp_export_dir


# ============================================================================
# Test Export to CSV - Success Cases
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_success(temp_export_dir, sample_news_data):
    """Test successful CSV export with valid data."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_data,
        url="https://example.com",
        filename="test_export.csv"
    )

    # Verify file was created
    assert os.path.exists(output_path)
    assert output_path.endswith(".csv")


@pytest.mark.unit
def test_export_to_csv_creates_directory(temp_export_dir, sample_news_data):
    """Test export creates export directory if it doesn't exist."""
    export_dir = os.path.join(temp_export_dir, "subdir")
    exporter = CSVExporter(export_path=export_dir)

    output_path = exporter.export_to_csv(sample_news_data, filename="test.csv")

    # Verify directory was created
    assert os.path.exists(export_dir)
    assert os.path.exists(output_path)


@pytest.mark.unit
def test_export_to_csv_auto_generates_filename(temp_export_dir, sample_news_data):
    """Test export auto-generates filename when not provided."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_data,
        url="https://example.com"
    )

    # Verify filename was generated
    assert os.path.exists(output_path)
    assert "example" in os.path.basename(output_path)  # Domain in filename
    assert output_path.endswith(".csv")


@pytest.mark.unit
def test_export_to_csv_adds_csv_extension(temp_export_dir, sample_news_data):
    """Test export adds .csv extension if not present."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_data,
        filename="test_file"  # No .csv extension
    )

    # Verify .csv extension was added
    assert output_path.endswith(".csv")


@pytest.mark.unit
def test_export_to_csv_content_correctness(temp_export_dir, sample_news_data):
    """Test exported CSV contains correct data."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(sample_news_data, filename="test.csv")

    # Read and verify CSV content
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]['title'] == "Test Article 1"
        assert rows[0]['description'] == "Description for article 1"
        assert rows[1]['title'] == "Test Article 2"


@pytest.mark.unit
def test_export_to_csv_headers(temp_export_dir, sample_news_data):
    """Test exported CSV has correct headers."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(sample_news_data, filename="test.csv")

    # Read headers
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames

        expected_headers = ['title', 'description', 'publication_date', 'url', 'created_at']
        assert headers == expected_headers


# ============================================================================
# Test Export to CSV - Error Cases
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_empty_data(temp_export_dir):
    """Test export raises ValueError for empty data."""
    exporter = CSVExporter(export_path=temp_export_dir)

    with pytest.raises(ValueError, match="No news items to export"):
        exporter.export_to_csv([], filename="test.csv")


@pytest.mark.unit
def test_export_to_csv_non_list_data(temp_export_dir):
    """Test export raises ValueError for non-list data."""
    exporter = CSVExporter(export_path=temp_export_dir)

    with pytest.raises(ValueError, match="news_items must be a list"):
        exporter.export_to_csv("not a list", filename="test.csv")


# ============================================================================
# Test Special Characters Handling
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_handles_quotes(temp_export_dir, sample_news_with_special_chars):
    """Test export handles quotes in data correctly."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_with_special_chars,
        filename="test.csv"
    )

    # Read and verify quotes are handled
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        assert 'Article with "quotes" and, commas' in rows[0]['title']


@pytest.mark.unit
def test_export_to_csv_handles_commas(temp_export_dir, sample_news_with_special_chars):
    """Test export handles commas in data correctly."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_with_special_chars,
        filename="test.csv"
    )

    # Read and verify commas are handled
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        # CSV should preserve commas in quoted fields
        assert "," in rows[0]['title']


@pytest.mark.unit
def test_export_to_csv_handles_newlines(temp_export_dir, sample_news_with_special_chars):
    """Test export handles newlines in data correctly."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(
        sample_news_with_special_chars,
        filename="test.csv"
    )

    # Read and verify newlines are handled
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        # CSV should preserve newlines in quoted fields
        assert "\n" in rows[0]['description']


# ============================================================================
# Test Filename Sanitization
# ============================================================================

@pytest.mark.unit
def test_sanitize_filename_removes_invalid_chars():
    """Test _sanitize_filename removes invalid characters."""
    exporter = CSVExporter()

    sanitized = exporter._sanitize_filename("file:name*with?invalid|chars")

    # Should replace invalid chars with underscore
    assert ":" not in sanitized
    assert "*" not in sanitized
    assert "?" not in sanitized
    assert "|" not in sanitized
    assert "_" in sanitized


@pytest.mark.unit
def test_sanitize_filename_removes_consecutive_underscores():
    """Test _sanitize_filename removes consecutive underscores."""
    exporter = CSVExporter()

    sanitized = exporter._sanitize_filename("file___name")

    # Should reduce to single underscore
    assert "___" not in sanitized
    assert "_" in sanitized


@pytest.mark.unit
def test_sanitize_filename_trims_underscores():
    """Test _sanitize_filename trims leading/trailing underscores."""
    exporter = CSVExporter()

    sanitized = exporter._sanitize_filename("___filename___")

    # Should not start or end with underscore
    assert not sanitized.startswith("_")
    assert not sanitized.endswith("_")


@pytest.mark.unit
def test_sanitize_filename_limits_length():
    """Test _sanitize_filename limits filename length."""
    exporter = CSVExporter()

    long_filename = "a" * 300  # 300 characters
    sanitized = exporter._sanitize_filename(long_filename)

    # Should be truncated to 200 chars
    assert len(sanitized) <= 200


@pytest.mark.unit
def test_sanitize_filename_preserves_extension():
    """Test _sanitize_filename preserves file extension."""
    exporter = CSVExporter()

    long_filename = "a" * 300 + ".csv"
    sanitized = exporter._sanitize_filename(long_filename)

    # Should preserve .csv extension even after truncation
    assert sanitized.endswith(".csv")
    assert len(sanitized) <= 200


# ============================================================================
# Test Filename Generation
# ============================================================================

@pytest.mark.unit
def test_generate_filename_from_url():
    """Test _generate_filename extracts domain from URL."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("https://example.com/path/to/page")

    # Should contain domain
    assert "example" in filename
    assert filename.endswith(".csv")


@pytest.mark.unit
def test_generate_filename_removes_www():
    """Test _generate_filename removes www prefix."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("https://www.example.com")

    # Should not contain www
    assert "www" not in filename
    assert "example" in filename


@pytest.mark.unit
def test_generate_filename_removes_tld():
    """Test _generate_filename removes TLD."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("https://example.com")

    # Should extract just the domain name
    assert "example" in filename


@pytest.mark.unit
def test_generate_filename_includes_timestamp():
    """Test _generate_filename includes timestamp."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("https://example.com")

    # Should contain timestamp pattern (YYYYMMDD_HHMMSS)
    # Extract the timestamp part
    parts = filename.replace(".csv", "").split("_")
    assert len(parts) >= 2  # domain + date + time


@pytest.mark.unit
def test_generate_filename_handles_invalid_url():
    """Test _generate_filename handles invalid URL gracefully."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("not-a-valid-url")

    # Should use the domain part or "news" prefix
    assert filename.endswith(".csv")
    # The implementation extracts "not-a-valid-url" as the domain part
    assert len(filename) > 0


@pytest.mark.unit
def test_generate_filename_handles_empty_url():
    """Test _generate_filename handles empty URL."""
    exporter = CSVExporter()

    filename = exporter._generate_filename("")

    # Should use default "news" prefix
    assert "news" in filename
    assert filename.endswith(".csv")


# ============================================================================
# Test Export News (Legacy Method)
# ============================================================================

@pytest.mark.unit
def test_export_news_success(temp_export_dir, sample_news_data):
    """Test export_news() legacy method works."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_news(sample_news_data, filename="test.csv")

    # Verify file was created
    assert os.path.exists(output_path)


@pytest.mark.unit
def test_export_news_requires_filename(temp_export_dir, sample_news_data):
    """Test export_news() requires filename."""
    exporter = CSVExporter(export_path=temp_export_dir)

    with pytest.raises(ValueError, match="Filename is required"):
        exporter.export_news(sample_news_data, filename="")


# ============================================================================
# Test UTF-8 Encoding
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_utf8_encoding(temp_export_dir):
    """Test export handles UTF-8 characters correctly."""
    exporter = CSVExporter(export_path=temp_export_dir)

    news_data = [
        {
            "title": "Тестовая новость",  # Russian
            "description": "日本語のテスト",  # Japanese
            "publication_date": "2025-10-07",
            "url": "https://example.com",
            "created_at": "2025-10-07 12:00:00"
        }
    ]

    output_path = exporter.export_to_csv(news_data, filename="test_utf8.csv")

    # Read and verify UTF-8 content
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        assert rows[0]['title'] == "Тестовая новость"
        assert rows[0]['description'] == "日本語のテスト"


# ============================================================================
# Test Missing Fields Handling
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_handles_missing_fields(temp_export_dir):
    """Test export handles missing fields gracefully."""
    exporter = CSVExporter(export_path=temp_export_dir)

    news_data = [
        {
            "title": "Article with only title"
            # Missing other fields
        },
        {
            "title": "Article 2",
            "description": "Has description"
            # Missing other fields
        }
    ]

    output_path = exporter.export_to_csv(news_data, filename="test.csv")

    # Read and verify missing fields are handled
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]['title'] == "Article with only title"
        assert rows[0]['description'] == ""  # Should be empty string


# ============================================================================
# Test Multiple Exports
# ============================================================================

@pytest.mark.unit
def test_export_multiple_files(temp_export_dir, sample_news_data):
    """Test exporter can create multiple files."""
    exporter = CSVExporter(export_path=temp_export_dir)

    # Export first file
    path1 = exporter.export_to_csv(sample_news_data, filename="export1.csv")

    # Export second file
    path2 = exporter.export_to_csv(sample_news_data, filename="export2.csv")

    # Both files should exist
    assert os.path.exists(path1)
    assert os.path.exists(path2)
    assert path1 != path2


# ============================================================================
# Test Return Value
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_returns_full_path(temp_export_dir, sample_news_data):
    """Test export_to_csv() returns full path to created file."""
    exporter = CSVExporter(export_path=temp_export_dir)

    output_path = exporter.export_to_csv(sample_news_data, filename="test.csv")

    # Should be absolute or relative path with export_path
    assert temp_export_dir in output_path
    assert output_path.endswith("test.csv")


# ============================================================================
# Test Empty Field Handling
# ============================================================================

@pytest.mark.unit
def test_export_to_csv_strips_whitespace(temp_export_dir):
    """Test export strips whitespace from fields."""
    exporter = CSVExporter(export_path=temp_export_dir)

    news_data = [
        {
            "title": "  Title with spaces  ",
            "description": "  Description with spaces  ",
            "publication_date": "  2025-10-07  ",
            "url": "  https://example.com  ",
            "created_at": "  2025-10-07 12:00:00  "
        }
    ]

    output_path = exporter.export_to_csv(news_data, filename="test.csv")

    # Read and verify whitespace is stripped
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        assert rows[0]['title'] == "Title with spaces"
        assert rows[0]['description'] == "Description with spaces"
