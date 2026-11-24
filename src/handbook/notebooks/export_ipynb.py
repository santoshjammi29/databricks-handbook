"""
Export to Jupyter Notebook (.ipynb) Utility
Converts Databricks native Python source notebooks (.py) to standard Jupyter Notebooks (.ipynb).
"""

import json
from pathlib import Path


def convert_databricks_py_to_ipynb(py_path: Path, out_path: Path):
    content = py_path.read_text(encoding="utf-8")
    commands = content.split("# COMMAND ----------")

    cells = []
    for cmd in commands:
        cmd_stripped = cmd.strip()
        if not cmd_stripped:
            continue

        if cmd_stripped.startswith("# MAGIC %md") or "# MAGIC %md" in cmd_stripped:
            lines = []
            for line in cmd_stripped.splitlines():
                if line.startswith("# MAGIC %md"):
                    continue
                elif line.startswith("# MAGIC "):
                    lines.append(line[8:])
                elif line.startswith("# MAGIC"):
                    lines.append(line[7:])
                elif not line.startswith("# Databricks notebook source"):
                    lines.append(line)
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [src_line + "\n" for src_line in lines],
                }
            )
        else:
            lines = []
            for line in cmd_stripped.splitlines():
                if not line.startswith("# Databricks notebook source"):
                    lines.append(line)
            cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [src_line + "\n" for src_line in lines],
                }
            )

    nb_json = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(nb_json, indent=2), encoding="utf-8")


def export_all(base_dir: Path | None = None):
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
    py_files = sorted(list((base_dir / "notebooks").glob("*/*.py")))
    out_dir = base_dir / "ipynb_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting {len(py_files)} notebooks to Jupyter format at {out_dir}...")
    for py_file in py_files:
        rel = py_file.relative_to(base_dir / "notebooks")
        target_ipynb = out_dir / rel.with_suffix(".ipynb")
        convert_databricks_py_to_ipynb(py_file, target_ipynb)
    print(f"✅ Successfully exported {len(py_files)} notebooks to .ipynb format.")


if __name__ == "__main__":
    export_all()
