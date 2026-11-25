"""
Local Spark + Delta Lake Execution Runner for The Databricks Handbook.

Executes Databricks source notebook (.py) code cells sequentially against an isolated
local Delta-enabled SparkSession so T2 notebooks are genuinely verified at runtime.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Any

from handbook.audit import collect_audit_records


def create_local_spark(tmp_root: Path) -> Any:
    """Creates a local Delta Lake 3.2 enabled SparkSession isolated inside tmp_root."""
    from delta import configure_spark_with_delta_pip
    from pyspark.sql import SparkSession

    warehouse_dir = (tmp_root / "spark-warehouse").resolve()
    derby_dir = (tmp_root / "derby").resolve()
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    derby_dir.mkdir(parents=True, exist_ok=True)

    builder = (
        SparkSession.builder.master("local[2]")
        .appName("DatabricksHandbookLocalRunner")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.warehouse.dir", str(warehouse_dir))
        .config("spark.ui.enabled", "false")
        .config("spark.driver.extraJavaOptions", f"-Dderby.system.home={derby_dir}")
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def extract_executable_cells(nb_path: Path) -> list[str]:
    """Splits a Databricks source notebook into ordered executable Python code cells."""
    content = nb_path.read_text(encoding="utf-8")
    cells: list[str] = []
    for cmd in content.split("# COMMAND ----------"):
        cmd_s = cmd.strip()
        if not cmd_s or "# MAGIC %md" in cmd_s or cmd_s.startswith("# MAGIC"):
            continue
        code_lines = [
            line
            for line in cmd_s.splitlines()
            if not line.strip().startswith("# MAGIC")
            and not line.strip().startswith("%")
            and not line.strip().startswith("# Databricks notebook source")
        ]
        cleaned = "\n".join(code_lines).strip()
        if cleaned:
            cells.append(cleaned)
    return cells


@contextlib.contextmanager
def _temp_cwd(target_dir: Path):
    prev = Path.cwd()
    os.chdir(target_dir)
    try:
        yield
    finally:
        os.chdir(prev)


def run_notebook_local(nb_path: Path, spark: Any | None = None) -> tuple[bool, str]:
    """
    Executes all Python code cells of nb_path inside an isolated temporary directory.
    Returns (success, error_message).
    """
    cells = extract_executable_cells(nb_path)
    if not cells:
        return False, f"{nb_path.name}: No executable Python code cells found."

    owns_spark = spark is None
    with tempfile.TemporaryDirectory(prefix="handbook_run_") as tmp_str:
        tmp_dir = Path(tmp_str)
        active_spark = spark if spark is not None else create_local_spark(tmp_dir)
        namespace: dict[str, Any] = {
            "spark": active_spark,
            "__name__": "__main__",
            "HANDBOOK_TMP_DIR": str(tmp_dir),
        }
        try:
            with _temp_cwd(tmp_dir):
                for idx, cell_code in enumerate(cells, 1):
                    compiled = compile(cell_code, f"{nb_path.name}:cell_{idx}", "exec")
                    exec(compiled, namespace)  # noqa: S102
            return True, ""
        except Exception as exc:
            return False, f"{nb_path.name} (cell {idx}): {type(exc).__name__}: {exc}"
        finally:
            with contextlib.suppress(Exception):
                for tbl in active_spark.catalog.listTables("default"):
                    if tbl.isTemporary:
                        active_spark.catalog.dropTempView(tbl.name)
                    else:
                        active_spark.sql(f"DROP TABLE IF EXISTS default.`{tbl.name}`")
            if owns_spark:
                with contextlib.suppress(Exception):
                    active_spark.stop()


def resolve_notebook_by_id(base_dir: Path, nb_id: str) -> Path | None:
    """Resolves a 3-digit or unpadded notebook ID to its .py file path."""
    padded = f"{int(nb_id):03d}" if nb_id.isdigit() else nb_id
    matches = sorted((base_dir / "notebooks").glob(f"*/{padded}_*.py"))
    return matches[0] if matches else None


def run_tier_local(
    base_dir: Path, tier: str = "T2", spark: Any | None = None, verbose: bool = True
) -> tuple[bool, list[str]]:
    """Executes all notebooks belonging to the specified verification tier locally."""
    records = [r for r in collect_audit_records(base_dir) if r.declared_tier == tier]
    if not records:
        return False, [f"No notebooks found for tier {tier}"]

    owns_spark = spark is None
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="handbook_tier_") as tmp_str:
        active_spark = spark if spark is not None else create_local_spark(Path(tmp_str))
        try:
            for rec in records:
                ok, err = run_notebook_local(base_dir / rec.rel_path, spark=active_spark)
                if ok:
                    if verbose:
                        print(f"  ✅ [{rec.declared_tier}] {rec.nb_id}: {rec.title}")
                else:
                    if verbose:
                        print(f"  ❌ [{rec.declared_tier}] {rec.nb_id}: {err}")
                    errors.append(err)
        finally:
            if owns_spark:
                with contextlib.suppress(Exception):
                    active_spark.stop()

    return len(errors) == 0, errors
