.PHONY: check build-check validate test

check: build-check validate test

build-check:
	PYTHONPATH=src uv run --no-project python -m handbook.cli build --check

validate:
	PYTHONPATH=src uv run --no-project python -m handbook.cli validate --fast

test:
	PYTHONPATH=src uv run --no-project --with pytest pytest -q
