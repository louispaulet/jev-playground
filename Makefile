VENV := .venv
PYTHON := $(VENV)/bin/python
CALL_BUDGET ?= 40
MAX_HOPS ?= 6

.PHONY: install test-choice test-noul test-score benchmark-gender wikipedia-race generate-population validate-population

install:
	uv venv $(VENV) --allow-existing
	uv pip install --python $(PYTHON) -r requirements.txt

test-choice:
	uv run --env-file .env --python $(PYTHON) tests/test_surname_jev.py

test-noul:
	uv run --env-file .env --python $(PYTHON) tests/test_noul_jev.py

test-score:
	uv run --env-file .env --python $(PYTHON) tests/test_score_jev.py

benchmark-gender:
	uv run --env-file .env --python $(PYTHON) -m scripts.benchmark_gender

wikipedia-race:
ifndef START
	$(error START is required; use: make wikipedia-race START=Beaver END="Apollo 11")
endif
ifndef END
	$(error END is required; use: make wikipedia-race START=Beaver END="Apollo 11")
endif
	uv run --env-file .env --python $(PYTHON) -m scripts.wikipedia_race_jev "$(START)" "$(END)" --call-budget $(CALL_BUDGET) --max-hops $(MAX_HOPS)

generate-population:
	uv run --python $(PYTHON) population/create_population_sample.py

validate-population:
	uv run --python $(PYTHON) population/validate_population_sample.py
