import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from src.services.pipeline import run_pipeline
from src.db.database import Database
from src.utils.csv_exporter import export_to_csv


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Smart News Aggregator")
        root.geometry("720x220")

        self.db = Database()
        self.logger = logging.getLogger(__name__)

        self.url_label = tk.Label(root, text="Website URL:")
        self.url_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.url_entry = tk.Entry(root, width=100)
        self.url_entry.insert(0, "https://www.gazeta.ru/")
        self.url_entry.pack(padx=10, pady=(0, 10))

        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(padx=10, pady=5, anchor="w")

        self.scrape_button = tk.Button(
            self.buttons_frame, text="Scrape", command=self.on_scrape_click
        )
        self.scrape_button.pack(side=tk.LEFT, padx=(0, 10))

        self.export_button = tk.Button(
            self.buttons_frame, text="Export to CSV", command=self.on_export_click
        )
        self.export_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Idle")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="#555")
        self.status_label.pack(padx=10, pady=(10, 0), anchor="w")

    def set_loading(self, loading: bool, message: Optional[str] = None) -> None:
        self.scrape_button.config(state=tk.DISABLED if loading else tk.NORMAL)
        self.export_button.config(state=tk.DISABLED if loading else tk.NORMAL)
        if message is not None:
            self.status_var.set(message)

    def on_scrape_click(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        def job() -> None:
            try:
                self.logger.info("UI: scrape clicked, url=%s", url)
                self.set_loading(True, "Scraping and extracting news…")
                items = run_pipeline(url, self.db)
                self.logger.info("UI: pipeline returned items=%s", len(items))
                self.set_loading(False, f"Done. Fetched {len(items)} items.")
            except Exception as e:  # noqa: BLE001
                self.set_loading(False, "Error occurred.")
                self.logger.exception("UI: scrape error: %s", e)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=job, daemon=True).start()

    def on_export_click(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save CSV",
        )
        if not path:
            return
        self.logger.info("UI: export clicked, url=%s, path=%s", url, path)
        count = export_to_csv(self.db, url, path)
        self.status_var.set(f"Exported {count} rows to {path}")


def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
