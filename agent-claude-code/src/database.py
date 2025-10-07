"""Database Module

This module handles SQLite database operations for storing news articles.
Includes CRUD operations and schema management.
"""

from typing import List, Optional, Dict, Any
import logging
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing SQLite database operations.

    Features:
    - Automatic schema initialization
    - CRUD operations for news articles
    - Bulk insert operations
    - Query by URL for export
    - Connection pooling and management
    """

    def __init__(self, db_path: str):
        """Initialize the database service.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()  # Thread-safe access to database
        logger.info(f"DatabaseService initialized with db_path: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            SQLite connection object
        """
        if self._connection is None:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            if not db_dir.exists():
                logger.debug(f"Creating database directory: {db_dir}")
                db_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Opening database connection: {self.db_path}")
            # check_same_thread=False allows SQLite to be used from different threads (needed for UI)
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.debug("Database connection established")

        return self._connection

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor with thread-safe access.

        Yields:
            Database cursor
        """
        with self._lock:  # Ensure thread-safe access
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error, rolling back: {str(e)}")
                raise
            finally:
                cursor.close()

    def initialize(self):
        """Create database schema if it doesn't exist.

        Creates the news table with the following structure:
        - id: INTEGER PRIMARY KEY AUTOINCREMENT
        - url: TEXT NOT NULL (source URL)
        - title: TEXT NOT NULL
        - description: TEXT
        - publication_date: TEXT
        - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        - updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        Also creates indexes on url and created_at columns for efficient queries.
        """
        logger.info("Initializing database schema...")

        with self._get_cursor() as cursor:
            # Create news table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    publication_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_url
                ON news(url)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_created_at
                ON news(created_at)
            """)

            logger.info("Database schema initialized successfully")

    def save_news(self, url: str, news_items: List[Dict[str, Any]]) -> int:
        """Save multiple news articles from a URL.

        Args:
            url: Source URL
            news_items: List of news item dictionaries with keys: title, description, publication_date

        Returns:
            Number of records inserted

        Raises:
            ValueError: If required fields are missing
        """
        if not url:
            raise ValueError("URL is required")

        if not news_items:
            logger.warning("No news items to save")
            return 0

        logger.info(f"Saving {len(news_items)} news items from {url}")

        inserted_count = 0
        with self._get_cursor() as cursor:
            for item in news_items:
                # Validate required fields
                if "title" not in item or not item["title"]:
                    logger.warning(f"Skipping item without title: {item}")
                    continue

                try:
                    cursor.execute("""
                        INSERT INTO news (url, title, description, publication_date)
                        VALUES (?, ?, ?, ?)
                    """, (
                        url,
                        item.get("title", ""),
                        item.get("description", ""),
                        item.get("publication_date", "")
                    ))
                    inserted_count += 1
                    logger.debug(f"Inserted: {item.get('title', '')[:50]}...")

                except sqlite3.Error as e:
                    logger.error(f"Failed to insert news item: {str(e)}")
                    # Continue with other items
                    continue

        logger.info(f"Successfully saved {inserted_count} news items")
        return inserted_count

    def insert_news(
        self,
        url: str,
        title: str,
        description: str = "",
        publication_date: str = ""
    ) -> int:
        """Insert a single news article into the database.

        Args:
            url: Source URL
            title: Article title
            description: Article description
            publication_date: Publication date (ISO format)

        Returns:
            The ID of the inserted record

        Raises:
            ValueError: If required fields are missing
        """
        if not url:
            raise ValueError("URL is required")

        if not title:
            raise ValueError("Title is required")

        logger.debug(f"Inserting news: {title[:50]}...")

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO news (url, title, description, publication_date)
                VALUES (?, ?, ?, ?)
            """, (url, title, description, publication_date))

            inserted_id = cursor.lastrowid
            logger.debug(f"Inserted news with ID: {inserted_id}")
            return inserted_id

    def get_news_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Retrieve all news articles for a given URL.

        Args:
            url: Source URL to query

        Returns:
            List of news article dictionaries with all fields
        """
        logger.debug(f"Retrieving news for URL: {url}")

        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT id, url, title, description, publication_date, created_at, updated_at
                FROM news
                WHERE url = ?
                ORDER BY created_at DESC
            """, (url,))

            rows = cursor.fetchall()
            news_items = []
            for row in rows:
                news_items.append({
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "description": row["description"],
                    "publication_date": row["publication_date"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })

            logger.debug(f"Retrieved {len(news_items)} news items for {url}")
            return news_items

    def get_all_news(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve all news articles from database.

        Args:
            limit: Optional limit on number of records to return

        Returns:
            List of news article dictionaries
        """
        logger.debug(f"Retrieving all news (limit={limit})")

        with self._get_cursor() as cursor:
            query = """
                SELECT id, url, title, description, publication_date, created_at, updated_at
                FROM news
                ORDER BY created_at DESC
            """

            if limit is not None:
                query += " LIMIT ?"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)

            rows = cursor.fetchall()

            news_items = []
            for row in rows:
                news_items.append({
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "description": row["description"],
                    "publication_date": row["publication_date"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })

            logger.debug(f"Retrieved {len(news_items)} total news items")
            return news_items

    def count_news(self, url: Optional[str] = None) -> int:
        """Count news articles, optionally filtered by URL.

        Args:
            url: Optional URL to filter by

        Returns:
            Number of news articles
        """
        with self._get_cursor() as cursor:
            if url:
                cursor.execute("SELECT COUNT(*) FROM news WHERE url = ?", (url,))
            else:
                cursor.execute("SELECT COUNT(*) FROM news")

            count = cursor.fetchone()[0]
            logger.debug(f"News count: {count} (url={url})")
            return count

    def delete_news_by_url(self, url: str) -> int:
        """Delete all news articles for a given URL.

        Args:
            url: Source URL

        Returns:
            Number of records deleted
        """
        logger.info(f"Deleting news for URL: {url}")

        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM news WHERE url = ?", (url,))
            deleted_count = cursor.rowcount
            logger.info(f"Deleted {deleted_count} news items")
            return deleted_count

    def clear_all(self) -> int:
        """Delete all news articles from the database.

        Returns:
            Number of records deleted
        """
        logger.info("Clearing all news from database...")

        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM news")
            deleted_count = cursor.rowcount
            logger.info(f"Cleared {deleted_count} news items")
            return deleted_count

    def close(self):
        """Close database connection."""
        if self._connection:
            logger.debug("Closing database connection...")
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
