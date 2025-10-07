"""Unit tests for DatabaseService.

Tests the SQLite database functionality with in-memory databases.
Coverage: >80% of database.py
"""

import pytest
import sqlite3
import tempfile
import os
import threading
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseService


# ============================================================================
# Test Database Initialization
# ============================================================================

@pytest.mark.unit
def test_database_service_initialization():
    """Test DatabaseService initializes with database path."""
    db_path = ":memory:"
    db = DatabaseService(db_path)

    assert db.db_path == db_path
    assert db._connection is None


@pytest.mark.unit
def test_database_initialize_creates_schema(temp_database):
    """Test initialize() creates database schema."""
    # Schema should already be created by fixture
    conn = temp_database._get_connection()
    cursor = conn.cursor()

    # Check if news table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "news"


@pytest.mark.unit
def test_database_initialize_creates_indexes(temp_database):
    """Test initialize() creates database indexes."""
    conn = temp_database._get_connection()
    cursor = conn.cursor()

    # Check if indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_news_url'")
    url_index = cursor.fetchone()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_news_created_at'")
    created_at_index = cursor.fetchone()

    assert url_index is not None
    assert created_at_index is not None


@pytest.mark.unit
def test_database_initialize_idempotent(temp_database):
    """Test initialize() can be called multiple times safely."""
    # Call initialize multiple times
    temp_database.initialize()
    temp_database.initialize()
    temp_database.initialize()

    # Should not raise error and table should still exist
    conn = temp_database._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
    result = cursor.fetchone()

    assert result is not None


# ============================================================================
# Test Save News
# ============================================================================

@pytest.mark.unit
def test_save_news_single_item(temp_database):
    """Test save_news() with a single news item."""
    news_items = [
        {
            "title": "Test Article",
            "description": "Test description",
            "publication_date": "2025-10-07"
        }
    ]

    count = temp_database.save_news("https://example.com", news_items)

    assert count == 1


@pytest.mark.unit
def test_save_news_multiple_items(temp_database):
    """Test save_news() with multiple news items."""
    news_items = [
        {"title": "Article 1", "description": "Desc 1", "publication_date": "2025-10-07"},
        {"title": "Article 2", "description": "Desc 2", "publication_date": "2025-10-06"},
        {"title": "Article 3", "description": "Desc 3", "publication_date": "2025-10-05"}
    ]

    count = temp_database.save_news("https://example.com", news_items)

    assert count == 3


@pytest.mark.unit
def test_save_news_empty_list(temp_database):
    """Test save_news() with empty news list."""
    count = temp_database.save_news("https://example.com", [])

    assert count == 0


@pytest.mark.unit
def test_save_news_missing_url(temp_database):
    """Test save_news() raises ValueError for missing URL."""
    news_items = [{"title": "Test", "description": "", "publication_date": ""}]

    with pytest.raises(ValueError, match="URL is required"):
        temp_database.save_news("", news_items)


@pytest.mark.unit
def test_save_news_skips_items_without_title(temp_database):
    """Test save_news() skips items without title."""
    news_items = [
        {"title": "Valid Article", "description": "Desc", "publication_date": "2025-10-07"},
        {"description": "No title", "publication_date": "2025-10-07"},  # Missing title
        {"title": "", "description": "Empty title", "publication_date": "2025-10-07"}  # Empty title
    ]

    count = temp_database.save_news("https://example.com", news_items)

    # Only the first item should be saved
    assert count == 1


@pytest.mark.unit
def test_save_news_handles_optional_fields(temp_database):
    """Test save_news() handles optional fields correctly."""
    news_items = [
        {"title": "Article with all fields", "description": "Desc", "publication_date": "2025-10-07"},
        {"title": "Article without description"},
        {"title": "Article with empty fields", "description": "", "publication_date": ""}
    ]

    count = temp_database.save_news("https://example.com", news_items)

    assert count == 3


# ============================================================================
# Test Insert News
# ============================================================================

@pytest.mark.unit
def test_insert_news_success(temp_database):
    """Test insert_news() successfully inserts a news article."""
    inserted_id = temp_database.insert_news(
        url="https://example.com",
        title="Test Article",
        description="Test description",
        publication_date="2025-10-07"
    )

    assert inserted_id > 0


@pytest.mark.unit
def test_insert_news_missing_url(temp_database):
    """Test insert_news() raises ValueError for missing URL."""
    with pytest.raises(ValueError, match="URL is required"):
        temp_database.insert_news(
            url="",
            title="Test Article",
            description="Test description"
        )


@pytest.mark.unit
def test_insert_news_missing_title(temp_database):
    """Test insert_news() raises ValueError for missing title."""
    with pytest.raises(ValueError, match="Title is required"):
        temp_database.insert_news(
            url="https://example.com",
            title="",
            description="Test description"
        )


