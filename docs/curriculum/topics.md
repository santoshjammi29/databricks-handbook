# 🧠 Curriculum Topics Directory — 132 Topics Covered

> **Curriculum Scope**: **132 Production Topics** verified against real-world lakehouse internals, query engines, and distributed architectures.
> **Organization**: Grouped by **Relevant Functional Sections** and then by **Difficulty Level**.
> **Navigation**: All sections are **collapsible and collapsed by default** for rapid scanning.
> **Live Web Hub**: Explore interactive search and mindmaps at [moderndataengineer.uk/concepts](https://moderndataengineer.uk/concepts).

---

## 📑 Topics Directory at a Glance

| Pillar / Module | Topics | Functional Sections Covered | Status |
|:---|:---:|:---|:---:|
| ⚡ **Databricks Platform, Unity Catalog & Delta Lake 3.x** | **132** | Unity Catalog 3-Tier Governance & Security, Delta Lake 3.x ACID Mechanics & Transaction Log, Physical Layout, Liquid Clustering & Deletion Vectors, and 2 more | ✅ Collapsible Deck |

---

## 📚 Comprehensive Topic Specifications (Grouped by Section & Difficulty)

<details>
<summary><b>⚡ Databricks Platform, Unity Catalog & Delta Lake 3.x (132 Topics across 5 Sections)</b> — <i>Click to expand module</i></summary>

<details>
<summary>&nbsp;&nbsp;📂 <b>Section: Unity Catalog 3-Tier Governance & Security (42 Topics)</b> — <i>Click to expand functional domain</i></summary>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟢 Easy: <b>🟢 Easy (Level 100) (7 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Cluster Policy** | `🟢 Easy` | A Cluster Policy is an administrative governance rule set that restricts the configuration options available to users when provisioning compute clusters. |
| 2 | **Data Explorer** | `🟢 Easy` | Data Explorer is the visual UI tool in the Databricks Workspace used to discover, manage, inspect, and grant permissions on Unity Catalog data assets. |
| 3 | **Databricks Workspace** | `🟢 Easy` | A Databricks Workspace is a software-as-a-service (SaaS) environment that provides a unified collaborative interface for data engineers, data scientists, and analysts to access compute, notebooks, and storage. |
| 4 | **Metastore** | `🟢 Easy` | A Metastore is the central metadata repository that catalogs schema definitions, table partition locations, data types, and access privileges for data stored in the lakehouse. |
| 5 | **Three-Level Namespace** | `🟢 Easy` | The standard 3-tier logical namespace (`catalog.schema.table_or_view`) introduced by Unity Catalog to structure enterprise data assets, manage permissions, and enforce data mesh boundaries. |
| 6 | **Unity Catalog** | `🟢 Easy` | Unity Catalog is Databricks' centralized, multi-cloud governance solution providing unified access control, data auditing, lineage tracking, and discovery across all workspace assets. |
| 7 | **Volumes** | `🟢 Easy` | Governed Unity Catalog storage abstractions that provide secure access, governance, and audit lineage for non-tabular files including raw CSVs, unstructured text, images, and machine learning models. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟡 Intermediate: <b>🟡 Intermediate (Level 200) (11 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Compute Policies & Cluster Governance** | `🟡 Intermediate` | Administrative governance guardrails that enforce compute provisioning boundaries—including allowed VM types, max worker limits, spot instance allocations, and idle auto-termination. |
| 2 | **Data Lineage** | `🟡 Intermediate` | The automated, real-time metadata tracking engine in Unity Catalog that captures column-level and table-level data flow lineage across queries, notebooks, workflows, and dashboards. |
| 3 | **Delta UniForm & Multi-Engine Interoperability** | `🟡 Intermediate` | Delta Lake Universal Format (UniForm), which automatically translates and maintains Apache Iceberg and Apache Hudi metadata alongside Delta logs, enabling multi-engine query access without data duplication. |
| 4 | **Dynamic Views for Security** | `🟡 Intermediate` | Security-hardened SQL views that evaluate user context functions (`CURRENT_USER()`, `IS_MEMBER()`) at runtime to provide row-level filtering and column-level masking without duplicating data. |
| 5 | **External Locations & Storage Credentials** | `🟡 Intermediate` | Unity Catalog securable objects that encapsulate cloud identity credentials (IAM roles, Managed Identities) and associate them with specific object storage URLs for governed external table access. |
| 6 | **Managed vs. External Tables: Architecture Tradeoffs** | `🟡 Intermediate` | The strategic trade-offs between Unity Catalog managed tables (lifecycle managed by Databricks, Predictive Optimization enabled) and external tables (custom storage locations, multi-engine access). |
| 7 | **Permission Model & Inheritance** | `🟡 Intermediate` | The hierarchical access control model in Unity Catalog where security privileges granted on parent securable objects (Catalogs) automatically cascade down to Schemas, Tables, and Views. |
| 8 | **System Tables for Operations** | `🟡 Intermediate` | Centrally governed, audit-grade operational telemetry tables in Unity Catalog (`system.billing`, `system.compute`, `system.access`) used for cost tracking, cluster audit logs, and FinOps analytics. |
| 9 | **Unity Catalog Lineage Tracking** | `🟡 Intermediate` | Automated capture of column-level and table-level data flow across queries, jobs, and dashboards. |
| 10 | **Unity Catalog Volumes (Managed vs. External)** | `🟡 Intermediate` | A Unity Catalog securable object that extends centralized catalog governance, audit trails, and SQL permissions to unstructured and semi-structured files. |
| 11 | **Vector Search** | `🟡 Intermediate` | Databricks Vector Search is a serverless vector database integrated into Unity Catalog that stores and indexes vector embeddings for real-time similarity search and RAG applications. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🔴 Advanced: <b>🔴 Advanced (Level 300) (9 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Audit Logging** | `🔴 Advanced` | Audit Logging captures, records, and exports detailed security audit trails of all user and system activities occurring across Databricks workspaces and Unity Catalog. |
| 2 | **Databricks DBU Allocation via system.billing.usage** | `🔴 Advanced` | The system catalog telemetry table in Unity Catalog that records minute-by-minute Databricks Unit (DBU) consumption across all workspaces, jobs, and users. |
| 3 | **Lakehouse Federation** | `🔴 Advanced` | Lakehouse Federation allows Unity Catalog to query external operational and analytical databases (Snowflake, BigQuery, PostgreSQL, MySQL, SQL Server) in place without moving data. |
| 4 | **Multi-Workspace Architecture** | `🔴 Advanced` | Enterprise platform deployment topology evaluating single-workspace versus multi-workspace designs for team isolation, regulatory compliance boundaries, and multi-region governance. |
| 5 | **Predictive Optimization** | `🔴 Advanced` | Predictive Optimization is an automated AI-driven service in Databricks that intelligently schedules OPTIMIZE and VACUUM maintenance operations on Unity Catalog managed tables. |
| 6 | **Row Filters & Column Masks** | `🔴 Advanced` | Applying row-level and column-level security directly to tables via SQL UDFs. |
| 7 | **SCIM Provisioning** | `🔴 Advanced` | SCIM (System for Cross-domain Identity Management) Provisioning automatically synchronizes users, service principals, and security groups from enterprise identity providers to Databricks. |
| 8 | **Unity Catalog Fine-Grained Access Control** | `🔴 Advanced` | Fine-Grained Access Control in Unity Catalog enforces cell-level security via Row Filters and Column Masks defined with standard SQL functions. |
| 9 | **Unity Catalog System Tables** | `🔴 Advanced` | Unity Catalog System Tables are analytical Delta tables hosted in the system catalog that expose operational metadata, cost telemetry, query history, and data lineage. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟣 Architect: <b>🟣 Staff Architect (Level 400) (15 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Data Mesh on Databricks** | `🟣 Architect` | An architectural implementation of the Data Mesh paradigm on Databricks, treating data as a product owned by decentralized domain teams governed by Unity Catalog. |
| 2 | **Databricks + dbt Integration** | `🟣 Architect` | The production architecture pairing dbt with Databricks SQL Serverless and Unity Catalog, leveraging the dbt-databricks adapter for high-performance lakehouse transformations. |
| 3 | **Databricks Genie Compound AI** | `🟣 Architect` | A natural language conversational interface translating business questions into certified SQL over Unity Catalog metric views. |
| 4 | **Databricks Lakeflow Connectors** | `🟣 Architect` | Native managed SaaS and database ingestion connectors for Salesforce, Workday, ServiceNow, and SQL databases into Unity Catalog. |
| 5 | **Databricks Split-Plane Cloud Architecture** | `🟣 Architect` | A dual-plane cloud security model that segregates management/control infrastructure from distributed compute execution and persistent customer storage. |
| 6 | **Databricks Unity Catalog Architecture** | `🟣 Architect` | The centralized governance, metadata, and fine-grained access control layer for all data and AI assets across multiple Databricks workspaces in a cloud tenant. |
| 7 | **DBU Cost Governance** | `🟣 Architect` | The architectural framework and operational policies used to monitor, allocate, forecast, and optimize Databricks Unit (DBU) consumption and cloud infrastructure costs. |
| 8 | **Governance with Unity Catalog + Purview** | `🟣 Architect` | The enterprise governance integration between Databricks Unity Catalog and Microsoft Purview, unifying lakehouse metadata with company-wide data governance. |
| 9 | **Mosaic AI Vector Search Continuous Delta Sync** | `🟣 Architect` | A serverless vector database integrated with Unity Catalog that automatically synchronizes vector embeddings with underlying Delta tables in real time. |
| 10 | **Multi-Cloud Databricks Deployment** | `🟣 Architect` | An enterprise deployment pattern operating Databricks across multiple cloud providers (AWS, Azure, GCP) while maintaining unified governance and consistent CI/CD pipelines. |
| 11 | **Unity Catalog Dynamic Column Masking & Row Filters** | `🟣 Architect` | Declarative SQL-based fine-grained access control policies enforced transparently at the Unity Catalog metadata layer. |
| 12 | **Unity Catalog Dynamic Row Filters & Column Masks** | `🟣 Architect` | Fine-grained SQL access control mechanisms in Unity Catalog that dynamically redact columns or filter table rows based on the querying user's group membership. |
| 13 | **Unity Catalog Enterprise Governance** | `🟣 Architect` | The enterprise governance operating model for Unity Catalog encompassing account-level identity management, catalog segregation, classification tagging, and regulatory audit compliance. |
| 14 | **Unity Catalog Multi-Workspace Topology** | `🟣 Architect` | An enterprise architecture design that connects multiple environment- or business-unit-specific workspaces to a single regional Unity Catalog metastore. |
| 15 | **Unity Catalog System Tables for Lakehouse FinOps** | `🟣 Architect` | Centrally governed, read-only analytical schemas providing real-time telemetry on compute usage, billing, audit access, and lineage across an entire account. |

</details>

</details>

<details>
<summary>&nbsp;&nbsp;📂 <b>Section: Delta Lake 3.x ACID Mechanics & Transaction Log (10 Topics)</b> — <i>Click to expand functional domain</i></summary>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟢 Easy: <b>🟢 Easy (Level 100) (4 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **ACID Transactions** | `🟢 Easy` | The set of transactional guarantees (Atomicity, Consistency, Isolation, Durability) enforced by Delta Lake on top of cloud object storage using an append-only transaction log and optimistic concurrency control. |
| 2 | **Delta Lake (Databricks)** | `🟢 Easy` | Delta Lake is an open-source storage framework that brings ACID transactions, scalable metadata handling, and unified streaming and batch data processing to Apache Spark and data lakes. |
| 3 | **Shallow vs. Deep Clones** | `🟢 Easy` | Delta Lake table cloning capabilities that either create zero-copy metadata pointers to source data files (SHALLOW CLONE) or create fully independent physical table copies (DEEP CLONE). |
| 4 | **Transaction Log (`_delta_log`)** | `🟢 Easy` | The ordered, append-only directory of JSON commit files and Parquet checkpoints (`_delta_log`) that serves as the single source of truth for all metadata, schema versions, and physical file operations in a Delta table. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟡 Intermediate: <b>🟡 Intermediate (Level 200) (4 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Databricks SQL Warehouse** | `🟡 Intermediate` | A Databricks SQL Warehouse is a specialized compute resource optimized for SQL workloads, business intelligence queries, and high-concurrency analytical dashboards. |
| 2 | **Delta Time Travel** | `🟡 Intermediate` | Delta Time Travel is the ability to query point-in-time historical snapshots of a Delta table using historical commit versions or timestamps. |
| 3 | **Shallow Clone vs Deep Clone** | `🟡 Intermediate` | Delta Cloning creates copies of a table: Shallow Clone copies only metadata references with zero data duplication, whereas Deep Clone creates a fully independent physical copy of data and metadata. |
| 4 | **VACUUM Command** | `🟡 Intermediate` | The VACUUM command permanently deletes historical data files from cloud storage that are no longer referenced by the active Delta table log and exceed a retention threshold. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🔴 Advanced: <b>🔴 Advanced (Level 300) (1 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Databricks Serverless SQL Warehouse** | `🔴 Advanced` | A fully managed, instant-starting compute tier in Databricks optimized for high-concurrency SQL and BI queries running inside Databricks-managed compute planes. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟣 Architect: <b>🟣 Staff Architect (Level 400) (1 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Stream-to-Table Commit Boundary** | `🟣 Architect` | The consistency boundary between a streaming engine's checkpoint progress and the durable commit visible in its table sink. |

</details>

</details>

<details>
<summary>&nbsp;&nbsp;📂 <b>Section: Physical Layout, Liquid Clustering & Deletion Vectors (12 Topics)</b> — <i>Click to expand functional domain</i></summary>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟢 Easy: <b>🟢 Easy (Level 100) (1 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Delta Lake Liquid Clustering vs Hive Partitioning** | `🟢 Easy` | A physical data layout protocol that dynamically groups data along multiple columns without the rigidity, small-file explosion, or partition skew of traditional Hive directory trees. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟡 Intermediate: <b>🟡 Intermediate (Level 200) (6 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Cluster Sizing & Autoscaling** | `🟡 Intermediate` | The operational strategy of balancing cluster node memory-to-core ratios and autoscaling worker limits to optimize workload parallelism while controlling cloud infrastructure spending. |
| 2 | **OPTIMIZE & File Compaction** | `🟡 Intermediate` | A Delta Lake table maintenance command that bin-packs small files (1MB–10MB) into optimal larger files (~1GB) to reduce cloud object storage API overhead and significantly accelerate analytical query scanning performance. |
| 3 | **OPTIMIZE Command** | `🟡 Intermediate` | The OPTIMIZE command compacts fragmented small Parquet files in a Delta table into larger, query-efficient files (typically ~1GB in size). |
| 4 | **VACUUM & Storage Lifecycle** | `🟡 Intermediate` | A Delta Lake table maintenance command that permanently purges unreferenced physical data files older than a configured retention safety threshold (default 7 days) to reclaim object storage capacity. |
| 5 | **Write Optimization** | `🟡 Intermediate` | Delta Lake write-time optimizations—such as `optimizeWrite` and auto-compaction—that dynamically coalesce and size Parquet data files during ingestion to avoid small-file fragmentation. |
| 6 | **Z-Ordering** | `🟡 Intermediate` | Z-Ordering is a multidimensional clustering technique that colocates related information in the same set of Parquet files to maximize file skipping during SQL queries. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🔴 Advanced: <b>🔴 Advanced (Level 300) (3 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Delta Table Properties & Configuration** | `🔴 Advanced` | Configurable table-level metadata properties in Delta Lake that govern engine behavior, including Change Data Feed enablement, Deletion Vector activation, column mapping mode, and checkpoint frequency. |
| 2 | **Liquid Clustering** | `🔴 Advanced` | Delta Lake 3.x's next-generation data layout engine (`CLUSTER BY`) that organizes data along space-filling curves to optimize multi-dimensional query pruning without hive partitioning or write amplification. |
| 3 | **MERGE Write Amplification** | `🔴 Advanced` | The storage I/O performance penalty in copy-on-write architectures where updating a single row forces the engine to rewrite the entire underlying Parquet file. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟣 Architect: <b>🟣 Staff Architect (Level 400) (2 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Delta Lake Deletion Vectors** | `🟣 Architect` | A storage optimization technique in Delta Lake that marks deleted or updated rows using lightweight bitmap index files instead of rewriting entire Parquet data files. |
| 2 | **Delta Lake Liquid Clustering Architecture** | `🟣 Architect` | A modern, dynamic data layout architecture that organizes Delta Lake Parquet files along a space-filling Hilbert curve without rigid Hive directory hierarchies. |

</details>

</details>

<details>
<summary>&nbsp;&nbsp;📂 <b>Section: Workflows, DLT & Lakeflow Pipelines (18 Topics)</b> — <i>Click to expand functional domain</i></summary>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟢 Easy: <b>🟢 Easy (Level 100) (4 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Databricks Job** | `🟢 Easy` | A Databricks Job is a scheduled or triggered execution unit that runs non-interactive code (notebooks, JARs, Python scripts, dbt models) on automated compute clusters. |
| 2 | **Databricks Workflow** | `🟢 Easy` | Databricks Workflows is the fully managed, native orchestration service within Databricks that designs, schedules, and monitors multi-task Directed Acyclic Graphs (DAGs). |
| 3 | **Job Cluster** | `🟢 Easy` | A Job Cluster is an ephemeral, dedicated compute cluster automatically provisioned by Databricks to execute a specific automated workload and terminated immediately upon completion. |
| 4 | **Parameterization: Widgets, Job Parameters, Task Values** | `🟢 Easy` | The runtime parameterization suite in Databricks—including notebook widgets, job-level parameters, and inter-task dynamic task values—used to construct dynamic and reusable workflows. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟡 Intermediate: <b>🟡 Intermediate (Level 200) (6 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **DBU Cost Model & Billing** | `🟡 Intermediate` | The consumption-based billing framework where platform workloads consume Databricks Units (DBUs) based on compute SKU tiers (All-Purpose, Automated Jobs, SQL Serverless, and Lakeflow). |
| 2 | **Delta Live Tables (DLT)** | `🟡 Intermediate` | Delta Live Tables (DLT) is a declarative ETL framework in Databricks that simplifies data pipeline development by managing dependencies, infrastructure scaling, and data quality enforcement. |
| 3 | **Expectations (Quality Rules)** | `🟡 Intermediate` | Declarative data quality rules in Lakeflow pipelines (`EXPECT`, `EXPECT OR DROP`, `EXPECT OR FAIL`) that audit record integrity and maintain automated telemetry on data quality metrics. |
| 4 | **Incremental Processing Patterns** | `🟡 Intermediate` | Data pipeline design architectures that ingest and transform only new or modified data since the prior execution checkpoint, leveraging Auto Loader, Change Data Feed, and streaming watermarks. |
| 5 | **Streaming Tables vs. Materialized Views** | `🟡 Intermediate` | The architectural distinction in Lakeflow between append-only Streaming Tables for continuous incremental ingestion and stateful Materialized Views for precomputed analytical query acceleration. |
| 6 | **Task Dependencies, Retries & Conditional Logic** | `🟡 Intermediate` | Workflow orchestration primitives in Lakeflow Jobs that define multi-task DAG dependencies, conditional branch routing, retry policies, and SLA timeout limits. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🔴 Advanced: <b>🔴 Advanced (Level 300) (7 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **CDC Processing: AUTO CDC INTO** | `🔴 Advanced` | Declarative CDC processing primitives in Lakeflow pipelines that automatically reconcile out-of-order change logs and maintain SCD Type 1 or SCD Type 2 dimension tables. |
| 2 | **Databricks Delta Live Tables (DLT) Expectations** | `🔴 Advanced` | Declarative data quality rules (`@dlt.expect`, `@dlt.expect_or_drop`, `@dlt.expect_or_fail`) embedded into streaming pipelines. |
| 3 | **DLT Expectations** | `🔴 Advanced` | DLT Expectations are declarative data quality assertions applied to Delta Live Tables that validate incoming records and govern pipeline behavior upon data quality violations. |
| 4 | **Error Handling & Dead Letter Patterns** | `🔴 Advanced` | A resilient pipeline design pattern that routes malformed or schema-violating records into quarantined Dead-Letter Queue (DLQ) tables for offline inspection without aborting the pipeline. |
| 5 | **Join Performance Diagnosis** | `🔴 Advanced` | When a join is the bottleneck: reading shuffle sizes, spill metrics, and task skew in Spark UI for join stages. |
| 6 | **Performance Troubleshooting Methodology** | `🔴 Advanced` | A structured diagnostic workflow for identifying lakehouse performance bottlenecks by analyzing Spark UI stages, query execution plans, shuffle spill, data skew, and cluster resource utilization. |
| 7 | **Serverless DLT** | `🔴 Advanced` | Serverless DLT executes Delta Live Tables pipelines on instant, fully managed serverless compute clusters operated within the Databricks cloud control plane. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟣 Architect: <b>🟣 Staff Architect (Level 400) (1 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Lakeflow Spark Declarative Pipelines (DLT)** | `🟣 Architect` | A declarative framework for building, testing, and operating reliable lakehouse ETL pipelines with managed orchestration, state, and data quality expectations. |

</details>

</details>

<details>
<summary>&nbsp;&nbsp;📂 <b>Section: Workspace, Serverless Compute & FinOps (50 Topics)</b> — <i>Click to expand functional domain</i></summary>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟢 Easy: <b>🟢 Easy (Level 100) (10 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **All-Purpose Cluster** | `🟢 Easy` | An All-Purpose Cluster is a shared interactive compute cluster designed for collaborative exploratory data analysis, interactive notebook development, and ad-hoc querying. |
| 2 | **Choosing Compute for Jobs** | `🟢 Easy` | The architectural decision framework for matching workloads to compute tiers: Serverless (zero startup delay, auto-managed), Classic Automated Jobs clusters (custom libraries), or All-Purpose clusters. |
| 3 | **Databricks Notebook** | `🟢 Easy` | A Databricks Notebook is a web-based interactive development document combining live executable code cells, interactive visualizations, and narrative markdown documentation. |
| 4 | **Databricks Repos** | `🟢 Easy` | Databricks Repos (now known as Git Folders) provides visual and programmatic Git version control integration directly inside the Databricks Workspace. |
| 5 | **DBFS (Databricks File System)** | `🟢 Easy` | DBFS (Databricks File System) is a distributed file system abstraction layer mounted over cloud object storage (S3 bucket, Azure container, GCS bucket) accessible across the workspace. |
| 6 | **dbutils** | `🟢 Easy` | Databricks Utilities (dbutils) is a built-in Python and Scala library that provides programmatic helper methods for file system operations, secret management, notebook workflows, and UI widgets. |
| 7 | **Magic Commands** | `🟢 Easy` | Magic Commands are special prefix directives (%python, %sql, %scala, %r, %sh, %fs) entered at the beginning of a notebook cell to alter the execution runtime or execute system utilities. |
| 8 | **Notebook Development Patterns** | `🟢 Easy` | Software engineering methodologies for Databricks notebooks, contrasting modular Python packages, Git Folders, and Databricks Connect against legacy `%run` script chaining. |
| 9 | **Secrets Management** | `🟢 Easy` | The secure credential management framework in Databricks (Secret Scopes backed by Azure Key Vault or encrypted storage) used to securely inject tokens, API keys, and connection strings at runtime. |
| 10 | **Serverless Compute Economics** | `🟢 Easy` | The FinOps cost and operational efficiency model of Databricks Serverless Compute, which eliminates idle capacity costs and cold-start latency through instant provisioning and per-workload DBU billing. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟡 Intermediate: <b>🟡 Intermediate (Level 200) (16 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **AI Functions for Data Engineers** | `🟡 Intermediate` | Built-in SQL functions (`ai_query()`, `ai_classify()`, `ai_extract()`) in Databricks SQL that invoke foundation LLMs directly within batch and streaming queries for automated data enrichment. |
| 2 | **Auto Loader** | `🟡 Intermediate` | Auto Loader is an optimized ingestion engine in Databricks that incrementally and efficiently ingests raw data files from cloud storage as they arrive without state tracking overhead. |
| 3 | **Change Data Feed (CDF)** | `🟡 Intermediate` | Change Data Feed (CDF) is a Delta Lake feature that captures and exposes row-level change events (inserts, updates, deletes) committed to a Delta table. |
| 4 | **Column Statistics & File Pruning** | `🟡 Intermediate` | Per-file min/max statistics collected for the first 32 columns by default (managed tables with Predictive Optimization choose columns intelligently). |
| 5 | **Databricks Feature Store** | `🟡 Intermediate` | The Databricks Feature Store is a centralized catalog that enables data scientists to discover, share, and reuse ML features with guaranteed online/offline consistency. |
| 6 | **Databricks Secret Scopes (Azure Key Vault)** | `🟡 Intermediate` | Secure credential storage backed by cloud key vaults, accessed in notebooks via `dbutils.secrets.get()`. |
| 7 | **Databricks Workspace File Sync (Repos)** | `🟡 Intermediate` | Bi-directional Git integration synchronizing branch code directly into Databricks workspace directories. |
| 8 | **Information Schema & Metadata Queries** | `🟡 Intermediate` | Querying `system.information_schema.tables`, `.columns`, `.table_privileges` to discover and audit catalog contents. |
| 9 | **Medallion Architecture on Databricks** | `🟡 Intermediate` | The Medallion Architecture is a lakehouse data design pattern that logically organizes data into Bronze (raw ingestion), Silver (cleaned/conformed), and Gold (curated business marts) quality layers. |
| 10 | **MLflow Model Registry** | `🟡 Intermediate` | The MLflow Model Registry provides a centralized model store, set of APIs, and UI to collaboratively manage the full lifecycle of MLflow models from development to production deployment. |
| 11 | **MLflow Tracking** | `🟡 Intermediate` | MLflow Tracking is an enterprise logging API and UI for recording machine learning experiment runs, hyperparameters, evaluation metrics, code versions, and serialized model artifacts. |
| 12 | **Monitoring, Alerting & SQL Alerts** | `🟡 Intermediate` | Automated operational monitoring and alert mechanisms in Databricks SQL that periodically evaluate query thresholds and dispatch notifications via Slack, PagerDuty, or Webhooks. |
| 13 | **Photon Engine** | `🟡 Intermediate` | Databricks' native, high-performance vectorized query execution engine written in C++ that leverages hardware SIMD acceleration and CPU cache locality to dramatically accelerate SQL and DataFrame workloads. |
| 14 | **Query Profile & Execution Plans** | `🟡 Intermediate` | Reading the DBSQL Query Profile (visual plan, statistics, bottleneck identification). |
| 15 | **Serverless vs Provisioned Auto-scaling Compute Economics** | `🟡 Intermediate` | The unit cost and utilization modeling comparing pay-per-second serverless execution runtimes against fixed, provisioned auto-scaling VM cluster pools. |
| 16 | **Service Principals & Managed Identity** | `🟡 Intermediate` | Using service principals for automated jobs instead of personal credentials. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🔴 Advanced: <b>🔴 Advanced (Level 300) (11 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **Databricks Asset Bundles (DABs)** | `🔴 Advanced` | Databricks Asset Bundles (DABs) is an Infrastructure-as-Code (IaC) framework that allows developers to define, test, and deploy entire Databricks projects using version-controlled YAML configurations. |
| 2 | **Databricks Asset Bundles Multi-Environment Promotion** | `🔴 Advanced` | A declarative Infrastructure-as-Code (IaC) packaging framework that defines jobs, pipelines, notebooks, and permissions as versioned YAML for automated CI/CD promotion. |
| 3 | **Databricks Auto Loader (cloudFiles)** | `🔴 Advanced` | An optimized streaming source format in Databricks (`cloudFiles`) that incrementally and efficiently processes billions of new data files arriving in cloud storage without state file explosion. |
| 4 | **Databricks Connect v2** | `🔴 Advanced` | Databricks Connect v2 is a client library built on Spark Connect that allows developers to run PySpark code from local IDEs directly against remote Databricks compute clusters. |
| 5 | **Databricks Genie Spaces (Lakehouse AI)** | `🔴 Advanced` | An AI-powered conversational interface in Databricks that allows non-technical business stakeholders to query Lakehouse Delta tables using natural language. |
| 6 | **Databricks Structured Streaming** | `🔴 Advanced` | Databricks Structured Streaming is a scalable stream processing engine built on Spark SQL that processes continuous data streams with micro-batch or continuous processing semantics. |
| 7 | **Delta Lake Schema Enforcement vs. Evolution** | `🔴 Advanced` | Schema Enforcement prevents data corruption by blocking appends that deviate from table schema, while Schema Evolution allows controlled addition of new columns during write operations. |
| 8 | **Delta Sharing** | `🔴 Advanced` | Delta Sharing is an open, cross-platform protocol for securely sharing live data tables, schemas, and AI models across organizations and clouds without data duplication. |
| 9 | **SCD Type 1 & Type 2 Patterns** | `🔴 Advanced` | Dimensional modeling techniques in Delta Lake that either overwrite current dimension attribute values (SCD Type 1) or preserve historical state transitions using effective date ranges and active flags (SCD Type 2). |
| 10 | **Serverless Compute (Databricks)** | `🔴 Advanced` | Serverless Compute is an on-demand, fully managed compute architecture in Databricks that boots clusters in seconds and scales resources instantaneously within Databricks-managed cloud accounts. |
| 11 | **Spark Connect** | `🔴 Advanced` | Spark Connect is a decoupled client-server architecture for Apache Spark that enables thin clients and IDEs to execute Spark DataFrame queries via a lightweight gRPC protocol. |

</details>

<details>
<summary>&nbsp;&nbsp;&nbsp;&nbsp;🟣 Architect: <b>🟣 Staff Architect (Level 400) (13 Topics)</b></summary>

| # | Topic / Concept | Difficulty | Architectural Definition & Core Principle |
|:---:|---|:---:|---|
| 1 | **CI/CD for Databricks with DABs** | `🟣 Architect` | The continuous integration and continuous deployment (CI/CD) architecture for Databricks using Databricks Asset Bundles (DABs) and Git automation pipelines. |
| 2 | **Databricks Asset Bundles (DABs) Infrastructure-as-Code** | `🟣 Architect` | A declarative Infrastructure-as-Code (IaC) standard for authoring, testing, deploying, and version-controlling Databricks data and AI projects. |
| 3 | **Databricks Asset Bundles (DABs) Multi-Target CI/CD** | `🟣 Architect` | The official Infrastructure-as-Code (IaC) standard for authoring, version-controlling, testing, and deploying Databricks Lakehouse workflows and pipelines across environments. |
| 4 | **Databricks Clean Rooms** | `🟣 Architect` | A secure multi-party collaboration environment allowing organizations to query shared datasets without exposing raw data. |
| 5 | **Databricks for Data Products** | `🟣 Architect` | The methodology and platform architecture for engineering, publishing, documenting, and monetizing curated data products on Databricks. |
| 6 | **Databricks Lakehouse vs Snowflake** | `🟣 Architect` | The enterprise architectural evaluation comparing Databricks' open, compute-flexible lakehouse platform against Snowflake's proprietary, SQL-centric cloud data warehouse platform. |
| 7 | **Databricks MLOps Platform** | `🟣 Architect` | An end-to-end Machine Learning Operations (MLOps) architecture on Databricks encompassing automated feature engineering, experiment tracking, model registry, and serverless model serving. |
| 8 | **Databricks Serverless Compute Architecture** | `🟣 Architect` | A cloud compute model where Databricks manages an instant warm pool of virtual machines in the Databricks compute plane, eliminating cluster startup latency. |
| 9 | **Databricks Serverless Compute Plane** | `🟣 Architect` | A fully managed, instant-start compute tier running inside Databricks-managed cloud subscriptions with pre-warmed container fleets and sub-second elasticity. |
| 10 | **Databricks Workflows vs Airflow** | `🟣 Architect` | The architectural decision framework comparing native Databricks Workflows with external general-purpose orchestrators like Apache Airflow. |
| 11 | **Disaster Recovery for Databricks** | `🟣 Architect` | The disaster recovery (DR) architecture for Databricks ensuring business continuity, minimal RPO, and near-zero RTO during regional cloud infrastructure outages. |
| 12 | **Petabyte-Scale ELT on Databricks** | `🟣 Architect` | The architectural principles and tuning strategies required to ingest, transform, and merge petabyte-scale data volumes on Databricks with predictable SLAs. |
| 13 | **Real-Time Lakehouse Architecture** | `🟣 Architect` | A unified lakehouse architecture that processes high-frequency real-time event streams (Kafka, Event Hubs) with sub-second to minute-level latency directly into Delta Lake. |

</details>

</details>

</details>

---

## 🌐 Ecosystem Interlinking
All curriculum topics are synchronized across the 14-repository Modern Data Engineering ecosystem:
- [Modern Data Engineer Hub](https://github.com/santoshjammi29/moderndataengineer) — Central edge web platform and 921-topic encyclopedia
- [Databricks Handbook](https://github.com/santoshjammi29/databricks-handbook) — Unity Catalog, Delta Lake 3.x, and Lakeflow
- [PySpark Handbook](https://github.com/santoshjammi29/pyspark-handbook) — Distributed compute & PySpark internals
- [SQL Handbook](https://github.com/santoshjammi29/sql-handbook) — Query engine optimization & relational internals
- [dbt Handbook](https://github.com/santoshjammi29/dbt-handbook) — Analytics engineering, contracts, and modeling
- [Streaming Handbook](https://github.com/santoshjammi29/streaming-handbook) — Event streaming, Kafka, and Flink
- [DataOps & CI/CD Handbook](https://github.com/santoshjammi29/dataops-cicd-handbook) — Airflow, orchestration, and infrastructure
- [System Design Handbook](https://github.com/santoshjammi29/data-system-design-handbook) — Distributed architecture and scalability
- [Interview Handbook](https://github.com/santoshjammi29/data-engineering-interview-handbook) — 20 Knowledge Pillars & architectural defense
- [Azure Cheat Sheet](https://github.com/santoshjammi29/azure-cheat-sheet) — Fabric, OneLake, and ADF enterprise blueprints
- [Security Handbook](https://github.com/santoshjammi29/security-handbook) — Zero-trust, IAM, and lakehouse governance
