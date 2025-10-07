
import csv
from typing import List

def export_to_csv(news: List[dict], url: str):
    """
    Exports a list of news articles to a CSV file.
    The CSV file will be named after the URL.
    """
    filename = url.replace("https://", "").replace("/", "_") + ".csv"
    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["title", "description", "publication_date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for article in news:
            writer.writerow({
                "title": article["title"],
                "description": article["description"],
                "publication_date": article["publication_date"],
            })
