# 🗂️ Databricks Technical Flashcard Deck (50 Active Recall Questions)

> **Coverage**: Modules 01 through 10 of The Databricks Handbook curriculum
> **Focus**: Rapid-fire architectural invariants, API mechanics, and performance rules

---

### 1. ACID Transactions

**Answer:**  
Delta Lake guarantees ACID transactions on cloud object storage via Optimistic Concurrency Control (OCC) and atomic log commits inside `_delta_log/`: every write stages Parquet data files first and commits only by atomically writing the next numbered JSON log file (`00000N.json`), preventing readers from seeing partial writes, corrupt directories, or inconsistent multi-file updates that plague raw Parquet.

---

### 2. Transaction Log (`_delta_log`)

**Answer:**  
Delta Lake tracks every table mutation as ordered JSON commit files (`000000.json`, `000001.json`, ...) inside `_delta_log/` and periodically compacts log state into Parquet checkpoint files (every `10` commits by default in OSS Delta, customizable via `delta.checkpointInterval`, alongside V2 sidecar/UUID checkpoints). Readers attain Snapshot Isolation by reconstructing the file list (`AddFile` / `RemoveFile` actions) as of the table version pinned at query start, which simultaneously enables repeatable reads and Time Travel.

---

### 3. Time Travel & RESTORE

**Answer:**  
Previous table states can be queried declaratively with `SELECT * FROM tbl VERSION AS OF 12` or `TIMESTAMP AS OF '2026-11-01T00:00:00Z'`, and rolled back in-place using `RESTORE TABLE tbl TO VERSION AS OF 12`. Time Travel stops functioning once `VACUUM` physically deletes historical Parquet files or `_delta_log` entries age past `delta.logRetentionDuration` (default `INTERVAL 30 DAYS`), while unreferenced data files default to `delta.deletedFileRetentionDuration` (`INTERVAL 7 DAYS`).

---

### 4. Schema Enforcement vs. Evolution

**Answer:**  
By default, Delta rejects incompatible appends whose column names or types differ from the target table schema (Schema Enforcement). Setting `.option("mergeSchema", "true")` (or `spark.databricks.delta.schema.autoMerge.enabled = true`) allows additive nullable columns during writes, whereas `.option("overwriteSchema", "true")` replaces the target schema only on complete overwrites; production pipelines keep enforcement enabled and restrict `mergeSchema` to controlled Bronze/Silver ingestion boundaries.

---

### 5. Liquid Clustering

**Answer:**  
Liquid Clustering (`CLUSTER BY (col1, col2)`) replaces rigid directory partitioning (`PARTITIONED BY`) and `ZORDER BY` with dynamic Hilbert-curve multi-dimensional clustering stored incrementally in Parquet files without rewriting untouched data. You can alter keys zero-cost via `ALTER TABLE tbl CLUSTER BY (new_key)` and use `CLUSTER BY AUTO` so Databricks Predictive Optimization selects and incrementally compacts optimal clustering columns based on actual query predicates.

---

### 6. OPTIMIZE & File Compaction

**Answer:**  
Streaming micro-batches and frequent small appends degrade read throughput via S3/ADLS object-listing latency and Parquet footer overhead (the "small files problem"). Running `OPTIMIZE tbl` bin-packs small Parquet files into uniform target sizes (~128 MB–1 GB depending on adaptive heuristics) and applies clustering layout, while table properties `delta.autoOptimize.autoCompact` and `delta.autoOptimize.optimizeWrite` mitigate fragmentation at write time before Predictive Optimization compacts managed Unity Catalog tables automatically.

---

### 7. VACUUM & Storage Lifecycle

**Answer:**  
`VACUUM tbl RETAIN 168 HOURS` physically deletes Parquet files no longer referenced by the current snapshot whose deletion timestamp exceeds the 7-day (`168`-hour) safety threshold. Lowering retention below `168` hours requires disabling the safety guard (`spark.databricks.delta.retentionDurationCheck.enabled = false`) and risks aborting long-running concurrent readers or breaking Time Travel; Predictive Optimization runs `VACUUM` automatically on UC managed tables.

---

### 8. Change Data Feed (CDF)

**Answer:**  
Enabling `TBLPROPERTIES (delta.enableChangeDataFeed = true)` emits row-level change metadata queryable via `table_changes('tbl', start_version, end_version)` or `.option("readChangeFeed", "true")` streaming reads. Returned rows include `_change_type` (`insert`, `update_preimage`, `update_postimage`, `delete`), `_commit_version`, and `_commit_timestamp`, enabling efficient incremental Silver-to-Gold propagation, SCD pipelines, and external warehouse replication without full table scans.

