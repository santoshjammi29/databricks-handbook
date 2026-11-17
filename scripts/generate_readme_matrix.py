#!/usr/bin/env python3
"""
Generates the Curriculum Matrix and Track Overview for The Databricks Handbook README.md.
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

MODULE_CONFIG = {
    "01_platform_architecture_and_security": {
        "icon": "🛡️",
        "title": "01. Platform Architecture & Security",
        "anchor": "module-01-platform-architecture-and-security",
        "range": "001 – 010",
        "level": "🟢<br>Foundational",
        "desc": "Split-plane security, VNet injection, cluster types & policies, CLI v0.200+, REST API 2.1, secrets, volumes"
    },
    "02_unity_catalog_and_governance": {
        "icon": "🏛️",
        "title": "02. Unity Catalog & Governance",
        "anchor": "module-02-unity-catalog-and-governance",
        "range": "011 – 021",
        "level": "🟡<br>Intermediate",
        "desc": "3-level namespace, Managed vs External, Volumes, Dynamic RLS, Column Masking, Federation, Delta Sharing, ABAC"
    },
    "03_delta_lake_storage_engine": {
        "icon": "⚡",
        "title": "03. Delta Lake 3.x Storage Engine",
        "anchor": "module-03-delta-lake-storage-engine",
        "range": "022 – 032",
        "level": "🟡<br>Intermediate",
        "desc": "Transaction log internals, Deletion Vectors (MoR), Liquid Clustering, CDF, Predictive Optimization, UniForm, Clones"
    },
    "04_lakeflow_ingestion_and_dlt": {
        "icon": "🌊",
        "title": "04. Lakeflow Ingestion & DLT",
        "anchor": "module-04-lakeflow-ingestion-and-dlt",
        "range": "033 – 043",
        "level": "🔴<br>Advanced",
        "desc": "Auto Loader (cloudFiles), schema drift, _rescued_data, DLT expectations, DLQ quarantine, CDC apply_changes"
    },
    "05_lakeflow_jobs_and_orchestration": {
        "icon": "⚙️",
        "title": "05. Lakeflow Jobs & Orchestration",
        "anchor": "module-05-lakeflow-jobs-and-orchestration",
        "range": "044 – 054",
        "level": "🟡<br>Intermediate",
        "desc": "Multi-task DAGs, taskValues context sharing, Service Principals, triggers, exponential retries, repair & rerun"
    },
    "06_databricks_sql_and_photon": {
        "icon": "🚀",
        "title": "06. Databricks SQL & Photon Engine",
        "anchor": "module-06-databricks-sql-and-photon",
        "range": "055 – 065",
        "level": "🔴<br>Advanced",
        "desc": "Serverless SQL Warehouses, Photon C++ SIMD, IWM admission, multi-tier caching, Query Profile, AI/BI dashboards, Genie"
    },
    "07_enterprise_devops_and_dabs": {
        "icon": "📦",
        "title": "07. Enterprise DevOps & DABs",
        "anchor": "module-07-enterprise-devops-and-dabs",
        "range": "066 – 076",
        "level": "🔴<br>Advanced",
        "desc": "Databricks Asset Bundles (databricks.yml), dev/staging/prod targets, GitHub Actions OIDC, Terraform, DB Connect v2"
    },
    "08_databricks_apps_and_mosaic_ai": {
        "icon": "🤖",
        "title": "08. Databricks Apps & Mosaic AI",
        "anchor": "module-08-databricks-apps-and-mosaic_ai",
        "range": "077 – 087",
        "level": "🟣<br>Expert",
        "desc": "Databricks Apps (Streamlit/FastAPI), Vector Search Delta Sync, Foundation Model APIs, MLflow in UC, Enterprise RAG"
    },
    "09_finops_and_system_tables": {
        "icon": "💰",
        "title": "09. FinOps & System Tables",
        "anchor": "module-09-finops-and-system-tables",
        "range": "088 – 098",
        "level": "🟡<br>Intermediate",
        "desc": "system.billing.usage, cluster tagging attribution, audit forensics, zombie detection, 3-sigma cost anomalies, ARM VMs"
    },
    "10_production_incidents_and_blueprints": {
        "icon": "🚨",
        "title": "10. Incident Triage & Architecture Blueprints",
        "anchor": "module-10-production-incidents-and-blueprints",
        "range": "099 – 105",
        "level": "🟣<br>Principal",
        "desc": "Driver/Executor OOM triage, OCC conflict resolution, 99% straggler salting, RocksDB state leaks, master blueprint"
    }
}

def clean_for_table(text: str) -> str:
    if not text:
        return ""
    t = text.replace("|", "&#124;").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", t)

def extract_notebook_meta(nb_path: Path):
    content = nb_path.read_text(encoding="utf-8")
    
    # Extract ID and Title from Markdown header (# 001. ...)
    m_title = re.search(r"# MAGIC # (\d+)\.\s*(.+)", content)
    if m_title:
        nb_id = m_title.group(1)
        title = m_title.group(2).strip()
    else:
        nb_id = nb_path.name[:3]
        title = nb_path.stem[4:].replace("_", " ").title()
        
    # Extract Level
    m_level = re.search(r"# MAGIC \*\*Mastery Level\*\*:\s*`([^`]+)`", content)
    level = m_level.group(1).strip() if m_level else "Intermediate"
    
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
        "objective": clean_for_table(objective),
        "rel_path": f"notebooks/{nb_path.parent.name}/{nb_path.name}"
    }

def generate_markdown() -> str:
    lines = []
    lines.append("## 🗺️ Curriculum Overview & Track Architecture\n")
    lines.append("| Track | Module Name | Recipe Range | Level | Domain Focus & Key Capabilities |")
    lines.append("| :---: | :--- | :---: | :---: | :--- |")
    
    for mod_dir, cfg in MODULE_CONFIG.items():
        track_num = cfg["title"].split(".")[0]
        name_clean = cfg["title"].split(".")[1].strip()
        lines.append(f"| **{track_num}** | **[{cfg['icon']} {name_clean}](#-{cfg['anchor']})** | `{cfg['range']}` | {cfg['level']} | {cfg['desc']} |")
        
    lines.append("\n---\n")
    
    for mod_dir, cfg in MODULE_CONFIG.items():
        dir_path = NOTEBOOKS_DIR / mod_dir
        if not dir_path.exists():
            continue
            
        nb_files = sorted(list(dir_path.glob("*.py")))
        lines.append(f"\n### {cfg['icon']} <a id=\"{cfg['anchor']}\"></a>{cfg['title']} (`{cfg['range']}`)\n")
        lines.append(f"> **Focus**: {cfg['desc']}\n")
        lines.append("| # | Recipe Title | Level | Core Engineering Objective & Production Invariant | Source |")
        lines.append("| :---: | :--- | :---: | :--- | :---: |")
        
        for nb in nb_files:
            meta = extract_notebook_meta(nb)
            lvl_icon = "🟢" if "Foundational" in meta["level"] or "Beginner" in meta["level"] else ("🟡" if "Intermediate" in meta["level"] else ("🔴" if "Advanced" in meta["level"] else "🟣"))
            lines.append(f"| **{meta['id']}** | **{meta['title']}** | {lvl_icon}<br>`{meta['level']}` | {meta['objective']} | [`.py`]({meta['rel_path']}) |")
            
        lines.append("\n[↑ Back to Curriculum Overview](#-curriculum-overview)\n")
        lines.append("---")
        
    return "\n".join(lines) + "\n"

def main():
    curriculum_md = generate_markdown()
    out_file = BASE_DIR / "scripts" / "curriculum_matrix.md"
    out_file.write_text(curriculum_md, encoding="utf-8")
    print(f"✅ Generated curriculum matrix at {out_file} ({len(curriculum_md)} bytes)")

if __name__ == "__main__":
    main()
