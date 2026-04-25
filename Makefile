SHELL := /bin/sh
.SHELLFLAGS := -eu -c
.RECIPEPREFIX := >
.SILENT:

PYTHON ?= python

.PHONY: help lint test coverage-signal check plan budget drift

help:
>printf '%s\n' \
>  'Available targets:' \
>  '  make lint   - Compile Python scripts and tests' \
>  '  make test   - Run unit tests' \
>  '  make coverage-signal - Verify normalized coverage signal sample' \
>  '  make plan  - Print next task plan' \
>  '  make budget - Check campaign budget' \
>  '  make drift  - Check documentation drift' \
>  '  make check  - Run lint + test + coverage-signal + plan + budget + drift'

lint:
>$(PYTHON) -m compileall -q scripts tests

test:
>$(PYTHON) -m unittest discover -s tests

coverage-signal:
>$(PYTHON) scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format markdown

plan:
>$(PYTHON) scripts/plan_next_task.py --root . --format markdown

budget:
>$(PYTHON) scripts/check_campaign_budget.py --root . --format markdown

drift:
>$(PYTHON) scripts/check_doc_drift.py --root . --format markdown

check: lint test coverage-signal plan budget drift
