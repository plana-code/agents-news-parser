
import sqlite3

DATABASE_NAME = "news.db"

def get_db_connection():
    """Creates a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the news table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            publication_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()

def insert_news(url: str, title: str, description: str, publication_date: str):
    """Inserts a new news article into the database."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO news (url, title, description, publication_date)
        VALUES (?, ?, ?, ?)
    """, (url, title, description, publication_date))
    conn.commit()
    conn.close()

def get_news_by_url(url: str):
    """Retrieves all news articles for a given URL."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM news WHERE url = ?", (url,))
    news = cursor.fetchall()
    conn.close()
    return news
