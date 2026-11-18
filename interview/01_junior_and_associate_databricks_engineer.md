# 🎓 Databricks Interview Guide — Tier 1: Junior & Associate Databricks Engineer (Foundations)

> **Focus Areas**: Platform Architecture, Control Plane vs Compute Plane, Cluster Types, Medallion Architecture (Bronze/Silver/Gold), Delta Lake Fundamentals, dbutils utilities.
> **Target Audience**: Associate Data Engineers, Cloud Developers entering the Databricks ecosystem

---

### Q1.1: ACID Transactions (Delta Lake)

**Question & Concept Overview:**  
How Delta Lake guarantees atomicity, consistency, isolation, and durability on top of cloud object storage. Optimistic concurrency control. Why this matters vs. raw Parquet.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, ACID Transactions is an essential mechanism under Delta Lake. How Delta Lake guarantees atomicity, consistency, isolation, and durability on top of cloud object storage. Optimistic concurrency control. Why this matters vs. raw Parquet.

**Production Code / SQL Implementation:**
```python
-- ACID guarantees via optimistic concurrency control in Unity Catalog
BEGIN TRANSACTION;
INSERT INTO prod_catalog.gold.sales VALUES (101, 'Widget', 29.99, current_timestamp());
COMMIT;
```

**Key Invariants & Architectural Best Practices:**
- Delta Lake enforces ACID semantics on top of raw object storage (S3, ADLS Gen2, GCS).
- Uses Optimistic Concurrency Control (OCC) to detect write-write conflicts at commit time.
- Eliminates dirty reads and partial failures by committing changes atomically to the transaction log.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.2: Transaction Log (`_delta_log`) (Delta Lake)

**Question & Concept Overview:**  
How the JSON-based transaction log tracks every change. What happens during reads (snapshot isolation). Log checkpoints every 100 commits. How the log enables time travel.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Transaction Log (`_delta_log`) is an essential mechanism under Delta Lake. How the JSON-based transaction log tracks every change. What happens during reads (snapshot isolation). Log checkpoints every 100 commits. How the log enables time travel.

**Production Code / SQL Implementation:**
```python
-- Inspecting the transaction log commits in Unity Catalog
DESCRIBE HISTORY prod_catalog.gold.sales;
-- Reading raw log metadata via Unity Catalog Volumes
-- /Volumes/prod_catalog/gold/sales_volume/_delta_log/00000000000000000000.json
```

**Key Invariants & Architectural Best Practices:**
- _delta_log holds sequential JSON commit files tracking added, modified, and deleted Parquet files.
- Every 10 commits, Delta automatically writes a multi-part Parquet checkpoint file for fast state reconstruction.
- Snapshot isolation allows concurrent readers to query consistent states without acquiring file locks.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.3: Time Travel & RESTORE (Delta Lake)

**Question & Concept Overview:**  
Querying previous versions with `VERSION AS OF` and `TIMESTAMP AS OF`. Restoring tables with `RESTORE`. When time travel stops working (after VACUUM). Retention configuration.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Time Travel & RESTORE is an essential mechanism under Delta Lake. Querying previous versions with `VERSION AS OF` and `TIMESTAMP AS OF`. Restoring tables with `RESTORE`. When time travel stops working (after VACUUM). Retention configuration.

**Production Code / SQL Implementation:**
```sql
-- Querying historical snapshot
SELECT * FROM sales VERSION AS OF 12;
SELECT * FROM sales TIMESTAMP AS OF '2026-10-10 12:00:00';
-- Rollback accidental modification
RESTORE TABLE sales TO VERSION AS OF 11;
```

**Key Invariants & Architectural Best Practices:**
- Time travel queries read historical states defined by the transaction log and referenced Parquet files.
- RESTORE TABLE rolls back a table to a specific version or timestamp instantaneously.
- Historical time travel is bounded by the VACUUM retention window (default 7 days / 168 hours).

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.4: Lazy Evaluation & Actions (Spark Execution)

**Question & Concept Overview:**  
Why transformations build a plan but don't execute. Which operations are actions (collect, count, write, show) vs. transformations (filter, select, join). Why this enables optimization.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Lazy Evaluation & Actions is an essential mechanism under Spark Execution. Why transformations build a plan but don't execute. Which operations are actions (collect, count, write, show) vs. transformations (filter, select, join). Why this enables optimization.

