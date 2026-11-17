# 🎓 Databricks Interview Guide — Tier 1: Junior & Associate Engineer (Foundations)

> **Focus Areas**: Platform Architecture, Split-Plane Security, Cluster Types, Delta Lake Basics vs. Parquet, `dbutils`, Medallion Architecture, and Core PySpark.

---

### Q1.1: What is the split-plane cloud architecture of Databricks, and what is the difference between the Control Plane and Compute Plane?

**Answer:**  
Databricks separates platform operations into two distinct security planes:
1. **Control Plane (Databricks-Managed)**:
   - Resides in the Databricks cloud subscription.
   - Manages the Web UI, notebook orchestration, Lakeflow Jobs scheduling, Cluster Manager, and Unity Catalog metadata.
   - Notebook command definitions and query texts are encrypted at rest and in transit.
2. **Compute Plane (Classic vs. Serverless)**:
   - The execution environment where Apache Spark, Photon, and Python processes run.
   - In **Classic Compute**, VMs run inside the customer's cloud VNet/VPC.
   - In **Serverless Compute**, workloads run on pre-warmed container pools managed securely by Databricks with private endpoints to customer storage.
3. **Storage Plane (Customer-Owned)**:
   - Data never lives in Databricks; persistent Parquet/Delta files reside in the customer's cloud storage (ADLS Gen2, AWS S3, GCS).

---

### Q1.2: What are the primary differences between All-Purpose Compute, Job Compute, and SQL Warehouses?

**Answer:**  
- **All-Purpose Compute**: Interactive clusters used by developers for ad-hoc exploration, notebook development, and debugging. They can be shared among multiple users. They carry the highest DBU rate ($2\times$ to $3\times$ higher than Job Compute) and should never run scheduled production jobs.
- **Job Compute**: Ephemeral clusters created automatically when a Lakeflow Job runs and terminated immediately when the job finishes. They carry the lowest DBU rate, designed for automated, cost-efficient production pipelines.
- **SQL Warehouses**: Optimized elastic compute specifically for ANSI SQL queries, BI dashboards, and ad-hoc analytics. Powered by the Photon engine and Intelligent Workload Management (IWM). Serverless SQL Warehouses start in 2–4 seconds and scale to zero rapidly.

---

### Q1.3: What is Delta Lake, and how does it fundamentally differ from standard Apache Parquet?

**Answer:**  
Apache Parquet is an immutable columnar storage format with no ACID guarantees, no transaction log, and no mutation capabilities.  
Delta Lake is an open-source storage framework built *atop* Apache Parquet that adds:
1. **ACID Transactions**: Managed via the `_delta_log` directory recording atomic commits in JSON.
2. **DML Mutations**: Native `UPDATE`, `DELETE`, and `MERGE INTO` operations.
3. **Time Travel**: Point-in-time historical data query and version auditing.
4. **Schema Enforcement & Evolution**: Rejection of bad columns (`enforcement`) or controlled addition (`mergeSchema`).
5. **Compaction & Pruning**: Built-in `OPTIMIZE`, Liquid Clustering (`CLUSTER BY`), and Deletion Vectors (Merge-on-Read).

---

### Q1.4: Explain the Medallion Architecture (Bronze → Silver → Gold) and the responsibilities of each layer.

**Answer:**  
- **🥉 Bronze Layer (Raw Ingestion)**:
  - Append-only raw data preserved in its original source structure.
  - Adds technical metadata columns (`_ingest_ts`, `_source_file`).
  - No destructive business transformations; allows complete data replay if downstream business logic changes.
- **🥈 Silver Layer (Cleaned & Conformed)**:
  - Validates schemas, deduplicates keys, standardizes timestamps, and handles null/corrupted fields.
  - Implements Slowly Changing Dimensions (SCD Type 1 & 2).
  - Represents the single source of truth for enterprise domain entities.
- **🥇 Gold Layer (Curated Business Marts)**:
  - Kimball dimensional star schemas (Facts & Dimensions) and aggregated metrics.
  - Optimized for sub-second BI reporting, executive dashboards, and ML feature stores.

---

### Q1.5: What is `dbutils`, and what are its primary modules in Databricks?

**Answer:**  
`dbutils` (Databricks Utilities) is a built-in helper library providing programmatic access to the workspace environment:
- **`dbutils.fs`**: Interacting with the filesystem (`ls`, `cp`, `mv`, `rm`, `head`, `mkdirs`).
- **`dbutils.secrets`**: Secure retrieval of credentials (`dbutils.secrets.get(scope, key)`) without exposing plaintext secrets in code.
- **`dbutils.widgets`**: Parameterizing notebooks with dropdowns, text boxes, and combo boxes (`get`, `text`, `dropdown`).
- **`dbutils.notebook`**: Chaining notebooks and returning exit values (`run`, `exit`).
- **`dbutils.jobs.taskValues`**: Setting and retrieving dynamic parameters across DAG tasks in Lakeflow Jobs.
