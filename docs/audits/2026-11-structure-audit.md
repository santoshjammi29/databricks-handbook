# 🏛️ Databricks Handbook: Structural Audit & Remediation Tracker

**Repository**: `databricks-handbook`  
**Date**: November 2026  
**Scope**: Security gates, validator truthfulness, CI/CD, documentation consistency, and executable content tiers  
**Status**: PHASES 0–4 REMEDIATED | PHASE 5 PENDING OWNER APPROVAL

---

## 1. Executive Summary

Following the `v1.1.0` packaging refactor, a second adversarial audit proved that several quality gates passed on broken inputs (`F1`, `F2a–F2c`), toolchain configs had drifted, and most notebooks remained boilerplate/simulated stubs (`F3`).

Phases 1–4 remediate all security, validation, CI/CD, and documentation consistency defects while preserving the 105 notebooks byte-identical. Phase 5 (upgrading notebooks to real local-executable Spark/Delta code and aligning README claims with measured verification tiers) awaits explicit owner sign-off.

---

## 2. Ground Truth & Phase Status

| ID | Finding | Status | Remediation Summary |
|---|---|---|---|
| **F1** | **Blind Gitleaks config** | ✅ Fixed (Phase 1) | Enabled `[extend] useDefault = true` in `.gitleaks.toml`, removed blanket directory allowlists, added `tests/security/test_secret_canary.py` + CI canary job, and extended `test_secret_sanitization.py` token scans. |
| **F2a / F2b** | **DABs validator only grepped text** | ✅ Fixed (Phase 2) | Rewrote `src/handbook/validate/bundle.py` to parse YAML, enforce `mode` enums and `${var.*}` declarations, resolve all notebook/DLT/app paths, and validate against committed `src/handbook/data/bundle.schema.json`. Fixed invalid expressions/names in `databricks.yml` & `resources/*.yml`. |
| **F2c** | **README drift unchecked** | ✅ Fixed (Phase 2) | Added `handbook readme --check`, wired into `make check` and CI, enforced curriculum count and whiteboard domain sum checks in `hygiene.py`, and backed all gates with `tests/mutation/test_gates_fail.py`. |
| **F4–F7** | **Version, Dependabot, pre-commit & CI drift** | ✅ Fixed (Phase 3) | Aligned `pyproject.toml` (`1.1.0`) and `CITATION.cff` (`MIT`), switched Dependabot to grouped `uv` + `github-actions`, aligned pre-commit `ruff` hooks with `make lint`, extracted `.github/actions/setup`, and enforced `uv sync --locked`. |
| **F9–F10** | **Duplicate whiteboards, stale CLI refs, root clutter** | ✅ Fixed (Phase 4) | Replaced 331 KB `docs/whiteboard_diagrams/README.md` with redirect stub, updated `README.md` hero links & added Domain 07, updated `explorer.py` (`handbook explore`) & `02_unity_catalog_and_governance`, retired root `requirements.txt`, moved `SECURITY.md` & `CODE_OF_CONDUCT.md` to `.github/`. |
| **F3** | **Simulated notebooks & Spark smoke test** | ⏳ Pending (Phase 5) | Requires owner approval: add `handbook audit-content` & `docs/verification.md`, align public claims, strip unused boilerplate cells, upgrade Batch 1 notebooks (starting with Module 03) to real local Delta/Spark execution, and run T2 notebooks in `nightly-smoke.yml`. |

---

## 3. Preserved Invariants

1. **Byte-Identical Notebooks (Phases 0–4)**: All 105 Databricks source notebooks in `notebooks/` remain 100% byte-identical against baseline SHA-256 hashes until Phase 5 begins.
2. **Databricks Asset Bundle Paths**: `databricks.yml` and `resources/*.yml` resolve and validate cleanly offline and via `databricks bundle schema`.
3. **Whiteboard Blueprints**: All 52 `.webp` blueprints in `assets/whiteboards/` are preserved and referenced across all 7 domain guides.
4. **Mermaid Parsing Compliance**: All Mermaid diagrams pass automated syntax validation (`test_mermaid_diagrams.py`).