**Production Code / SQL Implementation:**
```python
# Transformations build DAG; Action triggers execution
df_filtered = df.filter(df.amount > 100).select('customer_id', 'amount') # Lazy
total_records = df_filtered.count() # Action: triggers Catalyst & Spark jobs
```

**Key Invariants & Architectural Best Practices:**
- Transformations (map, filter, join, groupBy) are lazily recorded into a logical execution DAG.
- Actions (count, collect, write, show) trigger physical query compilation and distributed execution.
- Lazy evaluation enables whole-stage code generation, filter pushdown, and partition pruning optimizations.

**Certification Alignment:** `Databricks Associate Data Engineer`

---

### Q1.5: Photon Engine (Spark Execution)

**Question & Concept Overview:**  
Native vectorized C++ query engine for SQL and DataFrame operations. Which operations benefit most (scans, filters, aggregations, joins). How to verify Photon is active in query plans. Automatically enabled on serverless compute.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Photon Engine is an essential mechanism under Spark Execution. Native vectorized C++ query engine for SQL and DataFrame operations. Which operations benefit most (scans, filters, aggregations, joins). How to verify Photon is active in query plans. Automatically enabled on serverless compute.

**Production Code / SQL Implementation:**
```sql
-- Verify Photon in query plan
EXPLAIN FORMATTED SELECT sum(amount) FROM sales GROUP BY country;
-- Look for 'PhotonGroupingAgg' and 'PhotonScan'
```

**Key Invariants & Architectural Best Practices:**
- Photon is Databricks' vectorized query engine written from scratch in modern C++.
- Executes directly on CPU registers and SIMD instructions, bypassing JVM garbage collection and bytecode overhead.
- Enabled automatically on Serverless SQL Warehouses and modern Databricks runtimes.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.6: DataFrame API: Core Operations (SQL & DataFrames)

**Question & Concept Overview:**  
select, filter, withColumn, groupBy, agg, join. Method chaining patterns. When to use DataFrame API vs. Spark SQL (same execution plan either way).

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, DataFrame API: Core Operations is an essential mechanism under SQL & DataFrames. select, filter, withColumn, groupBy, agg, join. Method chaining patterns. When to use DataFrame API vs. Spark SQL (same execution plan either way).

**Production Code / SQL Implementation:**
```sql
-- Example for DataFrame API: Core Operations
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- select, filter, withColumn, groupBy, agg, join. Method chaining patterns. When to use DataFrame API vs. Spark SQL (same execution plan either way).
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.7: Temp Views & Global Temp Views (SQL & DataFrames)

**Question & Concept Overview:**  
Scope: temp views live in the SparkSession, global temp views in `global_temp` and survive across notebooks on the same cluster. Neither persists across restarts.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Temp Views & Global Temp Views is an essential mechanism under SQL & DataFrames. Scope: temp views live in the SparkSession, global temp views in `global_temp` and survive across notebooks on the same cluster. Neither persists across restarts.

**Production Code / SQL Implementation:**
```sql
-- Example for Temp Views & Global Temp Views
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- Scope: temp views live in the SparkSession, global temp views in `global_temp` and survive across notebooks on the same cluster. Neither persists across restarts.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.8: COPY INTO vs. Auto Loader (Data Ingestion)

**Question & Concept Overview:**  
COPY INTO for ad-hoc/batch loads (idempotent, simpler). Auto Loader for continuous/streaming ingestion (exactly-once, scalable, schema evolution). Why Auto Loader is preferred for production.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, COPY INTO vs. Auto Loader is an essential mechanism under Data Ingestion. COPY INTO for ad-hoc/batch loads (idempotent, simpler). Auto Loader for continuous/streaming ingestion (exactly-once, scalable, schema evolution). Why Auto Loader is preferred for production.

