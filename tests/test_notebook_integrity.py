"""
Test Suite: Databricks Python Notebook Integrity & Standards Verification
"""

import ast
from pathlib import Path

def test_notebook_count(base_dir):
    nb_files = list((base_dir / "notebooks").glob("*/*.py"))
    assert len(nb_files) == 105, f"Expected exactly 105 .py notebooks, found {len(nb_files)}"

def test_all_ten_modules_present(base_dir):
    expected_modules = [
        "01_platform_architecture_and_security",
        "02_unity_catalog_and_governance",
        "03_delta_lake_storage_engine",
        "04_lakeflow_ingestion_and_dlt",
        "05_lakeflow_jobs_and_orchestration",
        "06_databricks_sql_and_photon",
        "07_enterprise_devops_and_dabs",
        "08_databricks_apps_and_mosaic_ai",
        "09_finops_and_system_tables",
        "10_production_incidents_and_blueprints"
    ]
    for mod in expected_modules:
        mod_path = base_dir / "notebooks" / mod
        assert mod_path.exists() and mod_path.is_dir(), f"Missing module directory: {mod}"
        nb_in_mod = list(mod_path.glob("*.py"))
        assert len(nb_in_mod) > 0, f"Module {mod} contains zero notebooks!"

def test_notebook_databricks_format(base_dir):
    nb_files = list((base_dir / "notebooks").glob("*/*.py"))
    for nb in nb_files:
        content = nb.read_text(encoding="utf-8")
        assert content.startswith("# Databricks notebook source"), f"{nb.name}: Missing Databricks source header"
        assert "# COMMAND ----------" in content, f"{nb.name}: Missing cell delimiter"
        assert "# MAGIC %md" in content, f"{nb.name}: Missing markdown documentation cells"

def test_notebook_python_ast_syntax(base_dir):
    nb_files = sorted(list((base_dir / "notebooks").glob("*/*.py")))
    syntax_errors = []
    for nb in nb_files:
        content = nb.read_text(encoding="utf-8")
        commands = content.split("# COMMAND ----------")
        for idx, cmd in enumerate(commands):
            cmd_stripped = cmd.strip()
            if not cmd_stripped or cmd_stripped.startswith("# MAGIC %md") or "# MAGIC %md" in cmd_stripped:
                continue
            code_lines = [
                line for line in cmd_stripped.splitlines()
                if not line.strip().startswith("# MAGIC") and not line.strip().startswith("%")
            ]
            code_clean = "\n".join(code_lines).strip()
            if code_clean:
                try:
                    ast.parse(code_clean)
                except SyntaxError as se:
                    syntax_errors.append(f"{nb.name} (cell {idx}): {se}")
    assert not syntax_errors, f"Python SyntaxErrors detected in notebooks:\n" + "\n".join(syntax_errors)
