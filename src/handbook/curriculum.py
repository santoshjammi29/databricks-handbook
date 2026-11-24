"""
Curriculum and Repository Structure Registry for The Databricks Handbook.

Single source of truth for modules, notebook counts, id ranges, and repository assets.
All validators, generators, test suites, and documentation builders import from this registry.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class ModuleSpec:
    """Specification for a curriculum module."""
    index: int
    folder: str
    name: str
    id_start: int
    id_end: int

    @property
    def expected_count(self) -> int:
        return self.id_end - self.id_start + 1

    @property
    def id_range_str(self) -> str:
        return f"{self.id_start:03d}-{self.id_end:03d}"


MODULES: Tuple[ModuleSpec, ...] = (
    ModuleSpec(
        index=1,
        folder="01_platform_architecture_and_security",
        name="Module 01: Platform Architecture, Workspaces & Control Plane",
        id_start=1,
        id_end=10,
    ),
    ModuleSpec(
        index=2,
        folder="02_unity_catalog_and_governance",
        name="Module 02: Unity Catalog — Governance, Security & Federation",
        id_start=11,
        id_end=21,
    ),
    ModuleSpec(
        index=3,
        folder="03_delta_lake_storage_engine",
        name="Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm",
        id_start=22,
        id_end=32,
    ),
    ModuleSpec(
        index=4,
        folder="04_lakeflow_ingestion_and_dlt",
        name="Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)",
        id_start=33,
        id_end=43,
    ),
    ModuleSpec(
        index=5,
        folder="05_lakeflow_jobs_and_orchestration",
        name="Module 05: Lakeflow Jobs, Workflows & Orchestration",
        id_start=44,
        id_end=54,
    ),
    ModuleSpec(
        index=6,
        folder="06_databricks_sql_and_photon",
        name="Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer",
        id_start=55,
        id_end=65,
    ),
    ModuleSpec(
        index=7,
        folder="07_enterprise_devops_and_dabs",
        name="Module 07: Enterprise DevOps — DABs, CI/CD & Testing",
        id_start=66,
        id_end=76,
    ),
    ModuleSpec(
        index=8,
        folder="08_databricks_apps_and_mosaic_ai",
        name="Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)",
        id_start=77,
        id_end=87,
    ),
    ModuleSpec(
        index=9,
        folder="09_finops_and_system_tables",
        name="Module 09: FinOps, Observability & System Tables Masterclass",
        id_start=88,
        id_end=98,
    ),
    ModuleSpec(
        index=10,
        folder="10_production_incidents_and_blueprints",
        name="Module 10: Production Incidents, Triage & Architecture Blueprints",
        id_start=99,
        id_end=105,
    ),
)

TOTAL_MODULES: int = len(MODULES)
TOTAL_NOTEBOOKS: int = sum(m.expected_count for m in MODULES)
EXPECTED_MODULE_FOLDERS: List[str] = [m.folder for m in MODULES]

TOTAL_WHITEBOARDS: int = 52
TOTAL_RUNBOOKS: int = 6
TOTAL_ARCHITECTURES: int = 4
TOTAL_INTERVIEW_GUIDES: int = 5
TOTAL_FLASHCARDS: int = 50
TOTAL_TOPICS: int = 132

EXPECTED_BUNDLE_RESOURCES: Tuple[str, ...] = (
    "jobs.yml",
    "dlt_pipelines.yml",
    "unity_catalog.yml",
    "dashboards.yml",
    "model_serving.yml",
    "apps.yml",
)
