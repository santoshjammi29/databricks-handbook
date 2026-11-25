"""
Dynamic README block generator for The Databricks Handbook.
Rewrites and verifies the generated module table within:
<!-- BEGIN GENERATED:modules --> ... <!-- END GENERATED:modules -->
"""

import re
from pathlib import Path

from handbook.curriculum import MODULES

BEGIN_MODULES_MARKER = "<!-- BEGIN GENERATED:modules -->"
END_MODULES_MARKER = "<!-- END GENERATED:modules -->"


def generate_modules_table() -> str:
    """Generates a clean, compact 10-row module overview table."""
    lines = [
        "| Track | Module Name | Range | Level | Domain Focus & Core Capabilities | Directory |",
        "|:---:|:---|:---:|:---:|:---|:---:|",
    ]

    module_summaries = {
        1: (
            "🟢 Foundational",
            "Split-plane security, VNet injection, cluster types & policies, "
            "CLI v0.200+, REST API 2.1, secrets",
        ),
        2: (
            "🟡 Intermediate",
            "3-level namespace, Managed vs External, Volumes, Dynamic RLS, "
            "Column Masking, Delta Sharing",
        ),
        3: (
            "🟡 Intermediate",
            "Transaction log internals, Deletion Vectors (MoR), Liquid Clustering, "
            "CDF, Predictive Optimization",
        ),
        4: (
            "🔴 Advanced",
            "Auto Loader (cloudFiles), schema drift, _rescued_data, DLT expectations, "
            "DLQ quarantine, CDC",
        ),
        5: (
            "🟡 Intermediate",
            "Multi-task DAGs, taskValues context sharing, Service Principals, "
            "triggers, retries & repair",
        ),
        6: (
            "🔴 Advanced",
            "Serverless SQL Warehouses, Photon C++ SIMD, IWM admission, "
            "multi-tier caching, Query Profile",
        ),
        7: (
            "🔴 Advanced",
            "Databricks Asset Bundles (databricks.yml), dev/staging/prod targets, "
            "GitHub Actions OIDC",
        ),
        8: (
            "🟣 Expert",
            "Databricks Apps (Streamlit/FastAPI), Vector Search Delta Sync, "
            "Foundation Model APIs, RAG",
        ),
        9: (
            "🟡 Intermediate",
            "system.billing.usage, cluster tagging attribution, audit forensics, "
            "zombie detection, anomalies",
        ),
        10: (
            "🟣 Principal",
            "Driver/Executor OOM triage, OCC conflict resolution, 99% straggler salting, "
            "RocksDB state leaks",
        ),
    }

    for mod in MODULES:
        lvl, summary = module_summaries.get(mod.index, ("🟡 Intermediate", mod.name))
        slug = f"module-{mod.index:02d}-{mod.folder[3:].replace('_', '-')}"
        name_clean = mod.name.split(":", 1)[1].strip()
        link = f"[`{mod.index:02d}. {name_clean}`](docs/curriculum/index.md#{slug})"
        dir_link = f"[`{mod.expected_count} Recipes`](notebooks/{mod.folder}/)"
        lines.append(
            f"| **{mod.index:02d}** | {link} | `{mod.id_range_str}` | "
            f"{lvl} | {summary} | {dir_link} |"
        )

    return "\n".join(lines)


def update_readme_blocks(base_dir: Path | None = None, check: bool = False) -> bool:
    """
    Updates or checks generated blocks in README.md.
    Returns True when markers are present and (for check=True) content is in sync.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    readme_file = base_dir / "README.md"
    if not readme_file.exists():
        raise FileNotFoundError(f"README.md missing at {readme_file}")

    content = readme_file.read_text(encoding="utf-8")
    if BEGIN_MODULES_MARKER not in content or END_MODULES_MARKER not in content:
        return False

    table_content = generate_modules_table()
    pattern = re.compile(
        rf"{re.escape(BEGIN_MODULES_MARKER)}.*?{re.escape(END_MODULES_MARKER)}",
        re.DOTALL,
    )
    replacement = f"{BEGIN_MODULES_MARKER}\n{table_content}\n{END_MODULES_MARKER}"

    if not pattern.search(content):
        return False

    new_content = pattern.sub(replacement, content)
    if check:
        return new_content == content

    readme_file.write_text(new_content, encoding="utf-8")
    return True


def build_readme(base_dir: Path | None = None, check: bool = False) -> bool:
    """Rebuilds or checks README dynamic blocks."""
    return update_readme_blocks(base_dir=base_dir, check=check)


if __name__ == "__main__":
    build_readme()
