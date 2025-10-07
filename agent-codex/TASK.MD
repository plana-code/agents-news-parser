# Smart News Aggregator with LLM Integration — Project Plan

## Overview
Build a Python desktop app that scrapes dynamic news pages with user emulation, extracts structured news using OpenRouter (free models only), stores results in SQLite, and exports by URL to CSV. Include unit tests and an optional E2E test (real network, real token, real site: https://www.gazeta.ru/).

## Goals
- Desktop UI (Tkinter) with URL input, Scrape, and Export to CSV.
- Robust JS-rendering scraper with user emulation (Playwright).
- LLM extraction via OpenRouter (free models only, no reasoning models).
- SQLite persistence with audit fields.
- CSV export by URL.
- Reliability: timeouts, retries, graceful error handling.
- Tests: unit + E2E (no mocks) from URL → scrape → LLM → DB → CSV.

## Scope & Deliverables
- Source under `src/` organized by domain.
- Tests under `tests/` mirroring structure.
- Makefile with `setup`, `run`, `test`, `lint` targets.
- Scripts for setup (Playwright browsers).
- `env/.env.example` with configuration.
- README with usage and testing instructions.
- Working application end-to-end.

## Architecture
1. UI (Tkinter)
   - `src/ui/app.py` renders the window.
   - Input: URL. Buttons: Scrape, Export to CSV.
   - Sync UX with loader (disable inputs, show status) using a background thread.

2. Scraper (Playwright)
   - `src/scraper/playwright_scraper.py`
   - Anti-bot/user emulation: custom user agent, language headers, viewport, navigator.webdriver patch, scroll to bottom, wait-for-network-idle, timeouts, retries.
   - Output: page HTML + optional extracted candidate blocks to keep LLM prompt small.

3. LLM (OpenRouter)
   - `src/llm/openrouter_client.py`
   - Discovers models from `/models`, filters FREE, excludes reasoning models.
   - Fallback static allowlist of known free models if discovery fails.
   - Extraction: prompt model to return strictly JSON list of items `{title, description, publication_date}`.
   - Retry on rate/timeouts; defensive JSON parsing (first JSON block extraction) and schema validation.

4. Data
   - `src/db/database.py` SQLite with table `news` (id, url, title, description, publication_date, created_at, updated_at). Unique (url, title).
   - Insert with upsert semantics; query by URL.

5. Services
   - `src/services/pipeline.py` orchestrates scrape → LLM → DB and returns inserted/updated items.
   - `src/utils/csv_exporter.py` exports query results to CSV.
   - `src/utils/common.py` small helpers (slugify, json extraction, time, logging config).

## Data Model
NewsItem: { title: str, description: str, publication_date: Optional[str] }

## Reliability
- Playwright: retries on page load; content readiness waits; JS rendering; stealth-like patches.
- LLM: retries with exponential backoff; fallback to alternate free model on failure.
- DB: upsert with unique constraint; transactional inserts.
- UI: exceptions surfaced in status; buttons re-enabled on error.

## Security & Config
- Primary: use env var `OPENROUTER_API_KEY` if present.
- Per explicit user request, default to real token hardcoded as fallback (can be overridden by env).
- Do not store other secrets. Provide `env/.env.example`.

## Testing
- Unit tests: utils, DB insert/query, LLM JSON parsing.
- E2E: optional, real network. Marked `@pytest.mark.e2e` and runs if `RUN_E2E=1`.
- Site: https://www.gazeta.ru/; validates DB populated and CSV generated.

## Milestones & Tasks
1) Scaffold project (src/, tests/, scripts/, Makefile, README) — Done when files exist.
2) Implement Playwright scraper — Done when returns stable HTML and retries.
3) Implement OpenRouter client — Done when discovery + extraction works with fallback.
4) Implement DB + CSV — Done when insert/query/export pass unit tests.
5) Build Tkinter UI — Done when manual run supports scrape and export flows.
6) Add tests — Done when unit tests run; E2E passes when network enabled.
7) Docs — Done when README covers setup, run, test.

## Risks & Mitigations
- Anti-bot blocks: use Playwright + user agent + navigator patches + waits; user may toggle headful mode.
- Token or model availability: dynamic discovery with fallback allowlist.
- Prompt size: extract candidate blocks before LLM; truncate to safe token budget.
- Non-JSON LLM output: robust JSON block extraction and schema sanitation.

## Progress Log
- [x] Scaffold project
- [x] Scraper implemented
- [x] OpenRouter client implemented
- [x] DB + CSV implemented
- [x] UI implemented
- [x] Tests added (unit + E2E)
- [x] README written
- [x] Local validation (unit + E2E)