**Production Code / SQL Implementation:**
```sql
-- Example for COPY INTO vs. Auto Loader
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- COPY INTO for ad-hoc/batch loads (idempotent, simpler). Auto Loader for continuous/streaming ingestion (exactly-once, scalable, schema evolution). Why Auto Loader is preferred for production.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.9: File Formats in the Lakehouse (Data Ingestion)

**Question & Concept Overview:**  
Why Parquet is the default (columnar, compressed, schema-embedded). Delta stores Parquet under the hood. When to use JSON, CSV, or Avro for ingestion sources. Schema-on-read vs. schema-on-write.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, File Formats in the Lakehouse is an essential mechanism under Data Ingestion. Why Parquet is the default (columnar, compressed, schema-embedded). Delta stores Parquet under the hood. When to use JSON, CSV, or Avro for ingestion sources. Schema-on-read vs. schema-on-write.

**Production Code / SQL Implementation:**
```sql
-- Example for File Formats in the Lakehouse
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- Why Parquet is the default (columnar, compressed, schema-embedded). Delta stores Parquet under the hood. When to use JSON, CSV, or Avro for ingestion sources. Schema-on-read vs. schema-on-write.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.10: Volumes (Data Ingestion)

**Question & Concept Overview:**  
Governed access to non-tabular files (CSVs, images, ML models) within Unity Catalog. Managed vs. external volumes. Using Volumes as landing zones and staging areas.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Volumes is an essential mechanism under Data Ingestion. Governed access to non-tabular files (CSVs, images, ML models) within Unity Catalog. Managed vs. external volumes. Using Volumes as landing zones and staging areas.

**Production Code / SQL Implementation:**
```sql
-- Example for Volumes
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- Governed access to non-tabular files (CSVs, images, ML models) within Unity Catalog. Managed vs. external volumes. Using Volumes as landing zones and staging areas.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.11: Serverless Compute Economics (Performance & Cost)

**Question & Concept Overview:**  
How serverless pricing works (DBU-based, pay per query/task vs. per cluster-hour). When serverless is cheaper vs. classic (bursty workloads vs. sustained compute). Why serverless eliminates idle cluster waste.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Serverless Compute Economics is an essential mechanism under Performance & Cost. How serverless pricing works (DBU-based, pay per query/task vs. per cluster-hour). When serverless is cheaper vs. classic (bursty workloads vs. sustained compute). Why serverless eliminates idle cluster waste.

**Production Code / SQL Implementation:**
```sql
-- Example for Serverless Compute Economics
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Performance & Cost.
- How serverless pricing works (DBU-based, pay per query/task vs. per cluster-hour). When serverless is cheaper vs. classic (bursty workloads vs. sustained compute). Why serverless eliminates idle cluster waste.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.12: Three-Level Namespace (Unity Catalog & Governance)

**Question & Concept Overview:**  
`catalog.schema.table` hierarchy. How it maps to organizational structure. Default catalog and schema settings. Migrating from the legacy Hive Metastore.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Three-Level Namespace is an essential mechanism under Unity Catalog & Governance. `catalog.schema.table` hierarchy. How it maps to organizational structure. Default catalog and schema settings. Migrating from the legacy Hive Metastore.

**Production Code / SQL Implementation:**
```sql
-- Example for Three-Level Namespace
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Unity Catalog & Governance.
- `catalog.schema.table` hierarchy. How it maps to organizational structure. Default catalog and schema settings. Migrating from the legacy Hive Metastore.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.13: Python vs. SQL Pipeline Syntax (Lakeflow Declarative Pipelines)

**Question & Concept Overview:**  
SQL: `CREATE STREAMING TABLE`, `CREATE MATERIALIZED VIEW`. Python: `@table`, `@materialized_view`, `@temporary_view` decorators (from `pyspark.pipelines`). Old `import dlt` syntax still works. Choosing based on team skills.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Python vs. SQL Pipeline Syntax is an essential mechanism under Lakeflow Declarative Pipelines. SQL: `CREATE STREAMING TABLE`, `CREATE MATERIALIZED VIEW`. Python: `@table`, `@materialized_view`, `@temporary_view` decorators (from `pyspark.pipelines`). Old `import dlt` syntax still works. Choosing based on team skills.

**Production Code / SQL Implementation:**
```sql
-- Example for Python vs. SQL Pipeline Syntax
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Lakeflow Declarative Pipelines.
- SQL: `CREATE STREAMING TABLE`, `CREATE MATERIALIZED VIEW`. Python: `@table`, `@materialized_view`, `@temporary_view` decorators (from `pyspark.pipelines`). Old `import dlt` syntax still works. Choosing based on team skills.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.14: Choosing Compute for Jobs (Workflows, CI/CD & Operations)

