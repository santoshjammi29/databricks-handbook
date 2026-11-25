"""
Unit tests for handbook.audit and handbook.runner.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from handbook.audit import audit_content, classify_notebook
from handbook.cli import main as cli_main
from handbook.runner import (
    extract_executable_cells,
    resolve_notebook_by_id,
    run_notebook_local,
    run_tier_local,
)


def test_audit_content_matches_committed_verification_doc(base_dir: Path):
    ok, counts, errors = audit_content(base_dir=base_dir, write=False, check=True)
    assert ok, f"Audit mismatch: {errors}"
    assert sum(counts.values()) == 105
    assert counts["T2"] >= 40


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


def test_audit_detects_workspace_markers_and_t0_violation(tmp_path: Path):
    nb_ws = tmp_path / "997_cloud.py"
    nb_ws.write_text(
        "# Databricks notebook source\n"
        "# COMMAND ----------\n"
        "# MAGIC %md\n"
        "# MAGIC # 997. Cloud\n"
        "# MAGIC **Verification Tier**: `T3 Workspace-executable`\n"
        "# COMMAND ----------\n"
        "df = spark.readStream.format('cloudFiles').load('/Volumes/raw')\n"
        "assert df is not None\n",
        encoding="utf-8",
    )
    rec_ws = classify_notebook(nb_ws)
    assert rec_ws.has_workspace_only is True
    assert rec_ws.inferred_tier == "T3"

    nb_t0 = tmp_path / "996_ref.py"
    nb_t0.write_text(
        "# Databricks notebook source\n"
        "# COMMAND ----------\n"
        "# MAGIC %md\n"
        "# MAGIC # 996. Ref\n"
        "# MAGIC **Verification Tier**: `T0 Reference`\n"
        "# COMMAND ----------\n"
        "x = 1\n"
        "assert x == 1\n",
        encoding="utf-8",
    )
    rec_t0 = classify_notebook(nb_t0)
    assert rec_t0.inferred_tier == "T1"


def test_audit_t0_mismatch_and_missing_doc(
    base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import shutil

    shutil.copytree(base_dir / "notebooks", tmp_path / "notebooks")
    (tmp_path / "docs").mkdir()
    ok, _, errors = audit_content(base_dir=tmp_path, write=False, check=True)
    assert not ok
    assert any("Missing generated verification report" in e for e in errors)

    t0_nb = (
        tmp_path
        / "notebooks"
        / "04_lakeflow_ingestion_and_dlt"
        / "033_auto_loader_cloudfiles_directory_listing_vs_file_notifications.py"
    )
    t0_nb.write_text(
        t0_nb.read_text(encoding="utf-8") + "\n# COMMAND ----------\n\nassert True\n",
        encoding="utf-8",
    )
    ok_bad, _, errs_bad = audit_content(base_dir=tmp_path, write=False, check=True)
    assert not ok_bad
    assert any("declared T0 Reference but contains" in e for e in errs_bad)


class _DummyCatalog:
    def __init__(self):
        self.dropped_views: list[str] = []

    def listTables(self, _db: str):
        return [
            SimpleNamespace(name="tmp_v", isTemporary=True),
            SimpleNamespace(name="perm_t", isTemporary=False),
        ]

    def dropTempView(self, name: str):
        self.dropped_views.append(name)


class _DummySpark:
    def __init__(self):
        self.catalog = _DummyCatalog()
        self.sql_log: list[str] = []

    def sql(self, query: str):
        self.sql_log.append(query)

    def stop(self):
        pass


def test_runner_helpers_extract_cells_and_resolve_id(base_dir: Path):
    nb_path = resolve_notebook_by_id(base_dir, "10")
    assert nb_path is not None
    assert nb_path.name.startswith("010_")

    cells = extract_executable_cells(nb_path)
    assert len(cells) >= 1
    assert any("createDataFrame" in c for c in cells)

    assert resolve_notebook_by_id(base_dir, "999") is None
    assert cli_main(["audit-content", "--check"]) == 0


def test_run_notebook_local_and_tier_with_mock_spark(
    base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    good_nb = tmp_path / "901_good.py"
    good_nb.write_text(
        "# Databricks notebook source\n# COMMAND ----------\nval = 21 * 2\nassert val == 42\n",
        encoding="utf-8",
    )
    dummy = _DummySpark()
    ok, err = run_notebook_local(good_nb, spark=dummy)
    assert ok and err == ""
    assert dummy.catalog.dropped_views == ["tmp_v"]
    assert any("DROP TABLE IF EXISTS default.`perm_t`" in q for q in dummy.sql_log)

    empty_nb = tmp_path / "902_empty.py"
    empty_nb.write_text(
        "# Databricks notebook source\n# MAGIC %md\n# MAGIC # Title\n", encoding="utf-8"
    )
    ok_empty, err_empty = run_notebook_local(empty_nb, spark=dummy)
    assert not ok_empty and "No executable" in err_empty

    bad_nb = tmp_path / "903_fail.py"
    bad_nb.write_text(
        "# Databricks notebook source\n# COMMAND ----------\nassert 1 == 2\n", encoding="utf-8"
    )
    ok_bad, err_bad = run_notebook_local(bad_nb, spark=dummy)
    assert not ok_bad and "AssertionError" in err_bad

    # Test run_tier_local with mocked collect + runner execution paths
    ok_none, errs_none = run_tier_local(tmp_path, tier="T2", spark=dummy, verbose=False)
    assert not ok_none and errs_none

    monkeypatch.setattr("handbook.runner.create_local_spark", lambda _p: dummy)
    monkeypatch.setattr(
        "handbook.runner.collect_audit_records",
        lambda _b: [
            SimpleNamespace(nb_id="901", title="Good", declared_tier="T2", rel_path=good_nb.name),
            SimpleNamespace(nb_id="903", title="Fail", declared_tier="T2", rel_path=bad_nb.name),
        ],
    )
    ok_tier, errs_tier = run_tier_local(tmp_path, tier="T2", spark=None, verbose=True)
    assert not ok_tier and len(errs_tier) == 1

    # CLI run-local argument validation & mocked dispatch
    assert cli_main(["run-local"]) == 1
    assert cli_main(["run-local", "999"]) == 1
    monkeypatch.setattr("handbook.runner.run_notebook_local", lambda _p: (True, ""))
    assert cli_main(["run-local", "010"]) == 0
    monkeypatch.setattr("handbook.runner.run_notebook_local", lambda _p: (False, "boom"))
    assert cli_main(["run-local", "010"]) == 1
    monkeypatch.setattr("handbook.runner.run_tier_local", lambda **_kw: (True, []))
    assert cli_main(["run-local", "--tier", "T2"]) == 0
    monkeypatch.setattr("handbook.runner.run_tier_local", lambda **_kw: (False, ["err"]))
    assert cli_main(["run-local", "--tier", "T2"]) == 1
