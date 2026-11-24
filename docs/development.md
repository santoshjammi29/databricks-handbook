# 🛠️ Databricks Handbook Developer & Contributor Guide

Welcome to the internal engineering and development guide for **The Databricks Handbook**.
This document outlines the generator architecture, development workflows, quality gates, and procedures for authoring and contributing production recipes.

---

## 1. Core Rule: Notebooks are Strictly Generated

> [!CAUTION]
> **NEVER HAND-EDIT FILES IN `notebooks/` DIRECTLY.**  
> The 105 Databricks source notebooks in `notebooks/` are programmatically assembled by deterministic generator modules located in `src/handbook/generators/`. Any manual changes made directly to `.py` files inside `notebooks/` will be flagged as drift by CI and overwritten upon the next build.

All notebook updates must be authored in the respective generator:
- Module 01 (`001–010`): `src/handbook/generators/mod01.py`
- Module 02 (`011–021`): `src/handbook/generators/mod02.py`
- Module 03 (`022–032`): `src/handbook/generators/mod03.py`
- Module 04 (`033–043`): `src/handbook/generators/mod04.py`
- Module 05 (`044–054`): `src/handbook/generators/mod05.py`
- Module 06 (`055–065`): `src/handbook/generators/mod06.py`
- Module 07 (`066–076`): `src/handbook/generators/mod07.py`
- Module 08 (`077–087`): `src/handbook/generators/mod08.py`
- Module 09 (`088–098`): `src/handbook/generators/mod09.py`
- Module 10 (`099–105`): `src/handbook/generators/mod10.py`

---

## 2. Quickstart & Local Setup

The repository uses `uv` for lightning-fast, reproducible virtual environment and package management:

```bash
# 1. Clone repository and navigate to root
git clone https://github.com/santoshjammi29/databricks-handbook.git
cd databricks-handbook

# 2. Install dependencies and dev tools into .venv
make install

# 3. Run the full quality gate
make check
```

---

## 3. Tooling & CLI Commands

The repository provides a unified CLI tool: `handbook`:

| Command | Action |
|---|---|
| `make check` | Runs full pre-flight verification (lint + build-check + validate-fast + test) |
| `make build` | Regenerates all notebooks from generator source strings |
| `make build-check` | Verifies zero drift between generators and disk (`handbook build --check`) |
| `make lint` | Validates code formatting and linting via `ruff` |
| `make test` | Runs the full 24-test pytest suite |
| `make validate` | Runs all validators (`notebooks`, `bundle`, `hygiene`, `links`) |
| `make clean` | Cleans temporary cache and build directories |

---

## 4. How to Add or Modify a Notebook Recipe

1. **Locate the generator module**:
   Find the generator in `src/handbook/generators/modNN.py`.

2. **Add or modify the recipe dictionary**:
   Every notebook must satisfy the **Code-Test-Doc Triad**:
   - `nb_id`: 3-digit zero-padded number (e.g. `"015"`).
   - `title`: Concise engineering title.
   - `business_scenario`: Real-world enterprise problem context.
   - `problem_statement`: Technical objective and constraints.
   - `architectural_notes`: Under-the-hood engine mechanics.
   - `sections`: Executable code sections with markdown explanations.
   - **Automated Assertions**: Must include at least one `assert` verifying invariants.

3. **Regenerate notebooks**:
   ```bash
   make build
   ```

4. **Verify drift and run checks**:
   ```bash
   make check
   ```

---

## 5. Databricks Asset Bundle (DAB) Configuration

The root `databricks.yml` governs deployments across three isolated environments:

- **`dev`**: Developer personal sandboxes in `/Users/<user>/.bundle/`.
- **`staging`**: Pre-production testing in `/Shared/.bundle/`.
- **`prod`**: Automated production workflows executed via Service Principal.

### Production Service Principal Variable
Production deployment mandates supplying the Service Principal client ID:
```bash
databricks bundle deploy -t prod --var="prod_service_principal_id=<CLIENT_ID>"
```
The production target specifies `run_as` using this variable:
```yaml
run_as:
  service_principal_name: "${var.prod_service_principal_id}"
```
This ensures zero reliance on human developer identities in automated environments.
