"""
Notebook Builder Utility
Constructs Databricks native Python source notebook (.py) files
with clean '# Databricks notebook source', '# COMMAND ----------', and '# MAGIC %md' blocks.
Optimized for Databricks Repos / Git Folders, local PySpark, and CI/CD test runners.
"""

import re
from pathlib import Path


def clean_text_spacing(text: str) -> str:
    """Removes trailing whitespace from lines and collapses 3+ newlines to 2."""
    if not text:
        return ""
    cleaned_lines = [line.rstrip() for line in text.strip().splitlines()]
    result = "\n".join(cleaned_lines)
    return re.sub(r"\n{3,}", "\n\n", result)


def format_markdown_cell(content: str) -> str:
    """Formats markdown content into clean Databricks MAGIC %md lines without redundant blank lines."""
    content_clean = clean_text_spacing(content)
    lines = content_clean.split("\n")

    magic_lines = ["# MAGIC %md"]
    prev_blank = False

    for line in lines:
        if line:
            magic_lines.append(f"# MAGIC {line}")
            prev_blank = False
        else:
            if not prev_blank:
                magic_lines.append("# MAGIC")
                prev_blank = True

    while len(magic_lines) > 1 and magic_lines[-1] == "# MAGIC":
        magic_lines.pop()

    return "\n".join(magic_lines)


def clean_code_cell(code: str) -> str:
    """Cleans code strings, removing excessive blank lines and trailing spaces."""
    return clean_text_spacing(code)


def build_notebook(
    nb_id: str,
    title: str,
    module_folder: str = "",
    module_name: str = "",
    difficulty: str = "Intermediate",
    business_scenario: str = "",
    problem_statement: str = "",
    architectural_notes: str = "",
    sections: list[dict[str, str]] | None = None,
    key_takeaways: list[str] | None = None,
    interview_questions: list[str] | None = None,
    **kwargs,
) -> str:
    """
    Assembles a complete Databricks source notebook in .py format.
    Ensures standard header, markdown documentation, executable code cells,
    and cell separator delimiters.
    """
    cells = []

    # Header cell
    cells.append("# Databricks notebook source")

    # Cell 1: Overview & Metadata (%md)
    intro_md = f"""# {nb_id}. {title}
**Module**: {module_name}  
**Mastery Level**: `{difficulty}`  
**Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2

---

### 🏢 Enterprise Business Scenario
{business_scenario}

### 🎯 Engineering Objective
{problem_statement}

### 🏛️ Architectural Context & Under the Hood Mechanics
{architectural_notes}"""
    cells.append(format_markdown_cell(intro_md))

    # Cell 2: Imports & Session Initialization (Python)
    setup_code = """import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# Initialize or obtain active SparkSession with Delta Lake & Unity Catalog support
spark = SparkSession.builder \\
    .appName("DatabricksHandbook") \\
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \\
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \\
    .config("spark.sql.adaptive.enabled", "true") \\
    .getOrCreate()"""
    cells.append(clean_code_cell(setup_code))

    # Implementation Sections
    if sections:
        for idx, sec in enumerate(sections, 1):
            sec_title = sec.get("title", f"Step {idx}")
            sec_desc = sec.get("explanation", "")
            sec_code = sec.get("code", "")

            # Markdown header for section
            sec_md = f"### {sec_title}\n\n{sec_desc}"
            cells.append(format_markdown_cell(sec_md))

            # Code block for section
            if sec_code:
                cells.append(clean_code_cell(sec_code))

    # Verification & Summary Cell
    summary_md = "### 📌 Production Invariants & Key Takeaways\n\n"
    if key_takeaways:
        for item in key_takeaways:
            summary_md += (
                f"- **{item.split(':')[0]}**: {':'.join(item.split(':')[1:]).strip()}\n"
                if ":" in item
                else f"- {item}\n"
            )
    else:
        summary_md += "- Ensure idempotence across scheduled batch and micro-batch writes.\n- Always enforce Unity Catalog 3-level naming conventions.\n- Monitor cost and resource allocation via System Tables.\n"

    if interview_questions:
        summary_md += "\n---\n\n### 🎓 Architect Interview Questions & Defense\n\n"
        for q in interview_questions:
            summary_md += f"1. {q}\n"

    cells.append(format_markdown_cell(summary_md))

    # Join with standard Databricks cell delimiter
    notebook_content = "\n# COMMAND ----------\n\n".join(cells)
    return notebook_content + "\n"


def write_notebook(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