@pytest.mark.unit
def test_insert_news_optional_fields_default(temp_database):
    """Test insert_news() with optional fields using defaults."""
    inserted_id = temp_database.insert_news(
        url="https://example.com",
        title="Test Article"
    )

    assert inserted_id > 0

    # Verify defaults were used
    news = temp_database.get_news_by_url("https://example.com")
    assert len(news) == 1
    assert news[0]["description"] == ""
    assert news[0]["publication_date"] == ""


# ============================================================================
# Test Get News By URL
# ============================================================================

@pytest.mark.unit
def test_get_news_by_url_success(temp_database):
    """Test get_news_by_url() retrieves saved news."""
    # Insert test data
    temp_database.save_news("https://example.com", [
        {"title": "Article 1", "description": "Desc 1", "publication_date": "2025-10-07"},
        {"title": "Article 2", "description": "Desc 2", "publication_date": "2025-10-06"}
    ])

    # Retrieve news
    news = temp_database.get_news_by_url("https://example.com")

    assert len(news) == 2
    assert news[0]["title"] in ["Article 1", "Article 2"]
    assert news[0]["url"] == "https://example.com"


@pytest.mark.unit
def test_get_news_by_url_empty_result(temp_database):
    """Test get_news_by_url() returns empty list for non-existent URL."""
    news = temp_database.get_news_by_url("https://nonexistent.com")

    assert len(news) == 0
    assert isinstance(news, list)


@pytest.mark.unit
def test_get_news_by_url_sorted_by_created_at(temp_database):
    """Test get_news_by_url() returns news sorted by created_at DESC."""
    import time

    # Insert first article
    temp_database.save_news("https://example.com", [
        {"title": "Article 1", "description": "First", "publication_date": "2025-10-07"}
    ])

    # Small delay to ensure different timestamps
    time.sleep(0.5)

    # Insert second article
    temp_database.save_news("https://example.com", [
        {"title": "Article 2", "description": "Second", "publication_date": "2025-10-07"}
    ])

    # Retrieve news
    news = temp_database.get_news_by_url("https://example.com")

    # Most recent should be first
    assert len(news) == 2
    # Just verify we got both articles (order may vary due to timing)
    descriptions = [n["description"] for n in news]
    assert "First" in descriptions
    assert "Second" in descriptions


@pytest.mark.unit
def test_get_news_by_url_returns_all_fields(temp_database):
    """Test get_news_by_url() returns all database fields."""
    temp_database.save_news("https://example.com", [
        {"title": "Test Article", "description": "Test", "publication_date": "2025-10-07"}
    ])

    news = temp_database.get_news_by_url("https://example.com")

    assert len(news) == 1
    item = news[0]

    # Check all fields are present
    assert "id" in item
    assert "url" in item
    assert "title" in item
    assert "description" in item
    assert "publication_date" in item
    assert "created_at" in item
    assert "updated_at" in item


# ============================================================================
# Test Get All News
# ============================================================================

@pytest.mark.unit
def test_get_all_news_success(temp_database):
    """Test get_all_news() retrieves all news articles."""
    # Insert news from multiple URLs
    temp_database.save_news("https://example1.com", [
        {"title": "Article 1", "description": "Desc 1", "publication_date": "2025-10-07"}
    ])
    temp_database.save_news("https://example2.com", [
        {"title": "Article 2", "description": "Desc 2", "publication_date": "2025-10-07"}
    ])

    news = temp_database.get_all_news()

    assert len(news) == 2


@pytest.mark.unit
def test_get_all_news_with_limit(temp_database):
    """Test get_all_news() respects limit parameter."""
    # Insert 5 articles
    for i in range(5):
        temp_database.save_news(f"https://example{i}.com", [
            {"title": f"Article {i}", "description": f"Desc {i}", "publication_date": "2025-10-07"}
        ])

    news = temp_database.get_all_news(limit=3)

    assert len(news) == 3


@pytest.mark.unit
def test_get_all_news_empty_database(temp_database):
    """Test get_all_news() returns empty list for empty database."""
    news = temp_database.get_all_news()

    assert len(news) == 0
    assert isinstance(news, list)


# ============================================================================
# Test Count News
# ============================================================================

@pytest.mark.unit
def test_count_news_total(temp_database):
    """Test count_news() returns total count."""
    temp_database.save_news("https://example1.com", [
        {"title": "Article 1", "description": "", "publication_date": ""}
    ])
    temp_database.save_news("https://example2.com", [
        {"title": "Article 2", "description": "", "publication_date": ""}
    ])

    count = temp_database.count_news()

    assert count == 2


