VENV := .venv
PYTHON := $(VENV)/bin/python
CALL_BUDGET ?= 40
MAX_HOPS ?= 6
WEIGHTS ?=
FORCE ?= 0
BENCHMARK_QUESTION_FILES := \
	polling_test/questions/presidential_2012_first_round.txt \
	polling_test/questions/presidential_2017_first_round.txt \
	polling_test/questions/q3_presidential_2022.txt \
	polling_test/questions/insee_sex.txt \
	polling_test/questions/insee_age_group.txt \
	polling_test/questions/insee_csp.txt \
	polling_test/questions/insee_region.txt \
	polling_test/questions/insee_urban_area.txt \
	polling_test/questions/insee_camme_financial_future.txt \
	polling_test/questions/insee_camme_major_purchases.txt \
	polling_test/questions/insee_camme_unemployment_future.txt

.PHONY: install test-choice test-noul test-score benchmark-gender wikipedia-race poll benchmark-poll compare-benchmarks calibrate-weights generate-population validate-population

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

poll:
ifndef QUESTION_FILE
	$(error QUESTION_FILE is required; use: make poll QUESTION_FILE=path/to/question.txt [LIMIT=1000])
endif
	uv run --env-file .env --python $(PYTHON) polling_test/polling/poll_population.py --csv "$(or $(CSV),polling_test/population/population_sample.csv)" --question-file "$(QUESTION_FILE)" --limit "$(or $(LIMIT),0)" --output-dir "$(or $(OUTPUT_DIR),polling_test/results)" --quiet $(if $(filter 1 true yes,$(FORCE)),--force,)

benchmark-poll:
	uv run --env-file .env --python $(PYTHON) polling_test/polling/poll_population.py --csv "$(or $(CSV),polling_test/population/population_sample.csv)" --limit "$(or $(LIMIT),0)" --output-dir "$(or $(OUTPUT_DIR),polling_test/results)" --quiet $(if $(filter 1 true yes,$(FORCE)),--force,) $(foreach file,$(BENCHMARK_QUESTION_FILES),--question-file "$(file)")

compare-benchmarks:
	uv run --python $(PYTHON) polling_test/polling/compare_benchmarks.py $(if $(WEIGHTS),--weights "$(WEIGHTS)",)

calibrate-weights:
	uv run --python $(PYTHON) polling_test/polling/calibrate_weights.py

generate-population:
	uv run --python $(PYTHON) population/create_population_sample.py

validate-population:
	uv run --python $(PYTHON) population/validate_population_sample.py
