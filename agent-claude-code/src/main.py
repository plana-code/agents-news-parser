"""Application Entry Point

Main entry point for the Smart News Aggregator application.
"""

import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper import ScraperService
from llm_service import OpenRouterService
from database import DatabaseService
from csv_exporter import CSVExporter
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO"):
    """Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # File handler (DEBUG level for detailed logging)
    file_handler = logging.FileHandler('logs/app.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    logger.info("Logging configured: console=INFO, file=DEBUG, log_file=logs/app.log")


def load_config() -> dict:
    """Load configuration from environment variables.

    Returns:
        Dictionary with configuration values

    Raises:
        ValueError: If required configuration is missing
    """
    # Load .env file
    load_dotenv()

    # Get configuration values
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")

    db_path = os.getenv('DATABASE_PATH', 'data/news.db')
    export_path = os.getenv('EXPORT_PATH', 'exports/')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    scraper_timeout = int(os.getenv('SCRAPER_TIMEOUT', '30000'))
    llm_model = os.getenv('OPENROUTER_MODEL', 'qwen/qwen3-coder:free')

    config = {
        'api_key': api_key,
        'db_path': db_path,
        'export_path': export_path,
        'log_level': log_level,
        'scraper_timeout': scraper_timeout,
        'llm_model': llm_model
    }

    logger.info(f"Configuration loaded: db_path={db_path}, export_path={export_path}, log_level={log_level}, llm_model={llm_model}")
    return config


def initialize_services(config: dict) -> tuple:
    """Initialize all application services.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (scraper, llm_service, database, csv_exporter)
    """
    logger.info("Initializing services...")

    # Initialize scraper
    scraper = ScraperService(
        timeout=config['scraper_timeout'],
        headless=True,
        max_retries=3
    )

    # Initialize LLM service with FREE model
    llm_service = OpenRouterService(
        api_key=config['api_key'],
        model=config['llm_model'],
        max_retries=3,
        timeout=120
    )

    # Initialize database
    database = DatabaseService(db_path=config['db_path'])
    database.initialize()

    # Initialize CSV exporter
    csv_exporter = CSVExporter(export_path=config['export_path'])

    logger.info("All services initialized successfully")
    return scraper, llm_service, database, csv_exporter


def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = load_config()

        # Setup logging
        setup_logging(config['log_level'])

        logger.info("="*60)
        logger.info("Smart News Aggregator starting...")
        logger.info("="*60)

        # Initialize services
        scraper, llm_service, database, csv_exporter = initialize_services(config)

        # Create and launch UI
        logger.info("Creating UI...")
        main_window = MainWindow(
            scraper=scraper,
            llm_service=llm_service,
            database=database,
            csv_exporter=csv_exporter
        )

        logger.info("Launching application...")
        # Use 0.0.0.0 for Docker, 127.0.0.1 for local development
        # Check if running in Docker by looking for common Docker env variables
        is_docker = os.getenv('DOCKER_CONTAINER') == 'true' or os.path.exists('/.dockerenv')
        server_name = "0.0.0.0" if is_docker else "127.0.0.1"

        logger.info(f"Starting server on {server_name}:7860 (Docker mode: {is_docker})")
        main_window.launch(
            share=False,
            server_name=server_name,
            server_port=7860
        )

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"\nConfiguration Error: {str(e)}")
        print("\nPlease ensure .env file exists with required settings:")
        print("  - OPENROUTER_API_KEY=your_api_key_here")
        sys.exit(1)

    except Exception as e:
        logger.exception("Fatal error during startup")
        print(f"\nFatal Error: {str(e)}")
        print("\nCheck logs/app.log for more details")
        sys.exit(1)

    finally:
        # Cleanup (Gradio handles its own cleanup on shutdown)
        logger.info("Application shutdown")


if __name__ == "__main__":
    main()
