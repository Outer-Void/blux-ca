PYTHON ?= python3

.PHONY: install fmt lint types test generated wheel ci

install:
	$(PYTHON) -m pip install -e '.[dev]'

fmt:
	ruff format .

lint:
	ruff format --check .
	ruff check .

types:
	mypy

test:
	$(PYTHON) -m pytest

# Schemas and .blux/capabilities.yaml are generated from src/blux_ca/construction/spec.py.
generated:
	$(PYTHON) scripts/gen_schemas.py --check

wheel:
	PYTHON=$(PYTHON) bash scripts/verify_wheel.sh

ci: lint types generated test wheel
