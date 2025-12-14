.PHONY: lint fmt test smoke

lint:
	python -m compileall .
	ruff check .
	black --check .

fmt:
	black .
	ruff check --fix .

test:
	pytest -q

smoke:
	python scripts/smoke.py
