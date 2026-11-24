"""
Databricks Notebook Validator & Python Syntax Integrity Verifier.
Verifies that all notebooks conform to Databricks source notebook formatting
and that all Python code cells parse cleanly via Python AST without syntax errors.
"""

import ast
import sys
from pathlib import Path

from handbook.curriculum import TOTAL_NOTEBOOKS


def validate_notebooks(
    base_dir: Path | None = None, verbose: bool = True
) -> tuple[bool, list[str]]:
    """
    Validates all notebooks in base_dir/notebooks against Databricks formatting and AST syntax.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    nb_files = sorted(list((base_dir / "notebooks").glob("*/*.py")))

    if verbose:
        print(f"Validating {len(nb_files)} Databricks notebooks at {base_dir / 'notebooks'}...")

    errors: list[str] = []

    if len(nb_files) != TOTAL_NOTEBOOKS:
        errors.append(f"Expected exactly {TOTAL_NOTEBOOKS} notebooks, found {len(nb_files)}")
        return False, errors

    format_errors: list[str] = []
    syntax_errors: list[str] = []

    for nb in nb_files:
        content = nb.read_text(encoding="utf-8")

        # Verify Databricks source headers and delimiters
        if not content.startswith("# Databricks notebook source"):
            format_errors.append(f"{nb.name}: Missing '# Databricks notebook source' header")
        if "# COMMAND ----------" not in content:
            format_errors.append(f"{nb.name}: Missing '# COMMAND ----------' cell separator")
        if "# MAGIC %md" not in content:
            format_errors.append(f"{nb.name}: Missing '# MAGIC %md' documentation cell")

        # Parse Python code cells via AST
        commands = content.split("# COMMAND ----------")
        for idx, cmd in enumerate(commands):
            cmd_stripped = cmd.strip()
            if (
                not cmd_stripped
                or "# MAGIC %md" in cmd_stripped
                or cmd_stripped.startswith("# MAGIC")
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

    errors = format_errors + syntax_errors

    if verbose:
        if format_errors:
            print("\n--- FORMAT ERRORS DETECTED ---")
            for err in format_errors:
                print(f"  ❌ {err}")

        if syntax_errors:
            print("\n--- PYTHON AST SYNTAX ERRORS DETECTED ---")
            for err in syntax_errors:
                print(f"  ❌ {err}")

        if not errors:
            print(
                f"\n✅ All {len(nb_files)} Databricks notebooks verified successfully: "
                "100% format & Python AST syntax compliance!"
            )

    return len(errors) == 0, errors


def validate():
    success, _ = validate_notebooks()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    validate()
