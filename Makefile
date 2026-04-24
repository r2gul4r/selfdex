SHELL := /bin/sh
.SHELLFLAGS := -eu -c
.RECIPEPREFIX := >
.SILENT:

.PHONY: help lint test check plan

help:
>printf '%s\n' \
>  'Available targets:' \
>  '  make lint  - Compile Python scripts' \
>  '  make test  - Run planner smoke tests' \
>  '  make plan  - Print next task plan' \
>  '  make check - Run lint + test'

lint:
>python3 -m compileall -q scripts

test:
>python3 scripts/plan_next_task.py --root . --format json >/dev/null
>python3 scripts/plan_next_task.py --root . --format markdown >/dev/null

plan:
>python3 scripts/plan_next_task.py --root . --format markdown

check: lint test