**Question & Concept Overview:**  
Serverless compute as the default for new jobs (no cluster management, Photon auto-enabled). When to use job clusters instead (custom init scripts, GPU workloads, unsupported task types). Why all-purpose clusters are for development, not production. Instance pools for fast classic cluster startup.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Choosing Compute for Jobs is an essential mechanism under Workflows, CI/CD & Operations. Serverless compute as the default for new jobs (no cluster management, Photon auto-enabled). When to use job clusters instead (custom init scripts, GPU workloads, unsupported task types). Why all-purpose clusters are for development, not production. Instance pools for fast classic cluster startup.

**Production Code / SQL Implementation:**
```sql
-- Example for Choosing Compute for Jobs
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Workflows, CI/CD & Operations.
- Serverless compute as the default for new jobs (no cluster management, Photon auto-enabled). When to use job clusters instead (custom init scripts, GPU workloads, unsupported task types). Why all-purpose clusters are for development, not production. Instance pools for fast classic cluster startup.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.15: Secrets Management (Workflows, CI/CD & Operations)

**Question & Concept Overview:**  
Databricks Secret Scopes for credentials (API keys, database passwords). `dbutils.secrets.get()` in notebooks. Key-vault backed scopes (Azure Key Vault, AWS Secrets Manager). Why secrets must never be hardcoded.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Secrets Management is an essential mechanism under Workflows, CI/CD & Operations. Databricks Secret Scopes for credentials (API keys, database passwords). `dbutils.secrets.get()` in notebooks. Key-vault backed scopes (Azure Key Vault, AWS Secrets Manager). Why secrets must never be hardcoded.

**Production Code / SQL Implementation:**
```sql
-- Example for Secrets Management
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Workflows, CI/CD & Operations.
- Databricks Secret Scopes for credentials (API keys, database passwords). `dbutils.secrets.get()` in notebooks. Key-vault backed scopes (Azure Key Vault, AWS Secrets Manager). Why secrets must never be hardcoded.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.16: Parameterization: Widgets, Job Parameters, Task Values (Workflows, CI/CD & Operations)

**Question & Concept Overview:**  
`dbutils.widgets` for notebook parameters. Job parameters passed from Workflows. Task values for inter-task communication. Databricks SQL parameters for parameterized queries.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Parameterization: Widgets, Job Parameters, Task Values is an essential mechanism under Workflows, CI/CD & Operations. `dbutils.widgets` for notebook parameters. Job parameters passed from Workflows. Task values for inter-task communication. Databricks SQL parameters for parameterized queries.

**Production Code / SQL Implementation:**
```sql
-- Example for Parameterization: Widgets, Job Parameters, Task Values
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Workflows, CI/CD & Operations.
- `dbutils.widgets` for notebook parameters. Job parameters passed from Workflows. Task values for inter-task communication. Databricks SQL parameters for parameterized queries.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.17: Notebook Development Patterns (Workflows, CI/CD & Operations)

**Question & Concept Overview:**  
`%run` for shared utilities. `dbutils.notebook.run()` for orchestration. Magic commands (`%sql`, `%python`, `%md`). Notebook-scoped libraries. When to use notebooks vs. Python files in production.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Notebook Development Patterns is an essential mechanism under Workflows, CI/CD & Operations. `%run` for shared utilities. `dbutils.notebook.run()` for orchestration. Magic commands (`%sql`, `%python`, `%md`). Notebook-scoped libraries. When to use notebooks vs. Python files in production.

**Production Code / SQL Implementation:**
```sql
-- Example for Notebook Development Patterns
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Workflows, CI/CD & Operations.
- `%run` for shared utilities. `dbutils.notebook.run()` for orchestration. Magic commands (`%sql`, `%python`, `%md`). Notebook-scoped libraries. When to use notebooks vs. Python files in production.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.18: Shallow vs. Deep Clones (Architecture & Advanced Patterns)

**Question & Concept Overview:**  
SHALLOW CLONE (zero-copy, references source files) vs. DEEP CLONE (full copy, independent). Use cases: dev/test environments, table migration, disaster recovery snapshots, schema evolution testing.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Shallow vs. Deep Clones is an essential mechanism under Architecture & Advanced Patterns. SHALLOW CLONE (zero-copy, references source files) vs. DEEP CLONE (full copy, independent). Use cases: dev/test environments, table migration, disaster recovery snapshots, schema evolution testing.

