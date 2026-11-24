# Changelog

All notable changes to the `databricks-handbook` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-24

### Added
- **Packaged CLI Tooling (`handbook`)**: Unified package under `src/handbook/` replacing `scripts/` junk drawer; exposes `handbook build`, `handbook validate`, `handbook readme`, `handbook export-ipynb`, and `handbook explore`.
- **Single Curriculum Registry**: `src/handbook/curriculum.py` as single source of truth for all module specs, ID ranges, notebook counts (105), whiteboards (52), and drills, eliminating hard-coded magic numbers across the codebase.
- **Robust Multi-Layer CI/CD**: Pinned GitHub Actions workflows in `.github/workflows/` (`ci.yml`, `security.yml`, `nightly-smoke.yml`) with concurrency controls, least-privilege permissions (`contents: read`), drift detection, and local Spark smoke suite.
- **Dependency & Toolchain Hardening**: Modular extras in `pyproject.toml` (`dev`, `spark`, `connect`, `app`, `ml`), `.python-version` pinned to 3.11, committed `uv.lock`, and mutually-exclusive documentation for `pyspark` and `databricks-connect`.
- **Automated Pre-Commit & Secret Scanning**: `.pre-commit-config.yaml` and `.gitleaks.toml` rules protecting against credential leaks.
- **Comprehensive Test Suite Expansion**: Pytest suite in `tests/` expanded from 15 to 24 tests across `unit/`, `content/`, and `bundle/`, including Code-Test-Doc Triad integrity assertions and pure-Spark smoke tests.
- **Governance & Contributor Ergonomics**: Contributor Covenant 2.1 `CODE_OF_CONDUCT.md`, enterprise vulnerability disclosure `SECURITY.md`, GitHub issue templates (`content-error.yml`, `new-recipe.yml`), PR template with Triad checklist (`PULL_REQUEST_TEMPLATE.md`), `CODEOWNERS`, and `CITATION.cff`.
- **Modular Documentation & Whiteboards**: Split monolithic 338 KB whiteboard document into `docs/whiteboards/` domain chapters (`01_fabric_power_bi.md` .. `07_data_modeling_architecture.md`) and index; authored `docs/curriculum/index.md` and developer guide `docs/development.md`.

### Changed
- **Root Directory Cleanup**: Reduced top-level clutter from 25 entries to clean layout; relocated `ROADMAP.md` and `TAXONOMY.md` to `docs/`, eliminated `topics/` directory in favor of `docs/curriculum/topics.md`.
- **README Compaction**: Refactored generated 150 KB monolith README down to ~170 lines with dynamically generated modules table (`handbook readme`).
- **Databricks Asset Bundle Parameterization**: Replaced hardcoded service principal UUID with bundle variable `${var.prod_service_principal_id}` in `databricks.yml`.
- **Link & Anchor Integrity**: Resolved all 46 broken in-page anchors and relative links across all documentation (verified 0 broken links/anchors).

### Fixed
- **Audit Contamination (F1)**: Archived lakehouse-architect audit doc to `docs/archive/` and authored repo-accurate audit in `docs/audits/2026-11-structure-audit.md`.
- **Dangling Skill Reference**: Installed missing `ecosystem-ci-cd-quality-gate` skill in `.agents/skills/` and renumbered `AGENTS.md`.

---

## [1.0.0] - 2026-11-17

### Added
- Initial enterprise release of Databricks Data Intelligence Platform Handbook.
- 105 Databricks source notebooks across 10 modules covering foundational architecture to principal production incident triage.
- 6 production incident runbooks (`runbooks/`).
- 4 production architecture guides (`architectures/`).
- 5 technical interview guides (`interview/`).
- 52 visual architecture whiteboard blueprints (`assets/whiteboards/`).
- Databricks Asset Bundle (DAB) definitions (`databricks.yml`, `resources/`).
- Lakehouse FinOps Monitor Databricks App (`apps/lakehouse_finops_monitor/`).
