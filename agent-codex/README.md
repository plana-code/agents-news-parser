%23 Smart News Aggregator (Python, Desktop UI, SQLite, OpenRouter)

A desktop app that scrapes dynamic news pages with user emulation (Playwright), extracts structured news using OpenRouter (free models only), stores in SQLite, and exports results to CSV.

## Features
- Desktop UI (Tkinter): URL input, Scrape, Export to CSV
- JS rendering with Playwright + user emulation tweaks
- LLM extraction via OpenRouter (free models), JSON-only output
- SQLite DB with audit fields and upsert
- CSV export by URL

## Quick Start

1) Setup

- Python 3.10+
- Install deps and Playwright browsers:

```
make setup
```

2) Run the desktop app

```
make run
```

3) Use the app

- Enter a URL (default: `https://www.gazeta.ru/`)
- Click `Scrape` to fetch and extract news
- Click `Export to CSV` to save results for that URL

## Configuration
- Set `OPENROUTER_API_KEY` to override the default token. By request, a default OpenRouter token is embedded for convenience.
- `NEWS_DB_PATH` to change the SQLite location (default: `data/news.db`).

Create `env/.env.example` and copy to your environment if desired.

## Testing

- Unit tests:
```
make test
```

- E2E (real network, OpenRouter, gazeta.ru):
```
RUN_E2E=1 make e2e
```

Notes:
- First run may download Playwright browsers.
- E2E requires outbound network access and valid OpenRouter availability.

## Implementation Notes
- Scraping: Playwright Chromium, headless by default, patches `navigator.webdriver`, sets UA and Accept-Language, scrolls to load content, waits for `networkidle`.
- LLM: Discovers free models from OpenRouter `/models` with a fallback allowlist. Prompts model to return strict JSON with up to 20 items.
- DB: Unique `(url, title)` ensures upsert semantics. Timestamps are UTC ISO strings.

## Make Targets
- `make setup` — Install deps and browsers
- `make run` — Start UI
- `make test` — Unit tests + coverage
- `make e2e` — E2E tests (requires `RUN_E2E=1`)
- `make lint` — Run black/ruff checks

## Structure
- `src/ui/app.py` — Tkinter UI
- `src/scraper/playwright_scraper.py` — Playwright scraper
- `src/llm/openrouter_client.py` — OpenRouter client + JSON parsing
- `src/db/database.py` — SQLite wrapper
- `src/services/pipeline.py` — End-to-end pipeline
- `src/utils/` — helpers, CSV exporter
- `tests/` — unit and e2e tests

## Reliability & Resilience
- Retries on scraping and LLM calls (exponential backoff)
- Reduced HTML passed to LLM to control prompt size
- Defensive JSON block extraction
- Headless mode controllable by editing code; consider non-headless for tougher sites

## License
No license files included. Do not commit secrets.
