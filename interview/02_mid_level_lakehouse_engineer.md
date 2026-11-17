# 🎓 Databricks Interview Guide — Tier 2: Mid-Level Lakehouse Engineer (Implementation)

> **Focus Areas**: Auto Loader (`cloudFiles`), Delta Live Tables (DLT), Deletion Vectors, Liquid Clustering, Delta CDF, Unity Catalog 3-Level Namespace, and DABs.

---

### Q2.1: How does Auto Loader (`cloudFiles`) work, and what are its two file discovery modes?

**Answer:**  
Auto Loader incrementally ingests new files arriving in cloud storage into Delta Lake using Structured Streaming:
1. **Incremental Directory Listing (Default)**:
   - Scans the directory using lexicographical file sorting and timestamp comparisons.
   - Extremely cost-effective for storage accounts with fewer than a few hundred thousand files.
2. **File Notification Mode**:
   - Automatically configures cloud messaging queues (AWS SQS/SNS or Azure Event Grid + Storage Queue).
   - When a new file lands, an event notification is published to the queue; Auto Loader reads directly from the queue.
   - Highly recommended for petabyte-scale storage accounts with millions of files to eliminate slow directory `LIST` operations.

**Key Features**:
- **`rescuedDataColumn`**: Preserves unparseable or unexpected data types safely in a JSON column (`_rescued_data`).
- **`cloudFiles.schemaEvolutionMode = "addNewColumns"`**: Automatically adds new columns upstream into the Delta schema.

---

### Q2.2: How does Delta Lake's ACID transaction log (`_delta_log`) work under the hood?

**Answer:**  
The `_delta_log` directory maintains the single source of truth for table state:
1. **Atomic Commit Files (`000000.json`, `000001.json`)**: Every transaction writes a numbered JSON file containing discrete actions:
   - `add`: New Parquet file added with column min/max statistics for data skipping.
   - `remove`: Parquet file logically tombstoned (marked invalid).
   - `metaData`: Schema changes or table properties.
   - `protocol`: Minimum reader/writer protocol version.
2. **Compacted Checkpoints (`000010.checkpoint.parquet`)**: Every 10 commits, Delta aggregates all active state actions into a columnar Parquet file.
3. **State Reconstruction**: Readers load the latest checkpoint Parquet file plus any trailing JSON commits to build the in-memory active file set, bypassing slow cloud storage directory listings.

---

### Q2.3: What are Deletion Vectors (Merge-on-Read), and how do they improve DML write performance over Copy-on-Write?

**Answer:**  
- **Copy-on-Write (CoW)**: Updating or deleting a single row in a 500 MB Parquet file requires reading the entire 500 MB, rewriting the unaffected rows and new row into a brand-new 500 MB file, and tombstoning the old file.
- **Merge-on-Read with Deletion Vectors (MoR)**:
  - The existing 500 MB Parquet file remains completely untouched.
  - Delta writes a small roaring bitmap (a `.dv` file, typically a few kilobytes) that records the exact physical row offsets that were invalidated.
  - For updates, Delta writes the small `.dv` file plus a small Parquet file containing only the updated rows.
  - **Result**: DML write speed improves by $10\times$ to $100\times$, write amplification is eliminated, and concurrent writes to the same Parquet file succeed via Row-Level Concurrency (RLC).

---

### Q2.4: Compare Liquid Clustering (`CLUSTER BY`) against Hive directory partitioning and Z-Ordering.

**Answer:**  
- **Hive Partitioning (`PARTITIONED BY`)**: Physically creates directory trees (`year=2026/month=11/`). Causes severe small file problems on high-cardinality columns (e.g., UUIDs or timestamps) and changing keys requires rewriting all data.
- **Z-Ordering (`ZORDER BY`)**: Re-sorts data along multi-dimensional space-filling curves within files, but requires a full table rewrite on each optimize and is not incremental.
- **Liquid Clustering (`CLUSTER BY`)**:
  - Uses multi-dimensional Hilbert-curve algorithms that incrementally cluster only newly appended data during `OPTIMIZE`.
  - Keys can be redefined instantly via `ALTER TABLE ... CLUSTER BY (...)` without rewriting existing files.
  - Automatically avoids the small file problem by maintaining target file sizes between 256 MB and 1 GB.

---

### Q2.5: What are Delta Live Tables (DLT), and what is the difference between a Streaming Table and a Materialized View?

**Answer:**  
DLT is a declarative framework for building reliable lakehouse ETL pipelines:
- **Streaming Table (`@dlt.table`)**:
  - Ingests data incrementally using an append-only stream.
  - Processes only newly arrived rows from the source; ideal for raw bronze ingestion and event streams.
- **Materialized View (`@dlt.view` / `@dlt.table` batch)**:
  - Precomputes query results according to its defining SQL query.
  - Automatically computes incremental updates or refreshes to match the current state of upstream tables; ideal for Silver conformance and Gold business aggregations.
- **Data Quality Expectations**:
  - `@dlt.expect("valid_id", "id IS NOT NULL")`: Logs quality metrics in event log.
  - `@dlt.expect_or_drop("valid_status", "status IN ('PAID', 'PENDING')")`: Drops invalid rows.
  - `@dlt.expect_or_fail("valid_amount", "amount >= 0")`: Fails the pipeline immediately.
