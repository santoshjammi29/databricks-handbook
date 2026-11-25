"""
Content Verification Tier Auditor for The Databricks Handbook.

Statically inspects every Databricks source notebook in notebooks/ using Python AST
and cross-checks its declared Verification Tier against measurable code signals:
  - T0 (Reference): prose or config templates; no executable runtime assertions.
  - T1 (Simulated): runs locally, but manipulates Python literals/mocks or string checks.
  - T2 (Local-executable): creates real data/tables and executes Spark/Delta locally with
    assertions on computed results.
  - T3 (Workspace-executable): requires a live Databricks workspace (UC, DLT, System Tables, Apps).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from handbook.curriculum import MODULES, TOTAL_NOTEBOOKS

TIER_LABELS: dict[str, str] = {
    "T0": "T0 Reference",
    "T1": "T1 Simulated",
    "T2": "T2 Local-executable",
    "T3": "T3 Workspace-executable",
}

SPARK_EXEC_ATTRS: frozenset[str] = frozenset(
    {
        "createDataFrame",
        "range",
        "sql",
        "read",
        "readStream",
        "table",
    }
)

WORKSPACE_ONLY_MARKERS: tuple[str, ...] = (
    "system.billing.",
    "system.access.",
    "system.compute.",
    "system.storage.",
    "dlt.",
    "cloudFiles",
    "dbutils.",
    "VectorSearchClient",
    "databricks.connect",
)


@dataclass(frozen=True)
class NotebookAuditRecord:
    """Audit result for a single Databricks source notebook."""

    nb_id: str
    title: str
    module_folder: str
    rel_path: str
    declared_tier: str
    inferred_tier: str
    assert_count: int
    computed_assert_count: int
    has_spark_exec: bool
    has_delta_ops: bool
    has_workspace_only: bool


def _extract_code_and_tier(nb_path: Path) -> tuple[str, str, str, str]:
    """Extracts notebook id, title, declared tier, and concatenated Python code cells."""
    content = nb_path.read_text(encoding="utf-8")

    m_title = re.search(r"# MAGIC # (\d+)\.\s*(.+)", content)
    nb_id = m_title.group(1) if m_title else nb_path.name[:3]
    title = m_title.group(2).strip() if m_title else nb_path.stem[4:].replace("_", " ").title()

    m_tier = re.search(r"\*\*Verification Tier\*\*:\s*`(T[0-3])[^`]*`", content)
    declared_tier = m_tier.group(1) if m_tier else "T1"

    code_chunks: list[str] = []
    for cmd in content.split("# COMMAND ----------"):
        cmd_s = cmd.strip()
        if not cmd_s or "# MAGIC %md" in cmd_s or cmd_s.startswith("# MAGIC"):
            continue
        lines = [
            line
            for line in cmd_s.splitlines()
            if not line.strip().startswith("# MAGIC")
            and not line.strip().startswith("%")
            and not line.strip().startswith("# Databricks notebook source")
        ]
        chunk = "\n".join(lines).strip()
        if chunk:
            code_chunks.append(chunk)

    return nb_id, title, declared_tier, "\n\n".join(code_chunks)


def _analyze_python_ast(code: str) -> tuple[int, int, bool, bool, bool]:
    """
    Analyzes Python AST for assertions, Spark execution calls, Delta operations,
    and workspace-only API calls (ignoring triple-quoted string templates).
    """
    if not code.strip():
        return 0, 0, False, False, False

    tree = ast.parse(code)
    assert_count = 0
    computed_assert_count = 0
    has_spark_exec = False
    has_delta_ops = False
    has_workspace_only = False

    # Track names assigned from literal dicts/lists/strings vs Spark/Delta calls
    literal_vars: set[str] = set()
    spark_vars: set[str] = {"spark"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name):
                val = node.value
                if isinstance(val, (ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Set)):
                    literal_vars.add(tgt.id)
                elif _expr_uses_names(val, spark_vars):
                    spark_vars.add(tgt.id)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "spark":
                    if attr in SPARK_EXEC_ATTRS:
                        has_spark_exec = True
                elif attr in {"format", "save", "merge", "toDelta", "history", "restoreToVersion"}:
                    if attr == "format" and node.args and isinstance(node.args[0], ast.Constant):
                        if node.args[0].value == "delta":
                            has_delta_ops = True
                    elif attr in {"merge", "history", "restoreToVersion"}:
                        has_delta_ops = True
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "DeltaTable":
                    has_spark_exec = True
                    has_delta_ops = True
                if isinstance(node.func.value, ast.Name) and node.func.value.id in {
                    "dbutils",
                    "dlt",
                }:
                    has_workspace_only = True
            elif isinstance(node.func, ast.Name) and node.func.id == "assert_df_equality":
                has_spark_exec = True
                computed_assert_count += 1

        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("delta"):
                has_delta_ops = True
            if node.module.startswith(
                ("databricks.sdk", "databricks.connect", "databricks.vector_search")
            ):
                has_workspace_only = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            assert_count += 1
            # Computed assertions reference Spark-derived vars or non-literal expressions.
            used_names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
            if used_names & spark_vars or (has_spark_exec and not (used_names <= literal_vars)):
                computed_assert_count += 1

    # Check if SQL executed via spark.sql(...) targets system.* tables directly
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sql"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "spark"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            sql_txt = node.args[0].value
            if any(
                m in sql_txt
                for m in ("system.billing.", "system.access.", "system.compute.", "system.storage.")
            ):
                has_workspace_only = True
            if "DELTA" in sql_txt.upper() or "delta." in sql_txt:
                has_delta_ops = True

    return assert_count, computed_assert_count, has_spark_exec, has_delta_ops, has_workspace_only


def _expr_uses_names(node: ast.AST, target_names: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in target_names for n in ast.walk(node))


def classify_notebook(nb_path: Path) -> NotebookAuditRecord:
    """Audits a single notebook and infers its verification tier from AST signals."""
    nb_id, title, declared_tier, code = _extract_code_and_tier(nb_path)
    assert_cnt, comp_assert_cnt, has_spark, has_delta, has_ws = _analyze_python_ast(code)

    if assert_cnt == 0 and comp_assert_cnt == 0:
        inferred = "T0"
    elif has_ws:
        inferred = "T3"
    elif has_spark and comp_assert_cnt > 0:
        inferred = "T2"
    else:
        inferred = "T1"

    return NotebookAuditRecord(
        nb_id=nb_id,
        title=title,
        module_folder=nb_path.parent.name,
        rel_path=f"notebooks/{nb_path.parent.name}/{nb_path.name}",
        declared_tier=declared_tier,
        inferred_tier=inferred,
        assert_count=assert_cnt,
        computed_assert_count=comp_assert_cnt,
        has_spark_exec=has_spark,
        has_delta_ops=has_delta,
        has_workspace_only=has_ws,
    )


def collect_audit_records(base_dir: Path) -> list[NotebookAuditRecord]:
    """Collects sorted audit records for all notebooks under base_dir/notebooks."""
    nb_files = sorted((base_dir / "notebooks").glob("*/*.py"))
    return [classify_notebook(p) for p in nb_files]


def generate_verification_doc(base_dir: Path, records: list[NotebookAuditRecord]) -> str:
    """Builds the deterministic docs/verification.md report."""
    counts = {tier: 0 for tier in TIER_LABELS}
    for rec in records:
        counts[rec.declared_tier] = counts.get(rec.declared_tier, 0) + 1

    total = len(records) or TOTAL_NOTEBOOKS
    lines: list[str] = [
        "# 🔍 Notebook Verification & Execution Tier Matrix",
        "",
        "> **Generated by**: `uv run handbook audit-content` (verified in CI via `--check`)  ",
        f"> **Total Audited Notebooks**: `{total}` across `{len(MODULES)}` modules",
        "",
        "---",
        "",
        "## 1. Tier Summary",
        "",
        "| Tier | Meaning | Count | Share | Verification Method |",
        "|:---:|:---|---:|---:|:---|",
    ]

    descriptions = {
        "T0": (
            "Reference / Config Templates",
            "Format & Python AST syntax check (`handbook validate --target notebooks`)",
        ),
        "T1": (
            "Simulated (Python Literals / String Checks)",
            "Format, AST syntax, and Python script execution of literal assertions",
        ),
        "T2": (
            "Local-Executable (PySpark + Delta Lake)",
            "Executed cell-by-cell against local Spark 3.5 + Delta 3.2 (`uv run pytest -m spark`)",
        ),
        "T3": (
            "Workspace-Executable (Databricks Cloud)",
            "Requires live Unity Catalog / DLT / System Tables / Vector Search workspace",
        ),
    }
    for tier in ("T2", "T3", "T1", "T0"):
        meaning, method = descriptions[tier]
        cnt = counts.get(tier, 0)
        pct = (cnt / total * 100.0) if total else 0.0
        lines.append(f"| **`{tier}`** | {meaning} | {cnt} | {pct:.1f}% | {method} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Static Classification Heuristic & Known Limits",
            "",
            "`handbook audit-content` parses each notebook's Python code cells with "
            "`ast.parse()` (ignoring `# MAGIC %md` cells and string literals) and evaluates:",
            "- **Spark/Delta Execution**: Calls to `spark.createDataFrame`, `spark.range`, "
            "`spark.read`, `spark.readStream`, `spark.sql`, `DeltaTable`, or "
            "`chispa.assert_df_equality`.",
            "- **Computed Assertions**: `assert` (or `assert_df_equality`) statements "
            "referencing Spark-derived variables rather than pure Python dictionary/string "
            "literals.",
            "- **Workspace-Only APIs**: Calls to `dlt`, `dbutils`, `VectorSearchClient`, "
            "`databricks.connect`, or unmocked `system.*` tables.",
            "",
            "**Known Heuristic Limits**:",
            "1. Static AST analysis cannot prove semantic data correctness or catch runtime "
            "SQL/Spark errors — only executing `uv run handbook run-local --tier T2` "
            "(or `uv run pytest -m spark`) proves `T2` notebooks pass end-to-end.",
            "2. Local Spark (`delta-spark 3.2`) runs without Unity Catalog, Photon C++, or "
            "Serverless SQL Warehouses, so `T3` features (Unity Catalog ACLs, "
            "`system.billing.usage`, DLT managed runtime) require a live Databricks workspace "
            "(`T3` currently stands at 0 workspace-verified runs without attached CI workspace "
            "secrets).",
            "",
            "---",
            "",
            "## 3. Per-Notebook Verification Catalog",
            "",
            "| ID | Notebook | Declared Tier | AST Signal | Asserts (Computed) | Spark / Delta |",
            "|:---:|:---|:---:|:---:|:---:|:---:|",
        ]
    )

    for rec in records:
        spark_badge = (
            "Spark+Delta"
            if rec.has_delta_ops
            else ("Spark" if rec.has_spark_exec else "Python/Text")
        )
        lines.append(
            f"| **{rec.nb_id}** | [{rec.title}](../{rec.rel_path}) | "
            f"`{rec.declared_tier}` | `{rec.inferred_tier}` | "
            f"{rec.assert_count} ({rec.computed_assert_count}) | {spark_badge} |"
        )

    return "\n".join(lines) + "\n"


def audit_content(
    base_dir: Path | None = None,
    write: bool = True,
    check: bool = False,
) -> tuple[bool, dict[str, int], list[str]]:
    """
    Audits all notebooks, enforces consistency between declared tier and static AST signals,
    and writes or drift-checks docs/verification.md.
    Returns (ok, tier_counts, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    records = collect_audit_records(base_dir)
    errors: list[str] = []

    if len(records) != TOTAL_NOTEBOOKS:
        errors.append(f"Expected {TOTAL_NOTEBOOKS} notebooks for audit, found {len(records)}")

    for rec in records:
        if rec.declared_tier == "T2" and rec.inferred_tier != "T2":
            errors.append(
                f"{rec.nb_id}: declared T2 Local-executable but AST inferred {rec.inferred_tier} "
                f"(spark={rec.has_spark_exec}, computed_asserts={rec.computed_assert_count}, "
                f"workspace_only={rec.has_workspace_only})"
            )
        elif rec.declared_tier == "T0" and rec.assert_count > 0:
            errors.append(
                f"{rec.nb_id}: declared T0 Reference but contains {rec.assert_count} assert(s)"
            )

    counts = {tier: 0 for tier in TIER_LABELS}
    for rec in records:
        counts[rec.declared_tier] = counts.get(rec.declared_tier, 0) + 1

    doc_content = generate_verification_doc(base_dir, records)
    doc_path = base_dir / "docs" / "verification.md"

    if check:
        if not doc_path.exists():
            errors.append(f"Missing generated verification report at {doc_path}")
        elif doc_path.read_text(encoding="utf-8") != doc_content:
            errors.append(
                "docs/verification.md is out of sync with notebooks! "
                "Run 'uv run handbook audit-content'."
            )
    elif write:
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(doc_content, encoding="utf-8")

    return len(errors) == 0, counts, errors
