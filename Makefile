VENV := .venv
PYTHON := $(VENV)/bin/python

.PHONY: install test

install:
	uv venv $(VENV) --allow-existing
	uv pip install --python $(PYTHON) -r requirements.txt

test:
	uv run --env-file .env --python $(PYTHON) tests/test_surname_jev.py
