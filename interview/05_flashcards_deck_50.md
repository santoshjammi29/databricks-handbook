# 🗂️ Databricks Technical Flashcard Deck (50 Active Recall Questions)

> **Coverage**: Modules 01 through 10 of The Databricks Handbook curriculum
> **Focus**: Rapid-fire architectural invariants, API mechanics, and performance rules

---

### 1. ACID Transactions

**Answer:**  
How Delta Lake guarantees atomicity, consistency, isolation, and durability on top of cloud object storage. Optimistic concurrency control. Why this matters vs. raw Parquet.

---

### 2. Transaction Log (`_delta_log`)

**Answer:**  
How the JSON-based transaction log tracks every change. What happens during reads (snapshot isolation). Log checkpoints every 100 commits. How the log enables time travel.

---

### 3. Time Travel & RESTORE

**Answer:**  
Querying previous versions with `VERSION AS OF` and `TIMESTAMP AS OF`. Restoring tables with `RESTORE`. When time travel stops working (after VACUUM). Retention configuration.

---

### 4. Schema Enforcement vs. Evolution

**Answer:**  
How `mergeSchema` and `overwriteSchema` work. What happens when a write doesn't match the schema. When to use enforcement vs. evolution in production.

---

### 5. Liquid Clustering

**Answer:**  
The recommended layout strategy for all new tables. How `CLUSTER BY` works. Replaces legacy partitioning and Z-ORDER. Clustering triggered on writes that exceed size thresholds. Why OPTIMIZE is still recommended for comprehensive clustering.

---

### 6. OPTIMIZE & File Compaction

