import customtkinter
from tkinter import messagebox
import logging
from src.scraper import scrape_url
from src.llm_client import extract_news_with_llm
from src.database import create_table, insert_news, get_news_by_url
from src.csv_exporter import export_to_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart News Aggregator")
        self.geometry("700x350")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.url_frame = customtkinter.CTkFrame(self)
        self.url_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = customtkinter.CTkEntry(self.url_frame, placeholder_text="Enter website URL")
        self.url_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.scrape_button = customtkinter.CTkButton(self.url_frame, text="Scrape", command=self.scrape)
        self.scrape_button.grid(row=0, column=1, padx=10, pady=10)

        self.export_button = customtkinter.CTkButton(self, text="Export to CSV", command=self.export)
        self.export_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status: Idle")
        self.status_label.grid(row=2, column=0, padx=10, pady=10, sticky="sw")

    def scrape(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        try:
            logging.info(f"Scraping URL: {url}")
            self.status_label.configure(text="Status: Scraping...")
            self.update_idletasks()
            html_content = scrape_url(url)

            logging.info("Extracting news with LLM...")
            self.status_label.configure(text="Status: Extracting news...")
            self.update_idletasks()
            extracted_data = extract_news_with_llm(html_content)

            news_list_str = extracted_data.get('choices', [{}])[0].get('message', {}).get('content')
            if news_list_str:
                import json
                logging.info(f"Extracted news: {news_list_str}")
                news_data = json.loads(news_list_str)
                if isinstance(news_data, dict):
                    news_items = news_data.get('articles', [])
                else:
                    news_items = news_data

                for item in news_items:
                    insert_news(url, item.get('title'), item.get('description'), item.get('publication_date'))
                logging.info(f"Inserted {len(news_items)} articles into the database.")
                self.status_label.configure(text=f"Status: Successfully scraped and saved {len(news_items)} articles.")
            else:
                logging.warning("No news found.")
                self.status_label.configure(text="Status: No news found.")

        except Exception as e:
            logging.error(f"An error occurred: {e}", exc_info=True)
            messagebox.showerror("Error", str(e))
            self.status_label.configure(text="Status: Error")

    def export(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL to export.")
            return

        try:
            logging.info(f"Exporting news for URL: {url}")
            news = get_news_by_url(url)
            if not news:
                messagebox.showinfo("Info", "No news found for this URL.")
                return

            export_to_csv(news, url)
            logging.info(f"Successfully exported news to {url.replace('https://', '').replace('/', '_')}.csv")
            messagebox.showinfo("Success", f"Successfully exported news to {url.replace('https://', '').replace('/', '_')}.csv")
        except Exception as e:
            logging.error(f"An error occurred during export: {e}", exc_info=True)
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    create_table()
    app = App()
    app.mainloop()
