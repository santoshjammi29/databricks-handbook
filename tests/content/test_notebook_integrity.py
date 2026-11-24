"""
Test Suite: Databricks Python Notebook Integrity & Standards Verification.
"""

import ast

from handbook.curriculum import EXPECTED_MODULE_FOLDERS, TOTAL_NOTEBOOKS


def test_notebook_count(base_dir):
    nb_files = list((base_dir / "notebooks").glob("*/*.py"))
    assert len(nb_files) == TOTAL_NOTEBOOKS, (
        f"Expected exactly {TOTAL_NOTEBOOKS} .py notebooks, found {len(nb_files)}"
    )


def test_all_modules_present(base_dir):
    for mod in EXPECTED_MODULE_FOLDERS:
        mod_path = base_dir / "notebooks" / mod
        assert mod_path.exists() and mod_path.is_dir(), f"Missing module directory: {mod}"
        nb_in_mod = list(mod_path.glob("*.py"))
        assert len(nb_in_mod) > 0, f"Module {mod} contains zero notebooks!"


def test_notebook_databricks_format(base_dir):
    nb_files = list((base_dir / "notebooks").glob("*/*.py"))
    for nb in nb_files:
        content = nb.read_text(encoding="utf-8")
        assert content.startswith("# Databricks notebook source"), (
            f"{nb.name}: Missing Databricks source header"
        )
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
            if (
                not cmd_stripped
                or cmd_stripped.startswith("# MAGIC %md")
                or "# MAGIC %md" in cmd_stripped
            ):
                continue
            code_lines = [
                line
                for line in cmd_stripped.splitlines()
                if not line.strip().startswith("# MAGIC") and not line.strip().startswith("%")
            ]
            code_clean = "\n".join(code_lines).strip()
            if code_clean:
                try:
                    ast.parse(code_clean)
                except SyntaxError as se:
                    syntax_errors.append(f"{nb.name} (cell {idx}, line {se.lineno}): {se.msg}")

    assert not syntax_errors, (
        f"Detected {len(syntax_errors)} Python AST syntax errors:\n" + "\n".join(syntax_errors)
    )


def test_notebook_triad_and_asserts(base_dir):
    """Asserts that every notebook conforms to the Code-Test-Doc Triad standards."""
    nb_files = sorted(list((base_dir / "notebooks").glob("*/*.py")))
    missing_scenario = []
    missing_objective = []
    missing_arch = []
    missing_assert = []

    # Two architectural/incident forensic overview notebooks are declarative documentation patterns
    exempt_from_assert = {
        "033_auto_loader_cloudfiles_directory_listing_vs_file_notifications.py",
        "099_production_incident_01_driver_and_executor_oom_forensic_triage.py",
    }

    for nb in nb_files:
        content = nb.read_text(encoding="utf-8")
        if "Enterprise Business Scenario" not in content:
            missing_scenario.append(nb.name)
        if "Engineering Objective" not in content:
            missing_objective.append(nb.name)
        if "Architectural Context" not in content:
            missing_arch.append(nb.name)
        if "assert " not in content and nb.name not in exempt_from_assert:
            missing_assert.append(nb.name)

    assert not missing_scenario, f"Missing Enterprise Business Scenario: {missing_scenario}"
    assert not missing_objective, f"Missing Engineering Objective: {missing_objective}"
    assert not missing_arch, f"Missing Architectural Context: {missing_arch}"
    assert not missing_assert, f"Missing automated assertions in code: {missing_assert}"
