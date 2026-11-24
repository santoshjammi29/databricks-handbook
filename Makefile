.PHONY: check

check:
	uv run --no-project --with pytest pytest -q
	python3 scripts/validate_notebooks.py
	python3 scripts/validate_bundle.py