---

### 9. Deletion Vectors

**Answer:**  
Deletion Vectors (`delta.enableDeletionVectors = true`, enabled by default on Databricks Runtime 14.1+ / UC managed tables) accelerate `DELETE`, `UPDATE`, and `MERGE` up to 10x by recording row-level Roaring bitmap tombstones instead of copying entire Parquet data files (Merge-on-Read semantics). Masked rows are physically purged during subsequent `OPTIMIZE` or `REORG TABLE ... APPLY (PURGE)`, and external engines require Reader v3 or Delta UniForm metadata generation.

---

### 10. Delta Table Properties & Configuration

**Answer:**  
Production Delta tables are tuned via `ALTER TABLE tbl SET TBLPROPERTIES (...)` using properties such as `delta.enableDeletionVectors`, `delta.enableChangeDataFeed`, `delta.columnMapping.mode = 'name'` (for zero-rewrite `RENAME`/`DROP COLUMN`), `delta.checkpointInterval`, `delta.deletedFileRetentionDuration`, and `delta.minReaderVersion` / `delta.minWriterVersion`. Upgrading protocol versions or enabling table features records permanent protocol entries in `_delta_log/`, which older external readers may not support.

---

### 11. Lazy Evaluation & Actions

**Answer:**  
Spark transformations (`filter`, `select`, `withColumn`, `join`) append logical operators to a Catalyst lineage DAG without triggering cluster computation. Execution starts only when an action (`count`, `collect`, `show`, `write`, `foreachBatch`) is invoked, allowing Catalyst to fuse filters, prune unused columns, push predicates into Parquet/Delta footers, and collapse stages before scheduling tasks across executors.

---

### 12. Photon Engine

**Answer:**  
Photon is Databricks' native C++ vectorized execution engine running off-JVM to process columnar memory batches via SIMD instructions, eliminating JVM garbage collection overhead on wide scans, hash joins, and aggregations. Enabled automatically on Databricks SQL Serverless Warehouses and toggleable on All-Purpose/Job clusters (`photon_enabled = true`), Photon activation appears directly in the Spark UI SQL DAG and `EXPLAIN` plan as `PhotonScan`, `PhotonFilter`, and `PhotonGroupingAgg` operators.

---

### 13. Catalyst Optimizer & Query Plans

**Answer:**  
Catalyst translates every SQL query and DataFrame chain through four pipeline stages: Analysis (resolving columns/types via Unity Catalog), Logical Optimization (predicate pushdown, constant folding, projection pruning), Physical Planning (cost-based join and scan selection), and Whole-Stage Codegen. Inspecting `df.explain("formatted")` exposes unnecessary `Exchange` shuffles, `BroadcastNestedLoopJoin` fallbacks, or missing `PushedFilters` before costly production runs.

---

### 14. Adaptive Query Execution (AQE)

**Answer:**  
Adaptive Query Execution (`spark.sql.adaptive.enabled = true`, enabled by default since Spark 3.0) re-optimizes the physical execution plan at stage shuffle boundaries using runtime byte/partition statistics. AQE automatically executes three key optimizations: coalescing tiny post-shuffle partitions (`coalescePartitions.enabled`), converting Sort-Merge Joins to Broadcast Hash Joins when runtime filtered inputs shrink below threshold, and splitting skewed partitions (`skewJoin.enabled`).

---

### 15. Shuffle Operations

**Answer:**  
Wide transformations (`groupBy`, `join`, `repartition`, `distinct`, window `PARTITION BY`) trigger a shuffle boundary (`Exchange`) that hashes, serializes, writes shuffle blocks to local SSD, and streams partitions across executor network links. Shuffles dominate latency and spill risk; Spark UI tracks their cost under **Shuffle Write** (upstream map stage) and **Shuffle Read / Remote Bytes** (downstream reduce stage).

---

### 16. Join Strategies

**Answer:**  
Spark selects among Broadcast Hash Join (BHJ — duplicates small relation <= `10 MB` default via `spark.sql.autoBroadcastJoinThreshold` to avoid shuffles), Sort-Merge Join (SMJ — sorts and shuffles both large inputs; default for large tables), Shuffle Hash Join (SHJ — hashes smaller shuffled side without full sort), and fallback Broadcast Nested Loop Join. Hints (`F.broadcast(dim)`) and AQE runtime join conversion eliminate multi-terabyte Sort-Merge shuffles cleanly.

