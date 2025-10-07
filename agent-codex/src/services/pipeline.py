import logging
import time
from typing import List

from bs4 import BeautifulSoup

from src.db.database import Database
from src.llm.openrouter_client import NewsItem, extract_news_from_html
from src.scraper.playwright_scraper import PlaywrightScraper


def _reduce_html(html: str) -> str:
    # Reduce prompt: keep only relevant blocks like headings, article tags and links
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    texts = []
    # capture heading and article content, and link texts
    for sel in [
        "article",
        "h1, h2, h3, h4, h5, h6",
        "a",
        "div[class*='news'], section[class*='news']",
    ]:
        for node in soup.select(sel):
            text = node.get_text(" ", strip=True)
            if text and len(text) > 40:
                texts.append(text)
    combined = "\n".join(texts)
    # Hard cap size
    out = combined[:18000]
    logging.getLogger(__name__).debug(
        "Reduced HTML text length=%s", len(out)
    )
    return out


def _candidate_list(html: str, max_items: int = 40) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    candidates = []
    # Headlines first
    for h in soup.select("h1, h2, h3"):
        t = h.get_text(" ", strip=True)
        if t and len(t) > 20:
            candidates.append(t)
        if len(candidates) >= max_items:
            break
    # Links that look like news
    if len(candidates) < max_items:
        for a in soup.select("a"):
            t = a.get_text(" ", strip=True)
            if t and len(t) > 30:
                candidates.append(t)
            if len(candidates) >= max_items:
                break
    numbered = "\n".join(f"- {c}" for c in candidates[:max_items])
    logging.getLogger(__name__).debug(
        "Built candidate list items=%s", min(len(candidates), max_items)
    )
    return numbered


def run_pipeline(url: str, db: Database) -> List[NewsItem]:
    logger = logging.getLogger(__name__)
    t0 = time.time()
    logger.info("Pipeline started: %s", url)
    scraper = PlaywrightScraper(headless=True)
    result = scraper.scrape(url)

    # Prefer compact candidate list to avoid huge prompts
    candidates = _candidate_list(result.html)
    items = extract_news_from_html(candidates)
    inserted = db.upsert_news(url, items)
    logger.info(
        "Pipeline finished: %s items=%s inserted_or_updated=%s duration=%.2fs",
        url,
        len(items),
        inserted,
        time.time() - t0,
    )
    return items
