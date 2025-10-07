PY ?= python3
PIP ?= pip3

.PHONY: setup run test lint playwright-install e2e

setup:
	$(PIP) install -r requirements.txt
	$(PY) -m playwright install

run:
	$(PY) -m src.main

test:
	pytest -q --maxfail=1 --cov=src

e2e:
	RUN_E2E=1 pytest -q -m e2e --maxfail=1

lint:
	$(PY) -m black --check src tests
	$(PY) -m ruff check src tests
