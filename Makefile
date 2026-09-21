VENV := .venv
PYTHON := $(VENV)/bin/python

.PHONY: install test-choice test-noul test-score test-wikipedia-race

install:
	uv venv $(VENV) --allow-existing
	uv pip install --python $(PYTHON) -r requirements.txt

test-choice:
	uv run --env-file .env --python $(PYTHON) tests/test_surname_jev.py

test-noul:
	uv run --env-file .env --python $(PYTHON) tests/test_noul_jev.py

test-score:
	uv run --env-file .env --python $(PYTHON) tests/test_score_jev.py

test-wikipedia-race:
	uv run --env-file .env --python $(PYTHON) -m scripts.wikipedia_race_jev Beaver "Apollo 11"
