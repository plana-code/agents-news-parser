"""CSV Export Module

This module handles exporting news data to CSV format.
"""

from typing import List, Dict, Any
import logging
import csv
import os
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CSVExporter:
    """Service for exporting news data to CSV files.

    Features:
    - Export with proper headers
    - Handle special characters and encoding
    - Create output directory if needed
    - Handle empty results gracefully
    """

    def __init__(self, export_path: str = "exports/"):
        """Initialize the CSV exporter.

        Args:
            export_path: Directory path for CSV exports
        """
        self.export_path = export_path
        logger.info(f"CSVExporter initialized with export_path: {export_path}")

    def export_to_csv(
        self,
        news_items: List[Dict[str, Any]],
        url: str = "",
        filename: str = ""
    ) -> str:
        """Export news items to a CSV file.

        Args:
            news_items: List of news article dictionaries
            url: Source URL (used for auto-generating filename if filename not provided)
            filename: Output filename (without path). If empty, auto-generates from URL and timestamp

        Returns:
            Full path to the created CSV file

        Raises:
            ValueError: If news_items is invalid
            IOError: If file cannot be written
        """
        if not news_items:
            raise ValueError("No news items to export")

        if not isinstance(news_items, list):
            raise ValueError("news_items must be a list")

        # Ensure export directory exists
        self._ensure_export_directory()

        # Generate filename if not provided
        if not filename:
            filename = self._generate_filename(url)
        else:
            filename = self._sanitize_filename(filename)

        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'

        # Full output path
        output_path = os.path.join(self.export_path, filename)

        logger.info(f"Exporting {len(news_items)} news items to {output_path}")

        try:
            # Write CSV file
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define CSV headers
                fieldnames = ['title', 'description', 'publication_date', 'url', 'created_at']

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

                # Write header
                writer.writeheader()

                # Write data rows
                for item in news_items:
                    # Ensure all required fields exist
                    row = {
                        'title': str(item.get('title', '')).strip(),
                        'description': str(item.get('description', '')).strip(),
                        'publication_date': str(item.get('publication_date', '')).strip(),
                        'url': str(item.get('url', '')).strip(),
                        'created_at': str(item.get('created_at', '')).strip()
                    }

                    # Write row
                    writer.writerow(row)

            logger.info(f"Successfully exported to {output_path}")
            return output_path

        except IOError as e:
            logger.error(f"Failed to write CSV file: {str(e)}")
            raise IOError(f"Failed to write CSV file to {output_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during CSV export: {str(e)}")
            raise

    def _ensure_export_directory(self):
        """Create export directory if it doesn't exist."""
        export_dir = Path(self.export_path)
        if not export_dir.exists():
            logger.debug(f"Creating export directory: {self.export_path}")
            export_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Export directory created")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace invalid filename characters
        # Keep only alphanumeric, dash, underscore, and dot
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)

        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')

        # Limit length
        max_length = 200
        if len(sanitized) > max_length:
            # Keep extension if present
            if '.' in sanitized:
                name, ext = sanitized.rsplit('.', 1)
                sanitized = name[:max_length - len(ext) - 1] + '.' + ext
            else:
                sanitized = sanitized[:max_length]

        logger.debug(f"Sanitized filename: {filename} -> {sanitized}")
        return sanitized

    def _generate_filename(self, url: str) -> str:
        """Generate a filename from URL and timestamp.

        Args:
            url: Source URL

        Returns:
            Generated filename
        """
        # Extract domain from URL
        domain_part = "news"
        if url:
            try:
                # Simple domain extraction
                # Remove protocol
                url_part = url.replace('https://', '').replace('http://', '')
                # Get first part (domain)
                domain = url_part.split('/')[0]
                # Remove www. prefix
                domain = domain.replace('www.', '')
                # Remove TLD
                domain_part = domain.split('.')[0]
            except Exception as e:
                logger.warning(f"Failed to extract domain from URL: {str(e)}")
                domain_part = "news"

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Combine
        filename = f"{domain_part}_{timestamp}.csv"

        logger.debug(f"Generated filename: {filename}")
        return filename

    def export_news(
        self,
        news_items: List[Dict[str, Any]],
        filename: str
    ) -> str:
        """Export news items to a CSV file.

        Legacy method for backward compatibility.

        Args:
            news_items: List of news article dictionaries
            filename: Output filename (without path)

        Returns:
            Full path to the created CSV file

        Raises:
            ValueError: If news_items is invalid or filename is empty
            IOError: If file cannot be written
        """
        if not filename:
            raise ValueError("Filename is required")

        return self.export_to_csv(news_items, filename=filename)
