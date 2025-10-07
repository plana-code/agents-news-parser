import os
import tempfile

import pytest

from src.db.database import Database
from src.services.pipeline import run_pipeline


pytestmark = pytest.mark.e2e


@pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1", reason="E2E disabled; set RUN_E2E=1 to run"
)
def test_full_pipeline_real_openrouter_and_site():
    url = "https://www.gazeta.ru/"
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "news.db")
        db = Database(path=db_path)
        items = run_pipeline(url, db)
        assert isinstance(items, list)
        rows = db.query_by_url(url)
        assert len(rows) >= len(items)
        # Export CSV as final step to ensure I/O works
        from src.utils.csv_exporter import export_to_csv

        out = os.path.join(td, "export.csv")
        count = export_to_csv(db, url, out)
        assert os.path.exists(out)
        assert count == len(rows)