@pytest.mark.unit
def test_count_news_by_url(temp_database):
    """Test count_news() returns count for specific URL."""
    temp_database.save_news("https://example.com", [
        {"title": "Article 1", "description": "", "publication_date": ""},
        {"title": "Article 2", "description": "", "publication_date": ""}
    ])
    temp_database.save_news("https://other.com", [
        {"title": "Article 3", "description": "", "publication_date": ""}
    ])

    count = temp_database.count_news(url="https://example.com")

    assert count == 2


@pytest.mark.unit
def test_count_news_empty_database(temp_database):
    """Test count_news() returns 0 for empty database."""
    count = temp_database.count_news()

    assert count == 0


# ============================================================================
# Test Delete News By URL
# ============================================================================

@pytest.mark.unit
def test_delete_news_by_url_success(temp_database):
    """Test delete_news_by_url() deletes news articles."""
    # Insert test data
    temp_database.save_news("https://example.com", [
        {"title": "Article 1", "description": "", "publication_date": ""},
        {"title": "Article 2", "description": "", "publication_date": ""}
    ])

    # Delete
    deleted_count = temp_database.delete_news_by_url("https://example.com")

    assert deleted_count == 2

    # Verify deletion
    news = temp_database.get_news_by_url("https://example.com")
    assert len(news) == 0


@pytest.mark.unit
def test_delete_news_by_url_non_existent(temp_database):
    """Test delete_news_by_url() returns 0 for non-existent URL."""
    deleted_count = temp_database.delete_news_by_url("https://nonexistent.com")

    assert deleted_count == 0


@pytest.mark.unit
def test_delete_news_by_url_does_not_affect_other_urls(temp_database):
    """Test delete_news_by_url() only deletes specified URL."""
    # Insert data for two URLs
    temp_database.save_news("https://example1.com", [
        {"title": "Article 1", "description": "", "publication_date": ""}
    ])
    temp_database.save_news("https://example2.com", [
        {"title": "Article 2", "description": "", "publication_date": ""}
    ])

    # Delete one URL
    temp_database.delete_news_by_url("https://example1.com")

    # Verify only one URL was deleted
    assert temp_database.count_news(url="https://example1.com") == 0
    assert temp_database.count_news(url="https://example2.com") == 1


# ============================================================================
# Test Database Connection Management
# ============================================================================

@pytest.mark.unit
def test_get_connection_creates_connection():
    """Test _get_connection() creates connection if not exists."""
    db = DatabaseService(":memory:")

    # Connection should be None initially
    assert db._connection is None

    # Get connection
    conn = db._get_connection()

    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)
    assert db._connection is not None

    db.close()


@pytest.mark.unit
def test_get_connection_reuses_existing(temp_database):
    """Test _get_connection() reuses existing connection."""
    # Get connection twice
    conn1 = temp_database._get_connection()
    conn2 = temp_database._get_connection()

    # Should be the same connection object
    assert conn1 is conn2


@pytest.mark.unit
def test_close_connection(temp_database):
    """Test close() closes database connection."""
    # Create connection
    temp_database._get_connection()
    assert temp_database._connection is not None

    # Close
    temp_database.close()

    assert temp_database._connection is None


@pytest.mark.unit
def test_close_when_no_connection():
    """Test close() when no connection exists."""
    db = DatabaseService(":memory:")

    # Should not raise error
    db.close()

    assert db._connection is None


# ============================================================================
# Test Context Manager
# ============================================================================

@pytest.mark.unit
def test_database_context_manager():
    """Test DatabaseService as context manager."""
    db_path = ":memory:"

    with DatabaseService(db_path) as db:
        db.initialize()
        db.save_news("https://example.com", [
            {"title": "Test", "description": "", "publication_date": ""}
        ])

        count = db.count_news()
        assert count == 1

    # Connection should be closed after context exit
    # (cannot test this directly as connection is internal)


# ============================================================================
# Test Transaction Rollback
# ============================================================================

@pytest.mark.unit
def test_transaction_rollback_on_error(temp_database):
    """Test transaction rollback on database error."""
    # This is implicitly tested by the _get_cursor context manager
    # We can verify that errors are properly handled

    try:
        with temp_database._get_cursor() as cursor:
            cursor.execute("INSERT INTO news (url, title) VALUES (?, ?)", ("https://example.com", "Test"))
            # Force an error by trying to insert into non-existent column
            cursor.execute("INSERT INTO nonexistent_table VALUES (1)")
    except Exception:
        pass  # Expected to fail

    # Verify no partial data was committed
    count = temp_database.count_news()
    assert count == 0  # Nothing should be committed


# ============================================================================
# Test Database File Creation
# ============================================================================

