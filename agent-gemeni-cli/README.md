
# Smart News Aggregator

A desktop application for scraping news from websites, extracting information using an LLM, and exporting it to a CSV file.

## Features

- Scrape news from any website with JavaScript rendering.
- Extract news title, description, and publication date using the OpenRouter API.
- Save extracted news to a local SQLite database.
- Export news to a CSV file.

## Tech Stack

- Python
- customtkinter for the UI
- Playwright for scraping
- SQLite for the database
- OpenRouter API for LLM integration

## Getting Started

### Prerequisites

- Python 3.10 or later

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/smart-news-aggregator.git
   cd smart-news-aggregator
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

### Usage

1. Run the application:
   ```bash
   python src/main.py
   ```

2. Enter a website URL in the input field.

3. Click the "Scrape" button to start scraping and extracting news.

4. Click the "Export to CSV" button to export the news for the given URL to a CSV file.

## Testing

To run the tests, use the following command:

```bash
pytest
```
