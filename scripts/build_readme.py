#!/usr/bin/env python3
"""
Builds the flagship README.md for The Databricks Handbook.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_FILE = BASE_DIR / "scripts" / "curriculum_matrix.md"
README_FILE = BASE_DIR / "README.md"

def build_readme():
    curriculum_md = CURRICULUM_FILE.read_text(encoding="utf-8")

    header = """# ⚡ The Databricks Handbook

**105 Production Coding Recipes, Unity Catalog Governance, Delta Lake 3.x, Lakeflow, Photon & Incident Runbooks**

[![CI Validation](https://github.com/santoshjammi29/databricks-handbook/actions/workflows/ci.yml/badge.svg)](https://github.com/santoshjammi29/databricks-handbook/actions)
[![Databricks](https://img.shields.io/badge/Databricks-Runtime_15.4%2B_LTS-FF3621?style=flat-square&logo=databricks&logoColor=white)](https://www.databricks.com/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5%2B-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta_Lake-3.2_ACID-00ADD8?style=flat-square&logo=delta&logoColor=white)](https://delta.io/)
[![Unity Catalog](https://img.shields.io/badge/Unity_Catalog-Unified_Governance-008080?style=flat-square&logo=databricks&logoColor=white)](https://www.databricks.com/product/unity-catalog)
[![Photon](https://img.shields.io/badge/Photon-C%2B%2B_Vectorized-8A2BE2?style=flat-square&logo=c%2B%2B&logoColor=white)](https://www.databricks.com/product/photon)
[![Python](https://img.shields.io/badge/Python-3.9_--_3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![DABs](https://img.shields.io/badge/Deploy-Databricks_Asset_Bundles-008080?style=flat-square&logo=databricks&logoColor=white)](databricks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

*The definitive enterprise reference repository of 105 battle-tested Databricks Data Intelligence Platform recipes, architectural blueprints, and disaster recovery incident runbooks.*  
*Structured in the official **Databricks Source Notebook format (`.py`)** for seamless 1-click sync with **Databricks Repos / Git Folders**, **Databricks Asset Bundles (DABs)**, **VS Code / Databricks Connect v2**, and CI/CD pipelines.*

[Curriculum Overview](#curriculum-overview) • [Platform Architecture](#platform-architecture) • [Whiteboard Blueprints](#whiteboard-blueprints) • [Quickstart](#quickstart) • [DAB Deployment](#dabs) • [Architecture Deep Dives](#architectures) • [Runbooks](#runbooks) • [Interview Matrix](#interview-matrix) • [FinOps Telemetry](#finops)

---

<a id="overview"></a>
## 🎯 Overview & Mission

Modern Lakehouse engineering on the **Databricks Data Intelligence Platform** demands far more than writing isolated Spark DataFrame transformations.

Enterprise data architects and lead engineers operate in zero-trust multi-cloud environments requiring:
- **Unified Account Governance**: Centralized Unity Catalog 3-level namespaces (`catalog.schema.table_or_volume`), Dynamic Row-Level Security (RLS), Column Masking, Lakehouse Federation (Snowflake, BigQuery, Postgres), Delta Sharing, and Clean Rooms.
- **Next-Generation Storage Internals**: Delta Lake 3.x ACID transaction log mechanics, Deletion Vectors (Merge-on-Read), Liquid Clustering (`CLUSTER BY`), Change Data Feed (CDF), Predictive Optimization, and Delta UniForm (Iceberg/Hudi).
- **Declarative ETL & Ingestion**: Databricks Auto Loader (`cloudFiles`), schema evolution (`addNewColumns`), `_rescued_data` poison pill isolation, and Delta Live Tables (DLT) with expectations and Dead Letter Queue (DLQ) quarantine patterns.
- **Enterprise Orchestration & DevOps**: Multi-task Lakeflow DAGs, task values context sharing (`dbutils.jobs.taskValues`), Run As Service Principal, Databricks Asset Bundles (DABs) IaC, and GitHub Actions CI/CD with cloud OIDC authentication.
- **High-Concurrency BI & Photon Engine**: Serverless SQL Warehouses, C++ SIMD vectorized execution, Intelligent Workload Management (IWM), multi-tier caching, AI/BI Dashboards (Lakeview), Genie Spaces, and Metric Views.
- **Databricks Apps & Mosaic AI**: Serverless Python web applications (Streamlit/FastAPI), managed Vector Search Delta Sync indexes, MLflow in Unity Catalog, real-time Model Serving, and enterprise RAG architectures.
- **FinOps & Observability**: Account-wide telemetry queries via Unity Catalog System Tables (`system.billing.usage`, `system.access.audit`, `system.compute.clusters`), right-sizing, cluster tag attribution, and statistical cost anomaly detection.

This repository provides **105 end-to-end, runnable, modular production recipes** covering every layer of the platform.

---

<a id="platform-architecture"></a>
## 🏛️ Platform Architecture

### 1. Split-Plane Cloud Architecture (Control Plane vs. Classic vs. Serverless)

```mermaid
flowchart TB
    subgraph CP["Control Plane (Databricks-Managed Cloud Tenant)"]
        UI["Workspace Web UI & IDE"]
        Scheduler["Lakeflow Jobs Scheduler"]
        Metastore["Unity Catalog Metastore Service"]
        ClusterMgr["Cluster Manager & Node Allocator"]
    end

    subgraph NetSec["Zero-Trust Network Perimeter"]
        PL_Front["Front-End Private Link (User -> Workspace)"]
        PL_Back["Back-End Private Link (Control Plane -> Compute Plane)"]
    end

    subgraph DP["Compute Plane (Classic Customer VNet or Managed Serverless)"]
        subgraph Classic["Classic Compute (Customer Cloud VNet)"]
            Driver["Spark Driver Node"]
            Worker1["Spark Worker Node 1"]
            Worker2["Spark Worker Node 2"]
        end
        subgraph Serverless["Serverless Compute (Pre-warmed Container Fleet)"]
            SQL_WH["Serverless SQL Warehouses"]
            Serverless_Jobs["Serverless Jobs & Notebooks"]
        end
    end

    subgraph Storage["Persistent Customer Cloud Storage Layer"]
        ADLS["Azure ADLS Gen2 / AWS S3 / Google Cloud Storage"]
        SecCred["Unity Catalog Storage Credentials (OIDC / Managed Identity)"]
    end

    UI --> PL_Front
    ClusterMgr --> PL_Back --> Driver
    Driver --> Worker1 & Worker2
    Worker1 & Worker2 -->|Direct HTTPS / TLS 1.3| ADLS
    SQL_WH -->|Storage Credentials| ADLS
    Metastore -.->|Metadata Grants| Driver & SQL_WH
```

---

### 2. Unity Catalog 3-Level Namespace Architecture

```mermaid
flowchart TD
    Metastore["Account-Level Unity Catalog Metastore (Region: us-east-1)"]
    
    Metastore --> CatProd["Catalog: prod_lakehouse (Managed Storage: s3://prod-lakehouse/)"]
    Metastore --> CatDev["Catalog: dev_lakehouse (Managed Storage: s3://dev-lakehouse/)"]
    Metastore --> CatFed["Foreign Catalog: snowflake_dw (Federated Connection)"]
    
    CatProd --> SchSilver["Schema: silver (Cleaned Data)"]
    CatProd --> SchGold["Schema: gold (Marts & Models)"]
    
    SchSilver --> TblOrders["Table: orders (Liquid Clustered Delta Table)"]
    SchSilver --> VolLanding["Volume: raw_documents (Managed Unstructured PDF/Images)"]
    SchGold --> ViewRevenue["View: monthly_revenue (Dynamic RLS Row Filter)"]
    SchGold --> ModelProphet["Model: churn_predictor (MLflow Model)"]
```

---

### 3. Medallion Lakehouse Architecture (Bronze → Silver → Gold)

```mermaid
flowchart LR
    subgraph Raw["Raw Sources"]
        S1["Cloud Storage (S3 / ADLS / GCS)"]
        S2["Kafka / Event Hubs"]
        S3["REST APIs / SaaS"]
    end

    subgraph Bronze["🥉 Bronze Layer"]
        B1["Raw Source Fidelity<br/>Auto Loader (cloudFiles)<br/>_rescued_data Quarantine"]
    end

    subgraph Silver["🥈 Silver Layer"]
        S_L["Cleaned & Conformed<br/>DLT Quality Expectations<br/>SCD 1 & 2 / CDF Merges"]
    end

    subgraph Gold["🥇 Gold Layer"]
        G1["Business Aggregates<br/>Liquid Clustering (`CLUSTER BY`)<br/>Photon SQL / Feature Store"]
    end

    Raw -->|"Auto Loader"| Bronze
    Bronze -->|"DLT Expectations & CDF"| Silver
    Silver -->|"Liquid Clustering & Photon"| Gold
```

---

<a id="whiteboard-blueprints"></a>
## 📐 Master Whiteboard Architecture Blueprints

The Databricks Handbook contains **52 architect-grade, hand-drawn digital whiteboard schematics** mirrored directly under [`assets/whiteboards/`](assets/whiteboards) and indexed with comprehensive multi-persona breakdowns, failure modes, and engine internals in [`docs/whiteboard_diagrams/README.md`](docs/whiteboard_diagrams/README.md).

### 🏛️ Core Platform & Engine Blueprints

#### 1. Databricks Unified Ecosystem & Lakehouse Architecture
![Databricks Unified Ecosystem & Lakehouse Architecture](assets/whiteboards/databricks_ecosystem_landscape.webp)

#### 2. Databricks Medallion Architecture (Bronze → Silver → Gold)
![Databricks Medallion Architecture](assets/whiteboards/databricks_medallion_architecture.webp)

#### 3. Unity Catalog Unified Governance & 3-Tier Namespace
![Unity Catalog Unified Governance](assets/whiteboards/unity_catalog_architecture.webp)

#### 4. Delta Lake 3.x Storage Engine & Transaction Log Mechanism
![Delta Lake Storage Engine](assets/whiteboards/delta_lake_mechanism.webp)

#### 5. Delta Lake 3.x vs. Apache Iceberg Architecture
![Delta Lake vs Apache Iceberg](assets/whiteboards/delta_lake_vs_iceberg_architecture.webp)

#### 6. Lakehouse ACID Concurrency, OCC & Row-Level Conflicts
![Lakehouse ACID Concurrency](assets/whiteboards/lakehouse_acid_concurrency.webp)

#### 7. Databricks Delta Live Tables (DLT) Declarative Pipeline
![Databricks DLT Pipeline](assets/whiteboards/databricks_dlt_pipeline.webp)

#### 8. Databricks Asset Bundles (DABs) Enterprise DevOps Pipeline
![Databricks DABs DevOps](assets/whiteboards/databricks_dabs_devops_pipeline.webp)

#### 9. Catalyst Optimizer & Vectorized Photon C++ Engine
![Catalyst & Photon Engine](assets/whiteboards/catalyst_photon_engine.webp)

#### 10. Photon Vectorized Engine vs. JVM Memory Execution
![Photon vs JVM](assets/whiteboards/photon_engine_vs_jvm.webp)

#### 11. Spark Memory Management, Execution Memory & Tungsten Disk Spill
![Spark Memory Management & Spill](assets/whiteboards/spark_memory_management_spill_diagram.webp)

#### 12. Lakehouse FinOps & DBU Cost Optimization Framework
![Lakehouse FinOps Cost Optimization](assets/whiteboards/lakehouse_finops_cost_optimization.webp)

---

### 🗺️ Full 52-Blueprint Catalog by Enterprise Domain

| Domain | Count | Primary Architecture Topics | Detailed Documentation |
| :--- | :---: | :--- | :---: |
| 🛡️ **Platform Landscape** | 8 | Ecosystem Landscape, Edge Compute, Distributed Resilience, Clean Rooms | [`docs/whiteboard_diagrams/#platform-landscape`](docs/whiteboard_diagrams/README.md#platform-landscape) |
| 🏛️ **Governance & Security** | 4 | Unity Catalog, Purview, Access Masking Lifecycle, BCDR Failover | [`docs/whiteboard_diagrams/#governance-security`](docs/whiteboard_diagrams/README.md#governance-security) |
| 💾 **Storage Engine** | 9 | Delta Lake Internals, Delta vs Iceberg, Open Formats, Compaction/Vacuum | [`docs/whiteboard_diagrams/#storage-engine`](docs/whiteboard_diagrams/README.md#storage-engine) |
| 🌊 **Data Pipelines & Ingestion** | 12 | DLT, Auto Loader, CDC Debezium, Kafka Streaming, Airflow, dbt, ADF | [`docs/whiteboard_diagrams/#data-pipelines-ingestion`](docs/whiteboard_diagrams/README.md#data-pipelines-ingestion) |
| 🚀 **Compute & Optimization** | 11 | Catalyst/Photon, Photon vs JVM, AQE Skew, Memory Spill, Join Trees | [`docs/whiteboard_diagrams/#compute-optimization`](docs/whiteboard_diagrams/README.md#compute-optimization) |
| 📊 **Fabric & Power BI** | 4 | OneLake Unified, Direct Lake VertiPaq, DAX Context, Shortcuts | [`docs/whiteboard_diagrams/#fabric-power-bi`](docs/whiteboard_diagrams/README.md#fabric-power-bi) |
| 📐 **Data Modeling** | 4 | Kimball Star Schema, Data Vault 2.0, SCD Types 1-6, Data Mesh | [`docs/whiteboard_diagrams/#data-modeling-architecture`](docs/whiteboard_diagrams/README.md#data-modeling-architecture) |

---

<a id="quickstart"></a>
## 🚀 Quickstart & Local Development

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/santoshjammi29/databricks-handbook.git
cd databricks-handbook

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Explore Recipes via the Interactive CLI Explorer
```bash
# Explore a specific recipe by ID or topic
python3 scripts/interactive_shell.py 025

# Search recipes by keyword
python3 scripts/interactive_shell.py "liquid clustering"

# List all 105 recipes across the 10 modules
python3 scripts/interactive_shell.py --list
```

### 3. Run Automated Validation & Test Suite
```bash
# Validate Databricks source notebook formatting and Python AST syntax across all 105 notebooks
python3 scripts/validate_notebooks.py

# Validate Databricks Asset Bundle schemas and paths
python3 scripts/validate_bundle.py

# Run standalone integrity test suite
python3 scripts/run_tests.py
```
"""

    footer = """
---

<a id="dabs"></a>
## 📦 Production Deployment with DABs

This repository includes a complete production-grade **Databricks Asset Bundle (DAB)** configuration suite under `databricks.yml` and `resources/*.yml`.

### 1. Validate Bundle Configurations
```bash
# Validate bundle schema and variable resolution for development target
databricks bundle validate -t dev

# Validate for production target
databricks bundle validate -t prod
```

### 2. Deploy to Development or Production
```bash
# Deploy to developer sandbox (/Users/username/.bundle/databricks-handbook/dev)
databricks bundle deploy -t dev

# Deploy to production via CI/CD Service Principal (/Shared/.bundle/databricks-handbook/prod)
databricks bundle deploy -t prod
```

### 3. Run Workflows & Pipelines
```bash
# Trigger master pipeline on production cluster
databricks bundle run -t prod databricks_handbook_master_pipeline
```

---

<a id="architectures"></a>
## 🏛️ Architecture Deep Dives

The repository includes 4 exhaustive system design and architectural specifications under `architectures/`:

| Document | Title | Core Architectural Focus |
| :---: | :--- | :--- |
| **01** | **[Split-Plane Security & Serverless Compute](architectures/01_split_plane_security_and_serverless_compute.md)** | Control Plane vs Compute Plane boundary, dual Private Link, VNet injection, and Serverless pre-warmed container micro-VMs. |
| **02** | **[Unity Catalog Governance & Federation](architectures/02_unity_catalog_governance_and_lakehouse_federation.md)** | 3-level namespace, Managed vs External tables, Volumes, Dynamic RLS, Column Masking, and cross-cloud Lakehouse Federation. |
| **03** | **[Delta Lake 3.x Storage Engine](architectures/03_delta_lake_3x_storage_engine_and_liquid_clustering.md)** | Transaction log internals (`000.json`), Deletion Vectors (MoR), Liquid Clustering Hilbert curves, and Delta UniForm. |
| **04** | **[Enterprise DevOps & Lakeflow Orchestration](architectures/04_enterprise_devops_dabs_and_lakeflow_orchestration.md)** | Databricks Asset Bundles (DABs), multi-environment targeting, GitHub Actions OIDC, and multi-task Lakeflow DAGs. |

---

<a id="runbooks"></a>
## 🚨 Battle-Tested Production Runbooks

The repository includes 6 emergency incident triage runbooks under `runbooks/`:

| Runbook | Incident Title | Severity | Forensic Focus & Key Remediation Steps |
| :---: | :--- | :---: | :--- |
| **01** | **[Driver & Executor OOM Triage](runbooks/01_driver_and_executor_oom_triage.md)** | `SEV-1` | Triage `java.lang.OutOfMemoryError`, eliminate `.collect()`, size driver memory, and resolve join skew via two-phase key salting. |
| **02** | **[Delta OCC Conflict Resolution](runbooks/02_delta_concurrent_modification_conflicts.md)** | `SEV-2` | Resolve `ConcurrentModificationException` and `ConcurrentAppendException` using Row-Level Concurrency and partition pruning. |
| **03** | **[Streaming State & RocksDB Recovery](runbooks/03_streaming_checkpoint_and_rocksdb_state_corruption.md)** | `SEV-1` | Recover from corrupted checkpoints, eliminate state store leaks using event-time watermarks, and tune off-heap RocksDB SSD settings. |
| **04** | **[Auto Loader Schema Drift & Poison Pills](runbooks/04_auto_loader_schema_drift_and_poison_pill_quarantine.md)** | `SEV-2` | Handle upstream schema drift via `addNewColumns`, extract unparseable records using `_rescued_data`, and route to DLQ tables. |
| **05** | **[Serverless SQL Warehouse Spill Tuning](runbooks/05_serverless_sql_warehouse_queueing_and_spill_tuning.md)** | `SEV-2` | Diagnose query queue times, switch scaling policy from Economy to Pro, and eliminate disk spills using Liquid Clustering. |
| **06** | **[Unity Catalog Permission Disasters](runbooks/06_unity_catalog_storage_credential_and_permission_disasters.md)** | `SEV-1` | Triage `PERMISSION_DENIED` and `StorageAccessDenied` errors, rotate expired cloud credentials, and repair 3-level grant hierarchies. |

---

<a id="interview-matrix"></a>
## 🎓 4-Tier Interview Preparation Matrix

Comprehensive technical interview guides and flashcard decks under `interview/`:

| Tier | Role Target | Core Focus Areas | Direct Link |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **Junior & Associate Engineer** | Platform Architecture, Split-Plane Security, Cluster Types, Delta Lake Basics vs. Parquet, `dbutils`, Medallion Architecture. | [`01_junior.md`](interview/01_junior_and_associate_databricks_engineer.md) |
| **Tier 2** | **Mid-Level Lakehouse Engineer** | Auto Loader, DLT Expectations, Delta ACID log internals, Deletion Vectors, Liquid Clustering, Unity Catalog 3-Level Namespace, DABs. | [`02_mid_level.md`](interview/02_mid_level_lakehouse_engineer.md) |
| **Tier 3** | **Senior Performance Engineer** | Catalyst AQE Skew Joins, Photon C++ Engine, Memory Triage & OOMs, Stateful Streaming & RocksDB, System Tables FinOps, Dynamic RLS/Masking. | [`03_senior.md`](interview/03_senior_databricks_performance_engineer.md) |
| **Tier 4** | **Staff & Principal Architect** | Multi-Cloud Lakehouse Topologies, Zero-Trust Networks, Lakehouse Federation, Delta Sharing Open Protocol, Enterprise RAG & Mosaic AI, Disaster Recovery. | [`04_staff.md`](interview/04_staff_and_principal_lakehouse_architect.md) |
| **Deck** | **50 Rapid-Fire Flashcards** | 50 rapid-fire questions and answers across all 10 modules of the Databricks Handbook curriculum. | [`05_flashcards.md`](interview/05_flashcards_deck_50.md) |

---

<a id="finops"></a>
## 💰 FinOps & System Tables Observability

Every production workload deployed on Databricks must be cost-monitored using **Unity Catalog System Tables**. The handbook provides production queries across:
- **DBU Burn Tracking (`system.billing.usage`)**: Aggregate daily DBU consumption by workspace, SKU, and cluster.
- **Mandatory Cost Center Attribution**: Parse `custom_tags['CostCenter']` to eliminate unallocated cloud spend leaks.
- **Compute Right-Sizing (`system.compute.clusters`)**: Identify zombie clusters running with < 10% CPU utilization.
- **Predictive Optimization ROI (`system.storage.predictive_optimization`)**: Measure exact files compacted and terabytes reclaimed.
- **Statistical Cost Anomaly Alerts**: Compute 14-day rolling mean and standard deviation ($3\\sigma$) to catch runaway queries.

---

## 📦 Sister Repositories & Knowledge Base

- ⚡ **[The PySpark Handbook (105 Production Recipes)](https://github.com/santoshjammi29/pyspark-handbook)**: 105 battle-tested PySpark & Delta Lake notebooks with Databricks Asset Bundles (DABs) IaC.
- ⚡ **[The SQL Handbook (105 Production Exercises)](https://github.com/santoshjammi29/sql-handbook)**: 105 production SQL exercises, query optimization recipes, MPP architectures, and incident runbooks.
- 🌐 **[Modern Data Engineer Hub (`moderndataengineer.uk`)](https://github.com/santoshjammi29/moderndataengineer)**: Live production encyclopedia featuring 11,950+ verified assets, interactive simulators, and 52 whiteboard blueprints.
- ☁️ **[Azure Enterprise Cheat Sheet](https://github.com/santoshjammi29/azure-cheat-sheet)**: Enterprise Azure architecture, networking, security, and governance.

---

## 📄 License & Attribution

Distributed under the **MIT License**. Author: **Santosh Jammi** (2026).  
Contributions, feedback, and enterprise architectural discussions are welcome!
"""

    full_readme = header + curriculum_md + footer
    README_FILE.write_text(full_readme, encoding="utf-8")
    print(f"✅ Generated master README.md at {README_FILE} ({len(full_readme)} bytes)")

if __name__ == "__main__":
    build_readme()
