"""
Spark Runtime Smoke & Execution Suite.

Executes every notebook classified as `T2 Local-executable` cell-by-cell against
an isolated Apache Spark 3.5 + Delta Lake 3.2 runtime. Skipped automatically when
optional Spark dependencies are absent (e.g., lightweight dev-only CI matrix).
"""

from pathlib import Path

import pytest

from handbook.audit import collect_audit_records
from handbook.runner import create_local_spark, run_notebook_local

BASE_DIR = Path(__file__).resolve().parent.parent.parent
T2_NOTEBOOK_PATHS: list[str] = [
    r.rel_path for r in collect_audit_records(BASE_DIR) if r.declared_tier == "T2"
]


@pytest.fixture(scope="module")
def spark_session(tmp_path_factory: pytest.TempPathFactory):
    """Module-scoped local Delta-enabled SparkSession; skips if pyspark extra is absent."""
    pytest.importorskip("pyspark")
    pytest.importorskip("delta")
    tmp_root = tmp_path_factory.mktemp("spark_smoke")
    spark = create_local_spark(tmp_root)
    try:
        yield spark
    finally:
        spark.stop()


@pytest.mark.spark
@pytest.mark.parametrize("nb_rel_path", T2_NOTEBOOK_PATHS)
def test_t2_notebook_executes_cleanly(base_dir: Path, spark_session, nb_rel_path: str):
    """Proves every T2 notebook runs end-to-end against local Spark + Delta without failure."""
    nb_path = base_dir / nb_rel_path
    assert nb_path.exists(), f"Missing notebook at {nb_path}"
    ok, err = run_notebook_local(nb_path, spark=spark_session)
    assert ok, f"Notebook {nb_rel_path} failed under local Spark: {err}"


@pytest.mark.spark
def test_smoke_runner_fails_on_violated_spark_assertion(spark_session, tmp_path: Path):
    """Negative gate: run_notebook_local must fail loudly when a Spark assertion breaks."""
    broken_nb = tmp_path / "998_broken_spark.py"
    broken_nb.write_text(
        "# Databricks notebook source\n"
        "# COMMAND ----------\n"
        "df = spark.range(0, 5)\n"
        "assert df.count() == 999\n",
        encoding="utf-8",
    )
    ok, err = run_notebook_local(broken_nb, spark=spark_session)
    assert not ok
    assert "AssertionError" in err