**Production Code / SQL Implementation:**
```sql
-- Example for Shallow vs. Deep Clones
SELECT 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Architecture & Advanced Patterns.
- SHALLOW CLONE (zero-copy, references source files) vs. DEEP CLONE (full copy, independent). Use cases: dev/test environments, table migration, disaster recovery snapshots, schema evolution testing.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q1.19: Schema Enforcement vs. Evolution (Delta Lake)

**Question & Concept Overview:**  
How `mergeSchema` and `overwriteSchema` work. What happens when a write doesn't match the schema. When to use enforcement vs. evolution in production.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Schema Enforcement vs. Evolution is an essential mechanism under Delta Lake. How `mergeSchema` and `overwriteSchema` work. What happens when a write doesn't match the schema. When to use enforcement vs. evolution in production.

**Production Code / SQL Implementation:**
```python
# PySpark Schema Evolution on write
df_new.write \
  .format('delta') \
  .mode('append') \
  .option('mergeSchema', 'true') \
  .saveAsTable('sales')
```

**Key Invariants & Architectural Best Practices:**
- Schema enforcement rejects writes that contain unexpected columns or mismatched data types.
- option('mergeSchema', 'true') automatically appends new columns to the Delta table schema without rewriting files.
- overwriteSchema allows completely replacing schema during full table overwrites.

**Certification Alignment:** `Databricks Associate Data Engineer`

---

### Q1.20: Liquid Clustering (Delta Lake)

**Question & Concept Overview:**  
The recommended layout strategy for all new tables. How `CLUSTER BY` works. Replaces legacy partitioning and Z-ORDER. Clustering triggered on writes that exceed size thresholds. Why OPTIMIZE is still recommended for comprehensive clustering.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Liquid Clustering is an essential mechanism under Delta Lake. The recommended layout strategy for all new tables. How `CLUSTER BY` works. Replaces legacy partitioning and Z-ORDER. Clustering triggered on writes that exceed size thresholds. Why OPTIMIZE is still recommended for comprehensive clustering.

**Production Code / SQL Implementation:**
```sql
-- Next-generation layout optimization
CREATE TABLE sales_events (
  event_id BIGINT, event_date DATE, customer_id STRING, amount DOUBLE
) USING DELTA
CLUSTER BY (event_date, customer_id);

