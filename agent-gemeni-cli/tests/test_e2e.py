
import os
import csv
from src.scraper import scrape_url
from src.llm_client import extract_news_with_llm
from src.database import create_table, insert_news, get_news_by_url
from src.csv_exporter import export_to_csv

TEST_URL = "https://www.gazeta.ru/"

def test_e2e():
    """End-to-end test for the Smart News Aggregator."""
    # 1. Scrape the website
    html_content = scrape_url(TEST_URL)
    assert isinstance(html_content, str)
    assert len(html_content) > 0

    # 2. Extract news using the LLM
    extracted_data = extract_news_with_llm(html_content)
    assert isinstance(extracted_data, dict)
    assert "choices" in extracted_data

    news_list_str = extracted_data.get('choices', [{}])[0].get('message', {}).get('content')
    assert news_list_str is not None

    import json
    news_data = json.loads(news_list_str)
    if isinstance(news_data, dict):
        news_list = news_data.get('articles', [])
    else:
        news_list = news_data
    assert isinstance(news_list, list)
    assert len(news_list) > 0

    # 3. Save the news to the database
    create_table()
    for item in news_list:
        insert_news(TEST_URL, item.get('title'), item.get('description'), item.get('publication_date'))

    # 4. Export the news to a CSV file
    news_from_db = get_news_by_url(TEST_URL)
    export_to_csv(news_from_db, TEST_URL)

    # 5. Verify the CSV file is created and contains data
    filename = TEST_URL.replace("https://", "").replace("/", "_") + ".csv"
    assert os.path.exists(filename)

    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert len(rows) > 0

    os.remove(filename)
