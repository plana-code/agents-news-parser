
import os
import csv
from src.csv_exporter import export_to_csv

def test_export_to_csv():
    """Tests if the export_to_csv function creates a CSV file with the correct content."""
    url = "http://test.com"
    news = [
        {"title": "Title 1", "description": "Description 1", "publication_date": "2025-10-01"},
        {"title": "Title 2", "description": "Description 2", "publication_date": "2025-10-02"},
    ]
    filename = url.replace("https://", "").replace("/", "_") + ".csv"

    export_to_csv(news, url)

    assert os.path.exists(filename)

    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["title"] == "Title 1"
        assert rows[1]["title"] == "Title 2"

    os.remove(filename)