**Answer:**  
Why small files kill read performance (causes: frequent appends, streaming micro-batches). How OPTIMIZE rewrites files and triggers Liquid Clustering. Auto Compaction as a lighter-weight alternative. When to rely on Predictive Optimization (#53) vs. running manually.

---

### 7. VACUUM & Storage Lifecycle

**Answer:**  
How VACUUM removes unreferenced files. The 7-day default retention and why lowering it breaks time travel. Interaction with concurrent readers. How Predictive Optimization automates VACUUM on managed tables.

---

### 8. Change Data Feed (CDF)

**Answer:**  
How to enable and query `table_changes()`. The `_change_type` column (insert, update_preimage, update_postimage, delete). Use cases: incremental downstream processing, audit trails, replication.

---

### 9. Deletion Vectors

**Answer:**  
Soft-delete markers that avoid rewriting files on DELETE, UPDATE, and MERGE. Enabled by default on new tables (rolling out). Physical deletion happens at OPTIMIZE/compaction. Compatibility considerations for external readers.

---

### 10. Delta Table Properties & Configuration

**Answer:**  
Key table properties every DE manages: `delta.enableChangeDataFeed`, `delta.enableDeletionVectors`, `delta.columnMapping.mode`, `delta.minReaderVersion`/`minWriterVersion`, `delta.checkpointInterval`. How these affect compatibility, performance, and feature availability. Checking and setting with `ALTER TABLE SET TBLPROPERTIES`.

---

### 11. Lazy Evaluation & Actions

**Answer:**  
Why transformations build a plan but don't execute. Which operations are actions (collect, count, write, show) vs. transformations (filter, select, join). Why this enables optimization.

---

### 12. Photon Engine

**Answer:**  
Native vectorized C++ query engine for SQL and DataFrame operations. Which operations benefit most (scans, filters, aggregations, joins). How to verify Photon is active in query plans. Automatically enabled on serverless compute.

---

### 13. Catalyst Optimizer & Query Plans

**Answer:**  
How Catalyst transforms logical plans into physical plans. Reading `EXPLAIN` output. Recognizing when the optimizer makes good vs. poor decisions.

---

### 14. Adaptive Query Execution (AQE)

**Answer:**  
How AQE adjusts plans at runtime based on actual data statistics. Three key optimizations: coalescing shuffle partitions, converting sort-merge joins to broadcast, optimizing skew joins. Enabled by default.

---

### 15. Shuffle Operations

**Answer:**  
What triggers a shuffle (groupBy, join, repartition, distinct). Why shuffles are expensive (serialization + network + disk I/O). Reading shuffle metrics in Spark UI.

---

### 16. Join Strategies

**Answer:**  
The three join types: broadcast hash join (small table fits in memory), sort-merge join (default for large-large), shuffle hash join (rare). The 10MB broadcast threshold (higher with Photon). Using `broadcast()` hints. How AQE dynamically converts at runtime.

---

### 17. Reading the Spark UI

**Answer:**  
The tabs that matter: Jobs, Stages, Tasks, SQL. What to look for: task duration variance, spill metrics, shuffle read/write sizes, scan statistics. Diagnosing bottlenecks from the UI.

---

### 18. Partitioning & Parallelism

**Answer:**  
How `spark.sql.shuffle.partitions` controls parallelism after shuffles. When to repartition vs. coalesce. The relationship between partition count, core count, and task parallelism. How to diagnose over/under-partitioning from Spark UI task metrics.

---

### 19. Data Skew: Detection & Mitigation

**Answer:**  
Recognizing skew in Spark UI (one task takes 10x longer). Why skew kills parallelism. Salting technique for skewed keys. AQE's automatic skew join optimization. When manual salting is still needed.

---

### 20. Memory Management & Spill

**Answer:**  
The unified memory model (execution + storage pool). What causes spill to disk. How to diagnose spill from Spark UI. Tuning `spark.sql.shuffle.partitions` and executor memory.

---

### 21. DataFrame API: Core Operations

**Answer:**  
select, filter, withColumn, groupBy, agg, join. Method chaining patterns. When to use DataFrame API vs. Spark SQL (same execution plan either way).

---

### 22. Temp Views & Global Temp Views

**Answer:**  
Scope: temp views live in the SparkSession, global temp views in `global_temp` and survive across notebooks on the same cluster. Neither persists across restarts.

---

### 23. Window Functions

**Answer:**  
ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, running totals with SUM OVER. Partition and ordering clauses. How these translate to physical execution (shuffles on partition keys).

---

### 24. Complex Types: ARRAY, STRUCT, MAP

**Answer:**  
Creating and querying nested structures. Exploding arrays with `explode()` and `posexplode()`. Struct field access with dot notation. Flattening deeply nested JSON.

---

### 25. Higher-Order Functions

**Answer:**  
`transform()`, `filter()`, `exists()`, `aggregate()` for array manipulation without exploding. When these outperform explode + groupBy. Real patterns: cleaning arrays, conditional filtering.

---

### 26. CTEs, PIVOT & Subqueries

**Answer:**  
Writing CTEs for readable multi-step queries. PIVOT for wide-format reshaping. Correlated vs. uncorrelated subqueries. How these map to physical plans.

---

### 27. UDFs vs. Native Functions

**Answer:**  
Why Python UDFs break Catalyst and force row-by-row execution. The 10-100x performance gap. Pandas UDFs (vectorized) as a middle ground. When a UDF is genuinely the right choice.

---

### 28. VARIANT Type

**Answer:**  
Storing semi-structured data (JSON) in a native binary format. Schema-on-read without parsing overhead. Querying with `:` path syntax. When VARIANT outperforms STRING or STRUCT columns for JSON data.

---

### 29. MERGE INTO & Upsert Patterns

**Answer:**  
The MERGE syntax for insert/update/delete in one statement. Clause ordering (MATCHED before NOT MATCHED). Write amplification and why MERGE rewrites entire files. Optimization: match on Liquid Clustering keys. How deletion vectors reduce cost.

---

### 30. Table Constraints & Generated Columns

**Answer:**  
CHECK constraints, NOT NULL, PRIMARY KEY (informational), FOREIGN KEY (informational). Generated columns with expressions (e.g., `date GENERATED ALWAYS AS CAST(timestamp AS DATE)`). How constraints enforce data quality at the write layer.

---

### 31. COPY INTO vs. Auto Loader

**Answer:**  
COPY INTO for ad-hoc/batch loads (idempotent, simpler). Auto Loader for continuous/streaming ingestion (exactly-once, scalable, schema evolution). Why Auto Loader is preferred for production.

---

### 32. File Formats in the Lakehouse

**Answer:**  
Why Parquet is the default (columnar, compressed, schema-embedded). Delta stores Parquet under the hood. When to use JSON, CSV, or Avro for ingestion sources. Schema-on-read vs. schema-on-write.

---

### 33. Volumes

**Answer:**  
Governed access to non-tabular files (CSVs, images, ML models) within Unity Catalog. Managed vs. external volumes. Using Volumes as landing zones and staging areas.

---

### 34. Auto Loader: File Discovery

**Answer:**  
File notification mode (cloud events, efficient at scale, requires setup) vs. directory listing mode (simpler, slower with millions of files). When to use each. Why Auto Loader is the default for production ingestion.

---

### 35. Auto Loader: Schema Evolution & Rescued Data

**Answer:**  
How schema inference works from the first batch. `cloudFiles.schemaEvolutionMode` options (addNewColumns, rescue, failOnNewColumns, none). The `_rescued_data` column for capturing mismatches instead of failing.

---

### 36. Multi-Hop Medallion Architecture

**Answer:**  
Bronze (raw, append-only), Silver (cleaned, deduplicated, typed), Gold (business aggregates). Why this pattern exists. When it's overkill. How each layer serves different consumers with different freshness requirements.

---

### 37. Incremental Processing Patterns

**Answer:**  
Processing only new/changed data. Techniques: Auto Loader (file-level), Change Data Feed (row-level), watermark-based (time-based), merge keys (hash-based). Cost vs. latency tradeoffs for each.

---

### 38. Lakehouse Federation

**Answer:**  
Querying external databases (PostgreSQL, MySQL, SQL Server, Snowflake) without copying data. Query pushdown optimization. Connection objects and security. When federation beats ETL and when it doesn't.

---

### 39. Idempotent Pipeline Design

**Answer:**  
Why every production pipeline must produce the same result when re-run. Databricks-specific techniques: MERGE with natural keys, `INSERT OVERWRITE` with `replaceWhere`, Auto Loader checkpoint recovery, Workflows retry policies. How streaming checkpoints provide built-in idempotency.

---

### 40. SCD Type 1 & Type 2 Patterns

**Answer:**  
SCD1 (overwrite current values) vs. SCD2 (maintain full history with effective dates). Implementing SCD2 with MERGE. Why Lakeflow Declarative Pipelines' `AUTO CDC INTO` (#75) is simpler for SCD2 at scale.

---

### 41. Structured Streaming Fundamentals

**Answer:**  
How Structured Streaming on Databricks uses Delta Lake as both source and sink. The `readStream`/`writeStream` API. Why Delta-to-Delta streaming is the most common production pattern. Integration with Auto Loader as a file source.

---

### 42. Triggers

**Answer:**  
`processingTime` (recurring micro-batches at fixed intervals). `availableNow` (process all available data then stop; replaces deprecated `once`). Choosing the right trigger for latency vs. cost.

---

### 43. Output Modes

**Answer:**  
Append (new rows only, default). Complete (full result table, aggregations only). Update (changed rows only). Which modes work with which operations and sinks.

---

### 44. Stream-Static Joins

**Answer:**  
Joining streaming DataFrames with batch DataFrames. Static side re-read each micro-batch. Use cases: enriching events with dimension data. Outer join limitations on the streaming side.

---

### 45. Windowed Aggregations

**Answer:**  
Tumbling windows (fixed, non-overlapping), sliding windows (fixed, overlapping), session windows (gap-based). Combining windows with watermarks for bounded state.

---

### 46. foreachBatch Pattern

**Answer:**  
Using `foreachBatch()` to apply arbitrary batch logic to each micro-batch. Use cases: writing to multiple sinks, MERGE operations in streaming, calling external APIs. Exactly-once considerations.

---

### 47. Streaming Tables in Lakeflow Pipelines

**Answer:**  
How streaming tables in Lakeflow Declarative Pipelines abstract away checkpoint and state management. The difference between streaming tables and raw Structured Streaming. When to use each approach.

---

### 48. Checkpointing & Exactly-Once

**Answer:**  
How checkpoint directories track processing state. Stream restart behavior (replay from checkpoint). Why checkpoint location must be stable and unique per query. Limitations of exactly-once guarantees.

---

### 49. Watermarks & Late Data

**Answer:**  
How `withWatermark()` bounds how late data can arrive. The tradeoff: longer watermark = more complete results but higher memory/state. How Spark drops state for expired windows.

---

### 50. Stream-Stream Joins

**Answer:**  
Joining two streaming DataFrames. Watermark requirements for state cleanup. Inner, left outer, and right outer join semantics. State management implications.

---
