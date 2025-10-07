"""Main Window UI Module

This module contains the main user interface for the news aggregator application.
Built with Gradio for cross-platform compatibility and easy Docker deployment.
"""

import logging
import asyncio
import os
from typing import Tuple

import gradio as gr

from scraper import ScraperService
from llm_service import OpenRouterService
from database import DatabaseService
from csv_exporter import CSVExporter

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window using Gradio.

    Features:
    - URL input field
    - Scrape button with loading indicator
    - Export to CSV button
    - Status/log display area
    - Progress feedback
    - Error display
    """

    def __init__(
        self,
        scraper: ScraperService,
        llm_service: OpenRouterService,
        database: DatabaseService,
        csv_exporter: CSVExporter
    ):
        """Initialize the main window.

        Args:
            scraper: ScraperService instance (used as template for config)
            llm_service: OpenRouterService instance
            database: DatabaseService instance
            csv_exporter: CSVExporter instance
        """
        # Store scraper config, not instance (to avoid event loop issues)
        self.scraper_config = {
            'timeout': scraper.timeout,
            'headless': scraper.headless,
            'max_retries': scraper.max_retries
        }
        self.llm_service = llm_service
        self.database = database
        self.csv_exporter = csv_exporter
        self.interface = None
        logger.info("MainWindow initialized")

    def create_interface(self) -> gr.Blocks:
        """Create and configure the Gradio interface.

        Returns:
            Gradio Blocks interface object ready to launch
        """
        logger.debug("Creating Gradio interface...")

        with gr.Blocks(title="Smart News Aggregator", theme=gr.themes.Soft()) as interface:
            gr.Markdown("""
            # Smart News Aggregator

            Extract news articles from any website using AI-powered parsing.

            **How to use:**
            1. Enter a news website URL (e.g., https://www.gazeta.ru/)
            2. Click "Scrape & Extract News" to fetch and analyze the page
            3. Click "Export to CSV" to download the results
            """)

            with gr.Row():
                url_input = gr.Textbox(
                    label="Website URL",
                    placeholder="https://www.gazeta.ru/",
                    scale=4
                )

            with gr.Row():
                scrape_btn = gr.Button("Scrape & Extract News", variant="primary", scale=2)
                export_btn = gr.Button("Export to CSV", variant="secondary", scale=2)
                clear_btn = gr.Button("Clear Database", variant="stop", scale=1)

            with gr.Row():
                status_output = gr.Textbox(
                    label="Status",
                    lines=15,
                    max_lines=20,
                    interactive=False,
                    show_copy_button=True
                )

            # Event handlers
            scrape_btn.click(
                fn=self.handle_scrape,
                inputs=[url_input],
                outputs=[status_output]
            )

            export_btn.click(
                fn=self.handle_export,
                inputs=[url_input],
                outputs=[status_output]
            )

            clear_btn.click(
                fn=self.handle_clear,
                inputs=[],
                outputs=[status_output]
            )

            gr.Markdown("""
            ---
            **Note:** Scraping may take 30-60 seconds depending on the website and LLM processing time.
            """)

        self.interface = interface
        logger.debug("Gradio interface created successfully")
        return interface

    def handle_scrape(self, url: str) -> str:
        """Handle scrape button click.

        Args:
            url: URL to scrape

        Returns:
            Status message to display
        """
        import time
        start_time = time.time()

        logger.info(f"="*60)
        logger.info(f"Received scrape request for: {url}")
        logger.info(f"="*60)

        if not url or not url.strip():
            logger.warning("Empty URL provided")
            return "Error: Please enter a URL"

        url = url.strip()

        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid URL format: {url}")
            return "Error: URL must start with http:// or https://"

        try:
            # Run async scraping in sync context
            status_messages = []

            # Step 1: Scraping
            status_messages.append(f"Step 1/4: Scraping {url}...")
            logger.info("Step 1/4: Starting web scraper...")
            scrape_start = time.time()

            # Create new scraper instance for each request to avoid event loop issues
            async def scrape_with_new_instance():
                async with ScraperService(**self.scraper_config) as scraper:
                    return await scraper.scrape(url)

            html_content = asyncio.run(scrape_with_new_instance())
            scrape_duration = time.time() - scrape_start

            status_messages.append(f"  Success: Retrieved {len(html_content)} characters of HTML content")
            logger.info(f"Scraping completed in {scrape_duration:.2f}s, HTML length: {len(html_content)} chars")

            # Step 2: LLM Extraction
            status_messages.append("\nStep 2/4: Extracting news with AI...")
            logger.info("Step 2/4: Sending HTML to LLM for extraction...")
            llm_start = time.time()

            news_items = self.llm_service.extract_news(html_content, url)
            llm_duration = time.time() - llm_start

            status_messages.append(f"  Success: Extracted {len(news_items)} news articles")
            logger.info(f"LLM extraction completed in {llm_duration:.2f}s, extracted {len(news_items)} items")

            if not news_items:
                status_messages.append("\nWarning: No news articles found on this page.")
                return "\n".join(status_messages)

            # Step 3: Save to Database
            status_messages.append("\nStep 3/4: Saving to database...")
            logger.info("Step 3/4: Saving news items to database...")
            db_start = time.time()

            # Convert NewsItem objects to dicts
            news_dicts = [item.to_dict() for item in news_items]
            saved_count = self.database.save_news(url, news_dicts)
            db_duration = time.time() - db_start

            status_messages.append(f"  Success: Saved {saved_count} articles to database")
            logger.info(f"Database save completed in {db_duration:.2f}s, saved {saved_count} articles")

            # Step 4: Display Summary
            status_messages.append("\nStep 4/4: Complete!")
            status_messages.append(f"\n{'='*60}")
            status_messages.append("EXTRACTED NEWS ARTICLES:")
            status_messages.append(f"{'='*60}\n")

            for i, item in enumerate(news_items[:10], 1):  # Show first 10
                status_messages.append(f"{i}. {item.title}")
                if item.description:
                    desc_preview = item.description[:100] + "..." if len(item.description) > 100 else item.description
                    status_messages.append(f"   {desc_preview}")
                if item.publication_date:
                    status_messages.append(f"   Date: {item.publication_date}")
                status_messages.append("")

            if len(news_items) > 10:
                status_messages.append(f"... and {len(news_items) - 10} more articles")

            total_duration = time.time() - start_time

            status_messages.append(f"\n{'='*60}")
            status_messages.append(f"Total: {len(news_items)} articles extracted and saved")
            status_messages.append(f"Total time: {total_duration:.2f}s")
            status_messages.append(f"{'='*60}")
            status_messages.append(f"\nReady to export! Click 'Export to CSV' button.")

            logger.info(f"="*60)
            logger.info(f"Pipeline complete in {total_duration:.2f}s - {len(news_items)} articles processed")
            logger.info(f"="*60)

            return "\n".join(status_messages)

        except ValueError as e:
            error_msg = f"Validation Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except TimeoutError as e:
            error_msg = f"Timeout Error: {str(e)}\n\nThe website took too long to respond. Please try again."
            logger.error(error_msg)
            return error_msg
        except RuntimeError as e:
            error_msg = f"Runtime Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}\n\nPlease check the logs for more details."
            logger.exception("Unexpected error in scrape handler")
            return error_msg

    def handle_export(self, url: str) -> str:
        """Handle export button click.

        Args:
            url: URL to filter export data

        Returns:
            Path to exported CSV file or error message
        """
        logger.info(f"Export handler called with URL: {url}")

        if not url or not url.strip():
            return "Error: Please enter a URL to export data for"

        url = url.strip()

        try:
            # Step 1: Query database for news
            logger.info(f"Querying database for URL: {url}")
            news_items = self.database.get_news_by_url(url)

            if not news_items:
                return f"No news articles found for URL: {url}\n\nPlease scrape the URL first."

            # Step 2: Export to CSV
            logger.info(f"Exporting {len(news_items)} items to CSV")
            csv_path = self.csv_exporter.export_to_csv(news_items, url=url)

            # Get absolute path for display
            abs_path = os.path.abspath(csv_path)

            success_msg = f"""
Export Successful!

File: {csv_path}
Full path: {abs_path}
Records: {len(news_items)} news articles

The CSV file contains:
- Title
- Description
- Publication Date
- Source URL
- Created Timestamp
"""
            logger.info(f"Export successful: {csv_path}")
            return success_msg

        except ValueError as e:
            error_msg = f"Validation Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except IOError as e:
            error_msg = f"File Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}\n\nPlease check the logs for more details."
            logger.exception("Unexpected error in export handler")
            return error_msg

    def handle_clear(self) -> str:
        """Handle clear database button click.

        Returns:
            Status message
        """
        logger.info("Clear database handler called")

        try:
            # Count items before clearing
            total_count = self.database.count_news()

            if total_count == 0:
                return "Database is already empty.\n\nNo articles to clear."

            # Clear all news
            logger.info(f"Clearing {total_count} news items from database")
            deleted_count = self.database.clear_all()

            success_msg = f"""
Database Cleared Successfully!

Deleted: {deleted_count} news articles
Status: Database is now empty

You can start scraping new websites.
"""
            logger.info(f"Database cleared: {deleted_count} items removed")
            return success_msg

        except Exception as e:
            error_msg = f"Error clearing database: {str(e)}\n\nPlease check the logs for more details."
            logger.exception("Unexpected error in clear handler")
            return error_msg

    def launch(self, share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860):
        """Launch the application interface.

        Args:
            share: Whether to create a public link
            server_name: Server hostname
            server_port: Server port
        """
        if self.interface is None:
            self.create_interface()

        logger.info(f"Launching Gradio interface on {server_name}:{server_port}")

        try:
            self.interface.launch(
                share=share,
                server_name=server_name,
                server_port=server_port,
                show_error=True,
                quiet=False
            )
        except Exception as e:
            logger.error(f"Failed to launch interface: {str(e)}")
            raise