-- Dynamic clustering re-clustering
OPTIMIZE sales_events;
```

**Key Invariants & Architectural Best Practices:**
- Liquid Clustering uses Hilbert space-filling curves, eliminating rigid Hive directory partitioning.
- Prevents small file fragmentation and data skew on high-cardinality clustering keys.
- Allows altering clustering keys via ALTER TABLE CLUSTER BY without rewriting existing data files.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.21: OPTIMIZE & File Compaction (Delta Lake)

**Question & Concept Overview:**  
Why small files kill read performance (causes: frequent appends, streaming micro-batches). How OPTIMIZE rewrites files and triggers Liquid Clustering. Auto Compaction as a lighter-weight alternative. When to rely on Predictive Optimization (#53) vs. running manually.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, OPTIMIZE & File Compaction is an essential mechanism under Delta Lake. Why small files kill read performance (causes: frequent appends, streaming micro-batches). How OPTIMIZE rewrites files and triggers Liquid Clustering. Auto Compaction as a lighter-weight alternative. When to rely on Predictive Optimization (#53) vs. running manually.

**Production Code / SQL Implementation:**
```python
-- Compacting fragmented files into ~1GB files
OPTIMIZE sales;
-- Compacting specific partition or range
OPTIMIZE sales WHERE event_date >= '2026-10-01';
```

**Key Invariants & Architectural Best Practices:**
- OPTIMIZE performs bin-packing to coalesce small 1MB-10MB files into optimal ~1GB target files.
- Significantly reduces cloud object storage API calls and query scanning latency.
- Predictive Optimization in Unity Catalog automates OPTIMIZE runs without manual cron jobs.

**Certification Alignment:** `Databricks Associate Data Engineer`

---

### Q1.22: VACUUM & Storage Lifecycle (Delta Lake)

**Question & Concept Overview:**  
How VACUUM removes unreferenced files. The 7-day default retention and why lowering it breaks time travel. Interaction with concurrent readers. How Predictive Optimization automates VACUUM on managed tables.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, VACUUM & Storage Lifecycle is an essential mechanism under Delta Lake. How VACUUM removes unreferenced files. The 7-day default retention and why lowering it breaks time travel. Interaction with concurrent readers. How Predictive Optimization automates VACUUM on managed tables.

**Production Code / SQL Implementation:**
```python
-- Storage hygiene: removing tombstoned Parquet files past 7 days
VACUUM sales RETAIN 168 HOURS;
-- Dry run check
VACUUM sales DRY RUN;
```

**Key Invariants & Architectural Best Practices:**
- VACUUM permanently purges unreferenced physical data files that were marked for deletion by UPDATE/DELETE/OPTIMIZE.
- Enforces a default 7-day (168-hour) safety threshold to prevent deleting files needed by concurrent active readers.
- Disabling retention safety (spark.databricks.delta.vacuum.parallelDelete.enabled) is strongly discouraged in production.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q1.23: Change Data Feed (CDF) (Delta Lake)

**Question & Concept Overview:**  
How to enable and query `table_changes()`. The `_change_type` column (insert, update_preimage, update_postimage, delete). Use cases: incremental downstream processing, audit trails, replication.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Change Data Feed (CDF) is an essential mechanism under Delta Lake. How to enable and query `table_changes()`. The `_change_type` column (insert, update_preimage, update_postimage, delete). Use cases: incremental downstream processing, audit trails, replication.

**Production Code / SQL Implementation:**
```sql
-- Enable Change Data Feed
ALTER TABLE sales SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
-- Querying CDC events
SELECT * FROM table_changes('sales', 2, 5);
```

**Key Invariants & Architectural Best Practices:**
- CDF exposes row-level changes with metadata: _change_type (insert, update_preimage, update_postimage, delete).
- Powers downstream incremental ETL pipelines and real-time Kafka/event-driven replication.
- Stores change logs inside _delta_log or inline within committed data files.

**Certification Alignment:** `Databricks Professional Data Engineer`

---

### Q1.24: Deletion Vectors (Delta Lake)

**Question & Concept Overview:**  
Soft-delete markers that avoid rewriting files on DELETE, UPDATE, and MERGE. Enabled by default on new tables (rolling out). Physical deletion happens at OPTIMIZE/compaction. Compatibility considerations for external readers.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Deletion Vectors is an essential mechanism under Delta Lake. Soft-delete markers that avoid rewriting files on DELETE, UPDATE, and MERGE. Enabled by default on new tables (rolling out). Physical deletion happens at OPTIMIZE/compaction. Compatibility considerations for external readers.

**Production Code / SQL Implementation:**
```sql
-- Deletion Vectors enable soft-deletes
ALTER TABLE sales SET TBLPROPERTIES (delta.enableDeletionVectors = true);
-- Soft delete modifies DV bitmap without rewriting the full Parquet file
DELETE FROM sales WHERE status = 'CANCELLED';
```

**Key Invariants & Architectural Best Practices:**
- Deletion Vectors use Roaring Bitmaps to record deleted row indices within an existing Parquet file.
- Turns write-heavy row deletes and MERGE updates into lightweight bitmap appends, cutting write amplification.
- Physical file rewriting is deferred until OPTIMIZE compaction is executed.

**Certification Alignment:** `Databricks Professional Data Engineer`

---

### Q1.25: Catalyst Optimizer & Query Plans (Spark Execution)

**Question & Concept Overview:**  
How Catalyst transforms logical plans into physical plans. Reading `EXPLAIN` output. Recognizing when the optimizer makes good vs. poor decisions.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Catalyst Optimizer & Query Plans is an essential mechanism under Spark Execution. How Catalyst transforms logical plans into physical plans. Reading `EXPLAIN` output. Recognizing when the optimizer makes good vs. poor decisions.

**Production Code / SQL Implementation:**
```python
# Reading Catalyst Optimizer Physical Plan
df.explain(extended=True)
# Catalyst: Parsed -> Analyzed -> Optimized -> Physical
```

**Key Invariants & Architectural Best Practices:**
- Catalyst pipeline has 4 phases: Analysis (catalog resolution), Logical Optimization, Physical Planning, and Code Generation.
- Performs cost-based optimizations (CBO) including projection pruning, constant folding, and predicate pushdown.
- Physical planning selects optimal join algorithms based on data size, broadcast thresholds, and sorting.

**Certification Alignment:** `Databricks Professional Data Engineer`

---
