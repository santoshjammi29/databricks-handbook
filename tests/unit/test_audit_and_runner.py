"""
Unit tests for handbook.audit and handbook.runner.
"""

from pathlib import Path

from handbook.audit import audit_content, classify_notebook
from handbook.cli import main as cli_main
from handbook.runner import extract_executable_cells, resolve_notebook_by_id


def test_audit_content_matches_committed_verification_doc(base_dir: Path):
    ok, counts, errors = audit_content(base_dir=base_dir, write=False, check=True)
    assert ok, f"Audit mismatch: {errors}"
    assert sum(counts.values()) == 105
    assert counts["T2"] >= 5


def test_audit_detects_mislabeled_t2_notebook(tmp_path: Path):
    nb = tmp_path / "999_fake.py"
    nb.write_text(
        "# Databricks notebook source\n"
        "# COMMAND ----------\n"
        "# MAGIC %md\n"
        "# MAGIC # 999. Fake\n"
        "# MAGIC **Verification Tier**: `T2 Local-executable`\n"
        "# COMMAND ----------\n"
        "x = {'a': 1}\n"
        "assert x['a'] == 1\n",
        encoding="utf-8",
    )
    rec = classify_notebook(nb)
    assert rec.declared_tier == "T2"
    assert rec.inferred_tier == "T1"


def test_runner_helpers_extract_cells_and_resolve_id(base_dir: Path):
    nb_path = resolve_notebook_by_id(base_dir, "10")
    assert nb_path is not None
    assert nb_path.name.startswith("010_")

    cells = extract_executable_cells(nb_path)
    assert len(cells) >= 1
    assert any("createDataFrame" in c for c in cells)

    assert resolve_notebook_by_id(base_dir, "999") is None
    assert cli_main(["audit-content", "--check"]) == 0
