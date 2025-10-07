
import os
import sqlite3
from src.database import get_db_connection, create_table, insert_news, get_news_by_url

DATABASE_NAME = "news.db"

def setup_module(module):
    """Setup the test database."""
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
    create_table()

def teardown_module(module):
    """Teardown the test database."""
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)

def test_create_table():
    """Tests if the news table is created."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
    table_exists = cursor.fetchone() is not None
    conn.close()
    assert table_exists

def test_insert_and_get_news():
    """Tests inserting and retrieving a news article."""
    url = "http://test.com"
    title = "Test Title"
    description = "Test Description"
    publication_date = "2025-10-07"

    insert_news(url, title, description, publication_date)

    news = get_news_by_url(url)
    assert len(news) == 1
    article = news[0]
    assert article["url"] == url
    assert article["title"] == title
    assert article["description"] == description
    assert article["publication_date"] == publication_date
