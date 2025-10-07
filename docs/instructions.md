# Smart News Aggregator with LLM Integration

## Tech Stack
Python, Desktop UI, SQLite, OpenRouter API

## Features

### UI
- Input field for website URL
- "Scrape" button - synchronous execution with loader
- "Export to CSV" button - export all records by URL

### Process
1. Input URL → scraping with JS rendering
2. Send to LLM (OpenRouter) for news extraction
3. Save news to SQLite (title, description, publication date + audit fields)
4. Export to CSV

### Requirements
- Choose the best library for scraping with user emulation (anti-bot bypass)
- Use OpenRouter API with token from `OPENROUTER_API_KEY`
- Ensure reliability and resilience to failures and input data

## Testing
- Unit tests
- E2E without mocks: URL → scraping → LLM → DB → CSV

## Infrastructure
Dockerfile, docker-compose.yml, README.md

**Implementation details - at agent's discretion.**

---

## Execution Instructions
**BEFORE EXECUTION ANALYZE TASK AND CREATE DETAILED PLAN**

1. **Create plan:** Form detailed implementation plan in `TASK.MD` following the template: 
2. **Execution:** Execute each task in isolation (via sub-agents when possible)

3. **Completeness:** Bring to 100% completion, conduct full testing

4. **On errors:** Debug → restart → repeat until success

5. **Mandatory:**
    - Never interrupt under any circumstances
    - Keep the entire task in mind
    - Delegate to sub-agents where possible
    - After each phase update progress in `TASK.MD`
    - Avoid interruptions and unnecessary questions - complete all stated tasks

**Task is complete only when all components are 100% functional.**