---

### 17. Reading the Spark UI

**Answer:**  
Triage bottlenecks across four Spark UI tabs: **Jobs/Stages** (spot straggler tasks where Max Task Duration >> Median Duration, indicating data skew or GC), **Task Metrics** (inspect `Shuffle Read/Write`, `Spill (Memory)` vs. non-zero `Spill (Disk)`), **SQL / DataFrame** (examine DAG node row counts and Photon coverage), and **Executors** (identify dead containers, Exit Code `137` OOM kills, and JVM GC time > 10% of task time).

---

### 18. Partitioning & Parallelism

**Answer:**  
Post-shuffle parallelism defaults to `spark.sql.shuffle.partitions = 200` (or `auto` on Databricks Photon clusters) and should target roughly `128 MB` compressed data per partition across `2x–3x` total cluster vCPUs. Use `repartition(n, key)` to evenly redistribute or increase partitions via a full shuffle, whereas `coalesce(n)` narrows partitions without shuffling (though over-using `coalesce` upstream can throttle parallelism across entire stages).

---

### 19. Data Skew: Detection & Mitigation

**Answer:**  
Data skew occurs when one key (`NULL`, default sentinel, or hot tenant ID) concentrates disproportionate rows into one partition, leaving 199 tasks finished while 1 task stalls or OOMs on disk spill. AQE Skew Join automatically splits large skewed partitions during Sort-Merge Joins; when joining outside AQE or aggregating (`COUNT DISTINCT` / `groupBy`) heavily skewed keys, apply a two-phase salt (`concat(key, '_', floor(rand() * N))`) followed by partial-to-global aggregation.

---

### 20. Memory Management & Spill

**Answer:**  
Spark shares JVM heap inside a unified pool (`spark.memory.fraction = 0.6` default) divided dynamically between Execution Memory (shuffle buffers, sort arrays, hash joins) and Storage Memory (cached DataFrames). When execution tasks exceed their memory share, Spark serializes sort/hash structures to local SSD (**Spill Memory -> Spill Disk**), degrading throughput severely; fix spill by eliminating wide skew, filtering early, raising `spark.sql.shuffle.partitions`, or choosing memory-optimized workers.

---

### 21. DataFrame API: Core Operations

**Answer:**  
Chained transformations (`select`, `filter`/`where`, `withColumn`, `groupBy().agg()`, `join`) compile down to the exact same Catalyst Logical Plan and Tungsten/Photon physical plan as equivalent Spark SQL strings. Prefer DataFrame APIs for programmatic modular pipelines, strong parameterization, and unit testing with `chispa`, and reserve multi-line Spark SQL views for analytics readability and DBSQL dashboard interoperability.

---

### 22. Temp Views & Global Temp Views

**Answer:**  
`df.createOrReplaceTempView("v")` binds a non-materialized logical view strictly to the active `SparkSession` within the current notebook/job, whereas `createOrReplaceGlobalTempView("gv")` stores it inside the `global_temp` database shared across notebooks attached to the same multi-notebook cluster. Neither view persists metadata or data across cluster termination; use Unity Catalog managed tables or SQL views (`CREATE VIEW`) for durable cross-session sharing.

---

### 23. Window Functions