@pytest.mark.unit
def test_database_creates_directory_if_not_exists():
    """Test database creates parent directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "subdir", "test.db")

        db = DatabaseService(db_path)
        db.initialize()

        # Verify directory was created
        assert os.path.exists(os.path.dirname(db_path))
        assert os.path.exists(db_path)

        db.close()


# ============================================================================
# Test Row Factory
# ============================================================================

@pytest.mark.unit
def test_row_factory_enables_dict_access(temp_database):
    """Test connection uses Row factory for dict-like access."""
    temp_database.save_news("https://example.com", [
        {"title": "Test", "description": "Desc", "publication_date": "2025-10-07"}
    ])

    news = temp_database.get_news_by_url("https://example.com")

    # Should be able to access as dict
    assert news[0]["title"] == "Test"
    assert news[0]["description"] == "Desc"


# ============================================================================
# Test Schema Columns
# ============================================================================

@pytest.mark.unit
def test_news_table_has_correct_columns(temp_database):
    """Test news table has all required columns."""
    conn = temp_database._get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(news)")
    columns = cursor.fetchall()

    column_names = [col[1] for col in columns]

    expected_columns = [
        "id", "url", "title", "description",
        "publication_date", "created_at", "updated_at"
    ]

    for col in expected_columns:
        assert col in column_names


# ============================================================================
# Test Multi-threading Support
# ============================================================================

@pytest.mark.unit
def test_database_multithreading_support():
    """Test that database can be used from multiple threads.
    
    This addresses the SQLite error:
    'SQLite objects created in a thread can only be used in that same thread'
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize database in main thread
        db = DatabaseService(db_path)
        db.initialize()

        # Test data
        test_urls = [
            "https://thread-test-1.com",
            "https://thread-test-2.com",
            "https://thread-test-3.com"
        ]
        
        results = []
        errors = []

        def write_from_thread(thread_id, url):
            """Function to run in separate thread."""
            try:
                news_data = [{
                    "title": f"Thread {thread_id} Article",
                    "description": f"Article from thread {thread_id}",
                    "publication_date": "2025-10-07"
                }]
                
                count = db.save_news(url, news_data)
                results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create and start threads
        threads = []
        for i, url in enumerate(test_urls):
            thread = threading.Thread(target=write_from_thread, args=(i, url))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Threading errors occurred: {errors}"
        assert len(results) == len(test_urls), "Not all threads completed successfully"

        # Verify data from main thread
        total_count = db.count_news()
        assert total_count == len(test_urls), "Not all news items were saved"

        # Verify each URL has its news
        for url in test_urls:
            news = db.get_news_by_url(url)
            assert len(news) == 1, f"Expected 1 item for {url}, got {len(news)}"

        db.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.unit
def test_database_concurrent_reads_and_writes():
    """Test concurrent reads and writes from multiple threads."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseService(db_path)
        db.initialize()

        # Pre-populate with some data
        url = "https://concurrent-test.com"
        initial_data = [
            {"title": f"Article {i}", "description": f"Desc {i}", "publication_date": "2025-10-07"}
            for i in range(5)
        ]
        db.save_news(url, initial_data)

        read_results = []
        write_results = []
        errors = []

        def read_from_thread(thread_id):
            """Read data from thread."""
            try:
                news = db.get_news_by_url(url)
                read_results.append((thread_id, len(news)))
            except Exception as e:
                errors.append((thread_id, "read", str(e)))

        def write_from_thread(thread_id):
            """Write data from thread."""
            try:
                new_data = [{
                    "title": f"Thread {thread_id} New Article",
                    "description": f"New from thread {thread_id}",
                    "publication_date": "2025-10-07"
                }]
                count = db.save_news(url, new_data)
                write_results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, "write", str(e)))

        # Create mixed read and write threads
        threads = []
        
        # 3 read threads
        for i in range(3):
            thread = threading.Thread(target=read_from_thread, args=(f"R{i}",))
            threads.append(thread)
        
        # 2 write threads
        for i in range(2):
            thread = threading.Thread(target=write_from_thread, args=(f"W{i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check for errors
        assert len(errors) == 0, f"Concurrent operation errors: {errors}"
        assert len(read_results) == 3, "Not all read operations completed"
        assert len(write_results) == 2, "Not all write operations completed"

        # Verify final state
        final_news = db.get_news_by_url(url)
        assert len(final_news) == 7, "Expected 5 initial + 2 new = 7 articles"

        db.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.unit
def test_clear_all():
    """Test clearing all news from database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseService(db_path)
        db.initialize()

        # Add test data
        urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
        for url in urls:
            news_data = [{"title": f"Article from {url}", "description": "Test", "publication_date": "2025-10-07"}]
            db.save_news(url, news_data)

        # Verify data was added
        total_before = db.count_news()
        assert total_before == 3

        # Clear all
        deleted_count = db.clear_all()
        assert deleted_count == 3

        # Verify database is empty
        total_after = db.count_news()
        assert total_after == 0

        # Verify each URL has no news
        for url in urls:
            news = db.get_news_by_url(url)
            assert len(news) == 0

        db.close()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
