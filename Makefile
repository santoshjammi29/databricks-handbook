# ==============================================================================
# The Databricks Handbook - Automation & Quality Gate Makefile
# ==============================================================================

.PHONY: help install build build-check lint lint-fix test validate validate-fast docs readme-check schema smoke clean check

PYTHON ?= python3
UV ?= uv

help:
	@echo "Available targets:"
	@echo "  install       - Synchronize dependencies and install package in editable mode"
	@echo "  build         - Generate all notebooks from source generators"
	@echo "  build-check   - Verify zero drift between generators and notebooks on disk"
	@echo "  lint          - Run ruff linter and format checks on src/, tests/, and apps/"
	@echo "  lint-fix      - Automatically fix safe ruff linting and formatting issues"
	@echo "  test          - Run test suite via pytest"
	@echo "  validate      - Run all validators (notebooks, bundle, hygiene, links)"
	@echo "  validate-fast - Run fast validators (skips deep link checking)"
	@echo "  docs          - Regenerate README dynamic blocks"
	@echo "  readme-check  - Verify README dynamic blocks exist and have zero drift"
	@echo "  schema        - Refresh Databricks bundle JSON schema from Databricks CLI"
	@echo "  smoke         - Run smoke test suite against Spark runtime"
	@echo "  clean         - Clean temporary build caches and virtualenv artifacts"
	@echo "  check         - Run full CI quality gate (lint + build-check + readme-check + validate-fast + test)"

install:
	$(UV) sync --locked --extra dev

build:
	$(UV) run python -m handbook.cli build

build-check:
	$(UV) run python -m handbook.cli build --check

lint:
	$(UV) run ruff check src tests apps
	$(UV) run ruff format --check src tests apps

lint-fix:
	$(UV) run ruff check --fix src tests apps
	$(UV) run ruff format src tests apps

test:
	$(UV) run pytest -q

validate:
	$(UV) run python -m handbook.cli validate

validate-fast:
	$(UV) run python -m handbook.cli validate --fast

docs:
	$(UV) run python -m handbook.cli readme

readme-check:
	$(UV) run python -m handbook.cli readme --check

schema:
	databricks bundle schema > src/handbook/data/bundle.schema.json
	databricks --version | head -n 1 > src/handbook/data/bundle.schema.version

smoke:
	$(UV) run pytest -m spark -q

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info *.egg-info htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

check: lint build-check readme-check validate-fast test