**Answer:**  
SQL window functions (`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, cumulative `SUM() OVER (...)`) compute rankings and moving metrics without collapsing row grain. Catalyst maps each `PARTITION BY ... ORDER BY ...` clause to a `Window` physical operator preceded by an `Exchange` shuffle on the partition key and a partition sort; omitting `PARTITION BY` forces all cluster data onto a single executor partition and causes Driver/Executor OOM.

---

### 24. Complex Types: ARRAY, STRUCT, MAP

**Answer:**  
Spark handles hierarchical schemas natively with `ARRAY<T>`, `STRUCT<field:T>`, and `MAP<K,V>`: traverse struct attributes directly via dot notation (`customer.address.zip`), iterate or flatten arrays using `F.explode` / `F.explode_outer` (preserving null/empty arrays) or `F.posexplode` (keeping element ordinal index), and parse raw JSON strings deterministically using `F.from_json(col, schema)` instead of fragile regex extraction.

---

### 25. Higher-Order Functions

**Answer:**  
Higher-order SQL/DataFrame functions (`transform`, `filter`, `exists`, `forall`, `aggregate`) execute lambda transformations inline inside each `ARRAY` element without invoking `explode` + `groupBy` + `collect_list`. Avoiding array explosion eliminates intermediate row multiplication, network shuffles, and object-reordering bugs while enabling single-pass vectorized array sanitization (`FILTER(items, x -> x.price > 0)`).

---

### 26. CTEs, PIVOT & Subqueries

**Answer:**  
Common Table Expressions (`WITH cte AS (...)`) decompose complex analytical SQL into readable steps that Catalyst inlines and optimizes holistically (unless referenced multiple times where caching or temp Delta tables may prevent recomputation). `PIVOT` transposes long key-value aggregates into fixed wide columns, and Catalyst automatically rewrites most correlated `EXISTS`/`IN` subqueries into fast Broadcast or Sort-Merge semi-joins.

---

### 27. UDFs vs. Native Functions

**Answer:**  
Standard row-by-row Python UDFs serialize JVM rows across Py4J sockets to single-threaded Python worker processes, disabling Photon vectorization and Catalyst predicate pushdown (often 10x–100x slower). Always favor native `pyspark.sql.functions` expressions first, step up to Apache Arrow-backed Pandas UDFs (`@pandas_udf`) when external Python ML/SciPy libraries are unavoidable, and restrict custom Java/Scala UDFs to strict legacy reuse.

---

### 28. VARIANT Type

**Answer:**  
Introduced in Databricks Runtime 15.3+, the `VARIANT` type stores schema-less semi-structured JSON payloads in a compact shredded binary format rather than plain text `STRING`. It supports fast path extraction (`payload:user.id::INT`), avoids repeated JSON re-parsing at read time, allows deeply heterogeneous schemas to evolve without `ALTER TABLE`, and achieves significantly better compression and query scan speed than `STRING` JSON blobs.

---

### 29. MERGE INTO & Upsert Patterns

**Answer:**  
`MERGE INTO target USING source ON keys` atomically executes conditional `WHEN MATCHED THEN UPDATE/DELETE`, `WHEN NOT MATCHED THEN INSERT`, and `WHEN NOT MATCHED BY SOURCE THEN DELETE` in one ACID commit. Because Copy-on-Write rewrites every touched Parquet file (write amplification), always place explicit constant partition/clustering predicates inside the `ON` condition (`t.event_date >= current_date() - 3`), keep `source` deduplicated by join key, and enable Deletion Vectors so updates avoid full-file rewrites.

---

### 30. Table Constraints & Generated Columns

**Answer:**  
Delta Lake enforces hard data integrity on writes using `NOT NULL` and `CHECK (amount > 0)` constraints (aborting invalid writes before `_delta_log` commit), while Unity Catalog `PRIMARY KEY` and `FOREIGN KEY` constraints are informational metadata used for ER modeling and optimizer join-elimination (`RELY` option). Generated columns (`event_date DATE GENERATED ALWAYS AS (CAST(ts AS DATE))`) derive columns automatically and forward parent filters (`ts >= ...`) for automatic data skipping.

---

### 31. COPY INTO vs. Auto Loader

**Answer:**  
`COPY INTO` performs idempotent SQL batch loads tracked per table log metadata and fits low-volume ad-hoc loads (< thousands of files). Auto Loader (`spark.readStream.format("cloudFiles")`) uses incremental lexical listing or cloud event queues plus RocksDB state checkpoints to ingest millions of cloud files at near-O(new files) cost with native schema evolution and `_rescued_data` capture, making it the Databricks production standard.

---

### 32. File Formats in the Lakehouse

**Answer:**  
Delta Lake builds on compressed columnar **Parquet** files because columnar storage enables projection pruning, dictionary/RLE compression, and footer min/max statistics for Z-Order / Liquid Clustering data skipping. Raw **JSON** and **CSV** are reserved for external landing zones (`Volumes`) prior to Silver parsing, while **Avro** fits row-oriented Kafka/Event Hub streaming payloads with Schema Registry contracts before writing Delta Bronze tables.

---

### 33. Volumes

**Answer:**  
Unity Catalog **Volumes** (`/Volumes/<catalog>/<schema>/<volume>/`) provide three-level governed, RBAC-controlled POSIX/REST access to non-tabular unstructured assets (CSVs, PDFs, ML artifacts, images, init scripts) inside cloud object storage without exposing storage keys or legacy DBFS mounts. **Managed Volumes** store files under catalog/schema managed storage with full lifecycle ownership, while **External Volumes** map existing cloud buckets governed by UC External Locations.

---

### 34. Auto Loader: File Discovery

**Answer:**  
Auto Loader supports two discovery modes: **Directory Listing** (default; supports incremental lexical listing across ordered timestamps with zero cloud IAM webhook setup, optimal under ~1M files/day) and **File Notification** (`cloudFiles.useNotifications = true`; provisions AWS SQS/SNS, Azure Event Grid, or GCP Pub/Sub queues via External Location permissions to push file creation events at near-constant latency across millions of daily objects).

---

### 35. Auto Loader: Schema Evolution & Rescued Data

**Answer:**  
On initialization, Auto Loader samples up to 50 GB or 1,000 files to infer types and caches the schema in `cloudFiles.schemaLocation`. Setting `cloudFiles.schemaEvolutionMode` controls drift handling: `addNewColumns` restarts the stream cleanly on new columns (default with inferred schema), `rescue` preserves unknown fields and malformed values inside a JSON `_rescued_data` column without halting ingestion, `failOnNewColumns` enforces strict contracts, and `none` drops unmapped fields.

---

### 36. Multi-Hop Medallion Architecture

**Answer:**  
The Medallion pattern separates data lifecycle into **Bronze** (immutable, append-only raw landing with ingestion timestamps and `_rescued_data`), **Silver** (deduplicated, typed, constraint-checked enterprise entities), and **Gold** (denormalized star-schema aggregates and feature tables tailored to BI/ML SLAs). It isolates schema drift from downstream dashboards and permits cheap Silver/Gold recomputation from Bronze without re-querying source systems.

---

### 37. Incremental Processing Patterns

**Answer:**  
Instead of reprocessing entire tables nightly, Lakehouse pipelines propagate deltas using **Auto Loader** for new landing files, **Delta Change Data Feed (`readChangeFeed`)** for row-level CDC inserts/updates/deletes, **Structured Streaming Watermarks + Stateful Operations** for windowed events, and **SCD/MERGE Watermark Queries** filtered by Liquid Clustering commit timestamps. Incremental processing cuts compute DBUs roughly proportional to `changed_bytes / total_bytes`.

---

### 38. Lakehouse Federation

**Answer:**  
Unity Catalog **Lakehouse Federation** creates `CONNECTION` objects and **Foreign Catalogs** (`CREATE FOREIGN CATALOG`) over PostgreSQL, MySQL, SQL Server, Snowflake, Redshift, or BigQuery so analysts query live remote tables using unified UC RBAC/lineage without building ETL replication first. Catalyst pushes filters, projections, and aggregates down to the remote SQL engine; choose ingestion into managed Delta instead for high-concurrency BI, large joins, or heavy analytical scans.

---

### 39. Idempotent Pipeline Design

**Answer:**  
An idempotent pipeline yields identical target state across arbitrary retries or partial failure restarts. Implement idempotency via natural-key `MERGE INTO` deduplication, bounded slice replacement (`df.write.option("replaceWhere", "event_date = '2026-11-25'").mode("overwrite")`), deterministic batch IDs / `txnAppId` + `txnVersion` Delta options, or Structured Streaming checkpoints that commit processed offset logs atomically with each micro-batch.

---

### 40. SCD Type 1 & Type 2 Patterns

**Answer:**  
**SCD Type 1** overwrites attributes in place (preserving only current truth), whereas **SCD Type 2** retains full historical versions via `__START_AT`, `__END_AT`, and active-row flags (`__END_AT IS NULL`). In Lakeflow Declarative Pipelines (DLT), `AUTO CDC INTO target FROM source KEYS (id) SEQUENCE BY updated_at STORED AS SCD TYPE 2` handles out-of-order late events, tombstones, and interval splits declaratively without hand-written staged self-joins.

---

### 41. Structured Streaming Fundamentals

**Answer:**  
Structured Streaming treats bounded and unbounded datasets uniformly via an infinite append-only table model backed natively by Delta Lake checkpoints (`_delta_log` offsets + RocksDB state). Combining `spark.readStream` (from `cloudFiles` or Delta sources) with `writeStream.format("delta")` provides ACID snapshot isolation for concurrent readers and seamless transition between continuous low-latency pipelines and scheduled serverless batch increments.

---

### 42. Triggers

**Answer:**  
Structured Streaming triggers govern micro-batch cadence vs. cost: `trigger(availableNow=True)` drains all queued files/commits in optimized multi-batch steps and shuts the cluster down cleanly (replacing deprecated `once=True`), `trigger(processingTime="30 seconds")` runs recurring fixed-interval batches on long-lived compute, `RealTime` / continuous `1 millisecond` mode serves sub-second stateless pipelines, and default/unset runs continuous back-to-back micro-batches as fast as previous ones finish.

---

### 43. Output Modes

**Answer:**  
Delta streaming sinks support three semantics: **Append** (default; outputs new finalized rows—for aggregations, rows emit only once `watermark` expires window end), **Complete** (rewrites the entire updated aggregation result table every batch; invalid for unaggregated append streams), and **Update** (emits only newly added or modified keys since the previous trigger, typically consumed inside `foreachBatch` `MERGE INTO` upserts).

---

### 44. Stream-Static Joins

**Answer:**  
Stream-static joins enrich incoming streaming events (`readStream`) against batch Delta dimension tables (`spark.read.table("dim_users")`) without requiring stream state stores on the static side. Spark dynamically reads the latest committed Delta snapshot of the static table on each micro-batch (`stateless` refresh); **inner** and **left outer** (with stream on left) joins are supported, whereas right/full outer joins on the static side fail because Spark cannot retroactively materialize unmatched static rows into past stream outputs.

---

### 45. Windowed Aggregations

**Answer:**  
Structured Streaming aggregates time-series events across **Tumbling windows** (`window("ts", "5 minutes")`, non-overlapping buckets), **Sliding windows** (`window("ts", "10 minutes", "5 minutes")`, overlapping buckets), and **Session windows** (`session_window("ts", "15 minutes")`, inactivity gap-bounded per key). Combining any window with `.withWatermark("ts", "10 minutes")` allows Spark to evict expired RocksDB state buckets once watermarks cross window boundaries.

---

### 46. foreachBatch Pattern

**Answer:**  
`writeStream.foreachBatch(fn)` exposes each streaming micro-batch as a deterministic static `DataFrame` + monotonic `batch_id`, allowing `MERGE INTO` upserts, multi-table Medallion/DLQ splits, or REST API calls unsupported by standard Delta sinks. Because Spark may retry `batch_id` after failure (at-least-once invocation), make `fn` strictly idempotent via Delta `txnAppId` / `txnVersion` write options or natural-key `MERGE`.

---

### 47. Streaming Tables in Lakeflow Pipelines

**Answer:**  
Lakeflow Declarative Pipelines (DLT) **Streaming Tables** (`CREATE OR REFRESH STREAMING TABLE`) manage Auto Loader streams, cloud checkpoints, RocksDB state provisioning, DQ `@dlt.expect` routing, and incremental Materialized Views automatically via Unity Catalog metadata without manual checkpoint directory management or custom `foreachBatch` boilerplate. Drop down to raw PySpark Structured Streaming only for custom multi-cluster sinks, arbitrary external APIs, or low-level RocksDB/flatMapGroupsWithState control.

---

### 48. Checkpointing & Exactly-Once

**Answer:**  
Every streaming query stores WAL source offsets, commit completion markers, and state-store snapshots under a unique immutable `checkpointLocation` directory on object storage. On restart, Spark reads the last uncommitted WAL offset from the checkpoint to replay idempotent sources (Delta/Auto Loader) and produce end-to-end **exactly-once** targets—provided sink writes are transactional (`Delta`) or deduplicated by `batch_id`; deleting/reusing checkpoints across differing queries corrupts offsets.

---

### 49. Watermarks & Late Data

**Answer:**  
`.withWatermark("event_time", "15 minutes")` sets `Watermark = max(event_time seen) - 15 minutes` to bound stateful aggregation/deduplication memory. Events arriving within the 15-minute grace delay still update open state windows before final output; records older than the advancing watermark are silently dropped and expired RocksDB key state is purged to prevent unbounded OOM growth (`STATE_STORE` heap exhaustion).

---

### 50. Stream-Stream Joins

**Answer:**  
Joining two live `readStream` DataFrames requires buffering uncommitted rows from both sides in distributed RocksDB state stores because matching events can arrive out of order. Production queries MUST specify event-time watermarks on **both** streams plus a range predicate (`a.event_ts BETWEEN b.event_ts - INTERVAL 1 HOUR AND b.event_ts + INTERVAL 1 HOUR`) so Spark can safely evict aged unmatched state, supporting `inner` and watermarked `left/right/full outer` semantics.
