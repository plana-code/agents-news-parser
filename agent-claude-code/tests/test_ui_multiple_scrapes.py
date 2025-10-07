"""Test UI multiple scrape requests to prevent hanging."""

import pytest
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ui.main_window import MainWindow
from scraper import ScraperService
from llm_service import OpenRouterService
from database import DatabaseService
from csv_exporter import CSVExporter


@pytest.mark.unit
def test_ui_handles_multiple_scrape_requests():
    """Test that UI can handle multiple scrape requests without hanging.
    
    This addresses the bug where second scrape request always hangs
    due to asyncio event loop issues.
    """
    # Initialize services
    scraper = ScraperService(timeout=10000, max_retries=1)
    api_key = "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"
    llm = OpenRouterService(api_key=api_key)
    db = DatabaseService(':memory:')
    exporter = CSVExporter()
    
    # Create window
    window = MainWindow(scraper, llm, db, exporter)
    
    # Verify scraper config is stored, not instance
    assert 'timeout' in window.scraper_config
    assert 'headless' in window.scraper_config
    assert 'max_retries' in window.scraper_config
    assert window.scraper_config['timeout'] == 10000
    assert window.scraper_config['max_retries'] == 1
    
    # Verify we can create new instances
    async def test_multiple_instances():
        # First scrape
        async with ScraperService(**window.scraper_config) as s1:
            assert s1 is not None
            assert s1.timeout == 10000
        
        # Second scrape (should not hang or fail)
        async with ScraperService(**window.scraper_config) as s2:
            assert s2 is not None
            assert s2.timeout == 10000
        
        # Verify they are different instances
        assert id(s1) != id(s2)
    
    # Run test
    asyncio.run(test_multiple_instances())


@pytest.mark.unit  
def test_scraper_config_preserved():
    """Test that scraper configuration is preserved in UI."""
    scraper = ScraperService(timeout=45000, headless=False, max_retries=5)
    api_key = "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"
    llm = OpenRouterService(api_key=api_key)
    db = DatabaseService(':memory:')
    exporter = CSVExporter()
    
    window = MainWindow(scraper, llm, db, exporter)
    
    assert window.scraper_config['timeout'] == 45000
    assert window.scraper_config['headless'] == False
    assert window.scraper_config['max_retries'] == 5
