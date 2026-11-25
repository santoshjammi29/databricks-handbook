#!/usr/bin/env python3
"""
Generates the Curriculum Matrix and Track Overview for The Databricks Handbook README.md.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_EN_DASH = "\u2013"

MODULE_CONFIG = {
    "01_platform_architecture_and_security": {
        "icon": "🛡️",
        "title": "01. Platform Architecture & Security",
        "anchor": "module-01-platform-architecture-and-security",
        "range": f"001 {_EN_DASH} 010",
        "level": "🟢<br>Foundational",
        "desc": (
            "Split-plane security, VNet injection, cluster types & policies, "
            "CLI v0.200+, REST API 2.1, secrets, volumes"
        ),
    },
    "02_unity_catalog_and_governance": {
        "icon": "🏛️",
        "title": "02. Unity Catalog & Governance",
        "anchor": "module-02-unity-catalog-and-governance",
        "range": f"011 {_EN_DASH} 021",
        "level": "🟡<br>Intermediate",
        "desc": (
            "3-level namespace, Managed vs External, Volumes, Dynamic RLS, "
            "Column Masking, Federation, Delta Sharing, ABAC"
        ),
    },
    "03_delta_lake_storage_engine": {
        "icon": "⚡",
        "title": "03. Delta Lake 3.x Storage Engine",
        "anchor": "module-03-delta-lake-storage-engine",
        "range": f"022 {_EN_DASH} 032",
        "level": "🟡<br>Intermediate",
        "desc": (
            "Transaction log internals, Deletion Vectors (MoR), Liquid Clustering, "
            "CDF, Predictive Optimization, UniForm, Clones"
        ),
    },
    "04_lakeflow_ingestion_and_dlt": {
        "icon": "🌊",
        "title": "04. Lakeflow Ingestion & DLT",
        "anchor": "module-04-lakeflow-ingestion-and-dlt",
        "range": f"033 {_EN_DASH} 043",
        "level": "🔴<br>Advanced",
        "desc": (
            "Auto Loader (cloudFiles), schema drift, _rescued_data, DLT expectations, "
            "DLQ quarantine, CDC apply_changes"
        ),
    },
    "05_lakeflow_jobs_and_orchestration": {
        "icon": "⚙️",
        "title": "05. Lakeflow Jobs & Orchestration",
        "anchor": "module-05-lakeflow-jobs-and-orchestration",
        "range": f"044 {_EN_DASH} 054",
        "level": "🟡<br>Intermediate",
        "desc": (
            "Multi-task DAGs, taskValues context sharing, Service Principals, "
            "triggers, exponential retries, repair & rerun"
        ),
    },
    "06_databricks_sql_and_photon": {
        "icon": "🚀",
        "title": "06. Databricks SQL & Photon Engine",
        "anchor": "module-06-databricks-sql-and-photon",
        "range": f"055 {_EN_DASH} 065",
        "level": "🔴<br>Advanced",
        "desc": (
            "Serverless SQL Warehouses, Photon C++ SIMD, IWM admission, multi-tier caching, "
            "Query Profile, AI/BI dashboards, Genie"
        ),
    },
    "07_enterprise_devops_and_dabs": {
        "icon": "📦",
        "title": "07. Enterprise DevOps & DABs",
        "anchor": "module-07-enterprise-devops-and-dabs",
        "range": f"066 {_EN_DASH} 076",
        "level": "🔴<br>Advanced",
        "desc": (
            "Databricks Asset Bundles (databricks.yml), dev/staging/prod targets, "
            "GitHub Actions OIDC, Terraform, DB Connect v2"
        ),
    },
    "08_databricks_apps_and_mosaic_ai": {
        "icon": "🤖",
        "title": "08. Databricks Apps & Mosaic AI",
        "anchor": "module-08-databricks-apps-and-mosaic-ai",
        "range": f"077 {_EN_DASH} 087",
        "level": "🟣<br>Expert",
        "desc": (
            "Databricks Apps (Streamlit/FastAPI), Vector Search Delta Sync, "
            "Foundation Model APIs, MLflow in UC, Enterprise RAG"
        ),
    },
    "09_finops_and_system_tables": {
        "icon": "💰",
        "title": "09. FinOps & System Tables",
        "anchor": "module-09-finops-and-system-tables",
        "range": f"088 {_EN_DASH} 098",
        "level": "🟡<br>Intermediate",
        "desc": (
            "system.billing.usage, cluster tagging attribution, audit forensics, "
            "zombie detection, 3-sigma cost anomalies, ARM VMs"
        ),
    },
    "10_production_incidents_and_blueprints": {
        "icon": "🚨",
        "title": "10. Incident Triage & Architecture Blueprints",
        "anchor": "module-10-production-incidents-and-blueprints",
        "range": f"099 {_EN_DASH} 105",
        "level": "🟣<br>Principal",
        "desc": (
            "Driver/Executor OOM triage, OCC conflict resolution, 99% straggler salting, "
            "RocksDB state leaks, master blueprint"
        ),
    },
}


def clean_for_table(text: str) -> str:
    if not text:
        return ""
    t = text.replace("|", "&#124;").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", t)


def make_wrappable(filename: str) -> str:
    """
    Inserts zero-width spaces (&#8203;) after underscores and before .py
    allowing long filenames to wrap naturally inside table cells without stretching layout.
    """
    w = filename.replace("_", "_&#8203;")
    if w.endswith(".py"):
        w = w[:-3] + "&#8203;.py"
    return w


def extract_notebook_meta(nb_path: Path) -> dict[str, str]:
    content = nb_path.read_text(encoding="utf-8")

    # Extract ID and Title from Markdown header (# 001. ...)
    m_title = re.search(r"# MAGIC # (\d+)\.\s*(.+)", content)
    if m_title:
        nb_id = m_title.group(1)
        title = m_title.group(2).strip()
    else:
        nb_id = nb_path.name[:3]
        title = nb_path.stem[4:].replace("_", " ").title()

    # Extract Level and Verification Tier
    m_level = re.search(r"# MAGIC \*\*Mastery Level\*\*:\s*`([^`]+)`", content)
    level = m_level.group(1).strip() if m_level else "Intermediate"

    m_tier = re.search(r"\*\*Verification Tier\*\*:\s*`(T[0-3])[^`]*`", content)
    tier = m_tier.group(1).strip() if m_tier else "T1"

    # Extract Objective
    m_obj = re.search(r"# MAGIC ### 🎯 Engineering Objective\s*# MAGIC (.+)", content)
    objective = m_obj.group(1).strip() if m_obj else ""
    if not objective:
        m_obj2 = re.search(r"# MAGIC ### 🏢 Enterprise Business Scenario\s*# MAGIC (.+)", content)
        objective = m_obj2.group(1).strip() if m_obj2 else ""

    return {
        "id": nb_id,
        "title": title,
        "level": level,
        "tier": tier,
        "objective": clean_for_table(objective),
        "filename": nb_path.name,
        "rel_path": f"notebooks/{nb_path.parent.name}/{nb_path.name}",
    }


def generate_markdown(path_prefix: str = "") -> str:
    lines = [
        '<a id="curriculum-overview"></a>',
        "## 🗺️ Curriculum Overview & Track Architecture\n",
        "| Track | Module Name | Recipe Range | Level | Domain Focus & Key Capabilities |",
        "| :---: | :--- | :---: | :---: | :--- |",
    ]

    for _mod_dir, cfg in MODULE_CONFIG.items():
        track_num = cfg["title"].split(".")[0]
        name_clean = cfg["title"].split(".")[1].strip()
        lines.append(
            f"| **{track_num}** | **[{cfg['icon']} {name_clean}](#{cfg['anchor']})** "
            f"| `{cfg['range']}` | {cfg['level']} | {cfg['desc']} |"
        )

    lines.append("\n---\n")

    for mod_dir, cfg in MODULE_CONFIG.items():
        dir_path = NOTEBOOKS_DIR / mod_dir
        if not dir_path.exists():
            continue

        nb_files = sorted(dir_path.glob("*.py"))
        lines.append(
            f'\n### {cfg["icon"]} <a id="{cfg["anchor"]}"></a>{cfg["title"]} (`{cfg["range"]}`)\n'
        )
        lines.append(f"> **Focus**: {cfg['desc']}\n")
        lines.append(
            "| # | Databricks Notebook Recipe | Level | Tier | "
            "Core Engineering Objective & Production Invariant | Source File (.py) |"
        )
        lines.append("| :---: | :--- | :---: | :---: | :--- | :--- |")

        for nb in nb_files:
            meta = extract_notebook_meta(nb)
            lvl_icon = (
                "🟢"
                if "Foundational" in meta["level"] or "Beginner" in meta["level"]
                else (
                    "🟡"
                    if "Intermediate" in meta["level"]
                    else ("🔴" if "Advanced" in meta["level"] else "🟣")
                )
            )
            wrappable_name = make_wrappable(meta["filename"])
            link_path = f"{path_prefix}{meta['rel_path']}"
            lines.append(
                f"| **{meta['id']}** | [**{meta['title']}**]({link_path}) "
                f"| {lvl_icon}<br>`{meta['level']}` | `{meta['tier']}` | {meta['objective']} "
                f"| [<code>{wrappable_name}</code>]({link_path}) |"
            )

        lines.append("\n[↑ Back to Curriculum Overview](#curriculum-overview)\n")
        lines.append("---")

    return "\n".join(lines) + "\n"


def build_curriculum_catalog(base_dir: Path | None = None) -> None:
    """Updates both src/handbook/data/curriculum_matrix.md and docs/curriculum/index.md."""
    root = base_dir if base_dir is not None else BASE_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    matrix_md = generate_markdown()
    (root / "src" / "handbook" / "data" / "curriculum_matrix.md").write_text(
        matrix_md, encoding="utf-8"
    )

    header = (
        "# 📚 The Databricks Handbook Curriculum Catalog\n\n"
        "> **105 Databricks Recipes across 10 Modules and Verification Tiers "
        f"`T0`{_EN_DASH}`T3`**  \n"
        "> See [**Verification Tiers**](../verification.md) for measured AST and local Spark "
        "execution coverage across every recipe.\n"
        ">\n"
        "> 🧠 **Comprehensive Concept Taxonomy**: See "
        "[132 Curriculum Concepts & Topics Directory](topics.md) for deep-dive architectural "
        "definitions.\n\n"
        "---\n\n"
    )
    catalog_body = generate_markdown(path_prefix="../../")
    (root / "docs" / "curriculum" / "index.md").write_text(header + catalog_body, encoding="utf-8")


def main() -> None:
    build_curriculum_catalog()
    print("✅ Generated curriculum matrix and docs/curriculum/index.md")


if __name__ == "__main__":
    main()
