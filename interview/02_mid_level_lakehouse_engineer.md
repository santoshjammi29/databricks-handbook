# 🎓 Databricks Interview Guide — Tier 2: Mid-Level Lakehouse Engineer (Core Pipelines & Storage)

> **Focus Areas**: Auto Loader (cloudFiles), Schema Evolution & _rescued_data, Delta Lake ACID Log Internals, Deletion Vectors, Liquid Clustering, DLT Pipelines, Unity Catalog 3-Tier Namespace.
> **Target Audience**: Production Data Engineers, Analytics Engineers, ETL Developers

---

### Q2.1: Adaptive Query Execution (AQE) (Spark Execution)

**Question & Concept Overview:**  
How AQE adjusts plans at runtime based on actual data statistics. Three key optimizations: coalescing shuffle partitions, converting sort-merge joins to broadcast, optimizing skew joins. Enabled by default.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Adaptive Query Execution (AQE) is an essential mechanism under Spark Execution. How AQE adjusts plans at runtime based on actual data statistics. Three key optimizations: coalescing shuffle partitions, converting sort-merge joins to broadcast, optimizing skew joins. Enabled by default.

**Production Code / SQL Implementation:**
```sql
-- Adaptive Query Execution (AQE) enabled by default in Spark 3.x
SET spark.sql.adaptive.enabled = true;
SET spark.sql.adaptive.coalescePartitions.enabled = true;
SET spark.sql.adaptive.skewJoin.enabled = true;
```

**Key Invariants & Architectural Best Practices:**
- AQE re-optimizes query execution plans dynamically at runtime based on actual stage shuffle statistics.
- Automatically coalesces small shuffle partitions to avoid over-partitioning overhead.
- Converts sort-merge joins into broadcast hash joins at runtime if stage outputs are below broadcast thresholds.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q2.2: Shuffle Operations (Spark Execution)

**Question & Concept Overview:**  
What triggers a shuffle (groupBy, join, repartition, distinct). Why shuffles are expensive (serialization + network + disk I/O). Reading shuffle metrics in Spark UI.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Shuffle Operations is an essential mechanism under Spark Execution. What triggers a shuffle (groupBy, join, repartition, distinct). Why shuffles are expensive (serialization + network + disk I/O). Reading shuffle metrics in Spark UI.

**Production Code / SQL Implementation:**
```python
# Operations that cause shuffles across cluster network
df_shuffled = df.groupBy('department').agg({'salary': 'avg'})
# Inspect shuffle read/write sizes in Spark UI Stages tab
```

**Key Invariants & Architectural Best Practices:**
- Shuffle redistributes data across cluster executor nodes via disk serialization and network transfer.
- Triggered by wide transformations: groupBy, distinct, join, repartition, and window functions.
- Shuffle is often the primary bottleneck in distributed compute; minimizing shuffle volume maximizes throughput.

**Certification Alignment:** `Databricks Professional Data Engineer`

---

### Q2.3: Join Strategies (Spark Execution)

**Question & Concept Overview:**  
The three join types: broadcast hash join (small table fits in memory), sort-merge join (default for large-large), shuffle hash join (rare). The 10MB broadcast threshold (higher with Photon). Using `broadcast()` hints. How AQE dynamically converts at runtime.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Join Strategies is an essential mechanism under Spark Execution. The three join types: broadcast hash join (small table fits in memory), sort-merge join (default for large-large), shuffle hash join (rare). The 10MB broadcast threshold (higher with Photon). Using `broadcast()` hints. How AQE dynamically converts at runtime.

**Production Code / SQL Implementation:**
```python
# Forcing Broadcast Hash Join for small lookup table
from pyspark.sql.functions import broadcast
df_joined = df_large.join(broadcast(df_small), 'dim_key')
```

**Key Invariants & Architectural Best Practices:**
- Broadcast Hash Join (BHJ): Copies small table (<10MB default) to all executors, eliminating network shuffle entirely.
- Sort-Merge Join (SMJ): Standard distributed join for large datasets; requires full key sorting and hash partitioning.
- Shuffle Hash Join (SHJ): Hashes one side into memory per partition when sorting overhead exceeds hash build cost.

**Certification Alignment:** `Databricks Associate / Professional Data Engineer`

---

### Q2.4: Reading the Spark UI (Spark Execution)

**Question & Concept Overview:**  
The tabs that matter: Jobs, Stages, Tasks, SQL. What to look for: task duration variance, spill metrics, shuffle read/write sizes, scan statistics. Diagnosing bottlenecks from the UI.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Reading the Spark UI is an essential mechanism under Spark Execution. The tabs that matter: Jobs, Stages, Tasks, SQL. What to look for: task duration variance, spill metrics, shuffle read/write sizes, scan statistics. Diagnosing bottlenecks from the UI.

**Production Code / SQL Implementation:**
```python
# Spark UI Diagnostics Checklist:
# 1. Jobs & Stages: Identify longest stage duration.
# 2. Tasks: Compare Min, Median, Max task runtimes (detect skew).
# 3. Storage & Shuffle: Check Spill (Memory) and Spill (Disk).
```

**Key Invariants & Architectural Best Practices:**
- Spark UI Stages tab reveals task duration percentiles; high Max vs Median indicates data skew.
- Spill (Memory) vs Spill (Disk) indicates executor memory exhaustion during shuffles or aggregations.
- SQL tab provides graphical Directed Acyclic Graphs (DAGs) with row counts and scan durations.

**Certification Alignment:** `Databricks Professional Data Engineer`

---

### Q2.5: Partitioning & Parallelism (Spark Execution)

**Question & Concept Overview:**  
How `spark.sql.shuffle.partitions` controls parallelism after shuffles. When to repartition vs. coalesce. The relationship between partition count, core count, and task parallelism. How to diagnose over/under-partitioning from Spark UI task metrics.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Partitioning & Parallelism is an essential mechanism under Spark Execution. How `spark.sql.shuffle.partitions` controls parallelism after shuffles. When to repartition vs. coalesce. The relationship between partition count, core count, and task parallelism. How to diagnose over/under-partitioning from Spark UI task metrics.

**Production Code / SQL Implementation:**
```python
# Controlling shuffle parallelism
spark.conf.set('spark.sql.shuffle.partitions', '400')
# Coalesce vs Repartition
df.coalesce(10) # Combines partitions without full shuffle
df.repartition(100, 'region') # Forces full hash shuffle
```

**Key Invariants & Architectural Best Practices:**
- spark.sql.shuffle.partitions defaults to 200; optimal sizing targets 100MB-200MB per shuffle partition.
- coalesce() combines local partitions without triggering a network shuffle (only reduces partition count).
- repartition() triggers a full cluster shuffle to evenly redistribute or increase partition count.

**Certification Alignment:** `Databricks Professional Data Engineer`

---

### Q2.6: Window Functions (SQL & DataFrames)

**Question & Concept Overview:**  
ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, running totals with SUM OVER. Partition and ordering clauses. How these translate to physical execution (shuffles on partition keys).

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Window Functions is an essential mechanism under SQL & DataFrames. ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, running totals with SUM OVER. Partition and ordering clauses. How these translate to physical execution (shuffles on partition keys).

**Production Code / SQL Implementation:**
```sql
-- Rank latest customer state & compute 7-day rolling spend via window frames
WITH ranked_events AS (
  SELECT
    customer_id,
    event_ts,
    spend_usd,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY event_ts DESC) AS recency_rank,
    SUM(spend_usd) OVER (
      PARTITION BY customer_id
      ORDER BY UNIX_TIMESTAMP(event_ts)
      RANGE BETWEEN 604800 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_spend_usd
  FROM prod_catalog.silver.customer_orders
)
SELECT customer_id, event_ts, spend_usd, rolling_7d_spend_usd
FROM ranked_events
WHERE recency_rank = 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, running totals with SUM OVER. Partition and ordering clauses. How these translate to physical execution (shuffles on partition keys).
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.7: Complex Types: ARRAY, STRUCT, MAP (SQL & DataFrames)

**Question & Concept Overview:**  
Creating and querying nested structures. Exploding arrays with `explode()` and `posexplode()`. Struct field access with dot notation. Flattening deeply nested JSON.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Complex Types: ARRAY, STRUCT, MAP is an essential mechanism under SQL & DataFrames. Creating and querying nested structures. Exploding arrays with `explode()` and `posexplode()`. Struct field access with dot notation. Flattening deeply nested JSON.

**Production Code / SQL Implementation:**
```sql
-- Traverse STRUCT paths and explode_outer ARRAY<STRUCT> payloads cleanly
SELECT
  o.order_id,
  o.customer.email AS customer_email,
  o.attributes['channel'] AS sales_channel,
  item_pos AS line_number,
  item.sku AS product_sku,
  item.qty * item.unit_price AS line_total_usd
FROM prod_catalog.bronze.order_events o
LATERAL VIEW POSEXPLODE_OUTER(o.line_items) exploded AS item_pos, item;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- Creating and querying nested structures. Exploding arrays with `explode()` and `posexplode()`. Struct field access with dot notation. Flattening deeply nested JSON.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.8: Higher-Order Functions (SQL & DataFrames)

**Question & Concept Overview:**  
`transform()`, `filter()`, `exists()`, `aggregate()` for array manipulation without exploding. When these outperform explode + groupBy. Real patterns: cleaning arrays, conditional filtering.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Higher-Order Functions is an essential mechanism under SQL & DataFrames. `transform()`, `filter()`, `exists()`, `aggregate()` for array manipulation without exploding. When these outperform explode + groupBy. Real patterns: cleaning arrays, conditional filtering.

**Production Code / SQL Implementation:**
```sql
-- Process nested arrays inline using FILTER, TRANSFORM, and AGGREGATE (zero explode shuffle)
SELECT
  cart_id,
  FILTER(items, x -> x.qty > 0 AND x.in_stock = true) AS valid_items,
  TRANSFORM(items, x -> ROUND(x.qty * x.unit_price * 0.90, 2)) AS discounted_totals,
  AGGREGATE(
    items,
    CAST(0.0 AS DOUBLE),
    (acc, x) -> acc + COALESCE(x.qty * x.unit_price, 0.0)
  ) AS gross_cart_usd
FROM prod_catalog.silver.shopping_carts;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- `transform()`, `filter()`, `exists()`, `aggregate()` for array manipulation without exploding. When these outperform explode + groupBy. Real patterns: cleaning arrays, conditional filtering.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.9: CTEs, PIVOT & Subqueries (SQL & DataFrames)

**Question & Concept Overview:**  
Writing CTEs for readable multi-step queries. PIVOT for wide-format reshaping. Correlated vs. uncorrelated subqueries. How these map to physical plans.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, CTEs, PIVOT & Subqueries is an essential mechanism under SQL & DataFrames. Writing CTEs for readable multi-step queries. PIVOT for wide-format reshaping. Correlated vs. uncorrelated subqueries. How these map to physical plans.

**Production Code / SQL Implementation:**
```sql
-- Readable multi-stage CTEs + PIVOT wide transformation for BI executive reporting
WITH monthly_sku AS (
  SELECT
    DATE_TRUNC('month', usage_date) AS billing_month,
    sku_name,
    ROUND(SUM(usage_quantity), 1) AS total_dbus
  FROM system.billing.usage
  WHERE usage_date >= current_date() - 90
  GROUP BY 1, 2
)
SELECT *
FROM monthly_sku
PIVOT (
  SUM(total_dbus) FOR sku_name IN ('JOBS', 'SERVERLESS_SQL', 'ALL_PURPOSE')
)
ORDER BY billing_month DESC;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- Writing CTEs for readable multi-step queries. PIVOT for wide-format reshaping. Correlated vs. uncorrelated subqueries. How these map to physical plans.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.10: UDFs vs. Native Functions (SQL & DataFrames)

**Question & Concept Overview:**  
Why Python UDFs break Catalyst and force row-by-row execution. The 10-100x performance gap. Pandas UDFs (vectorized) as a middle ground. When a UDF is genuinely the right choice.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, UDFs vs. Native Functions is an essential mechanism under SQL & DataFrames. Why Python UDFs break Catalyst and force row-by-row execution. The 10-100x performance gap. Pandas UDFs (vectorized) as a middle ground. When a UDF is genuinely the right choice.

**Production Code / SQL Implementation:**
```python
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.functions import pandas_udf

# 1. Prefer native Spark SQL functions (full Photon/Catalyst vectorization)
native_df = spark.range(1000).withColumn("normalized", F.upper(F.trim(F.lit("  prod  "))))


# 2. When Python scientific/ML libraries are required, use Arrow-backed @pandas_udf
@pandas_udf("double")
def zscore_series(vals: pd.Series) -> pd.Series:
    std = vals.std() or 1.0
    return (vals - vals.mean()) / std


scored_df = spark.range(1000).withColumn("z_score", zscore_series(F.col("id").cast("double")))
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- Why Python UDFs break Catalyst and force row-by-row execution. The 10-100x performance gap. Pandas UDFs (vectorized) as a middle ground. When a UDF is genuinely the right choice.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.11: VARIANT Type (SQL & DataFrames)

**Question & Concept Overview:**  
Storing semi-structured data (JSON) in a native binary format. Schema-on-read without parsing overhead. Querying with `:` path syntax. When VARIANT outperforms STRING or STRUCT columns for JSON data.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, VARIANT Type is an essential mechanism under SQL & DataFrames. Storing semi-structured data (JSON) in a native binary format. Schema-on-read without parsing overhead. Querying with `:` path syntax. When VARIANT outperforms STRING or STRUCT columns for JSON data.

**Production Code / SQL Implementation:**
```sql
-- Native semi-structured VARIANT storage & typed path extraction (DBR 15.3+)
CREATE TABLE IF NOT EXISTS prod_catalog.bronze.webhook_payloads (
  received_at TIMESTAMP,
  payload VARIANT
);

INSERT INTO prod_catalog.bronze.webhook_payloads
SELECT
  current_timestamp(),
  PARSE_JSON('{"event":"charge.succeeded","amount_cents":4900,"meta":{"region":"eu"}}');

SELECT
  payload:event::STRING AS event_name,
  payload:amount_cents::INT / 100.0 AS amount_usd,
  payload:meta.region::STRING AS region
FROM prod_catalog.bronze.webhook_payloads;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- Storing semi-structured data (JSON) in a native binary format. Schema-on-read without parsing overhead. Querying with `:` path syntax. When VARIANT outperforms STRING or STRUCT columns for JSON data.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.12: Table Constraints & Generated Columns (SQL & DataFrames)

**Question & Concept Overview:**  
CHECK constraints, NOT NULL, PRIMARY KEY (informational), FOREIGN KEY (informational). Generated columns with expressions (e.g., `date GENERATED ALWAYS AS CAST(timestamp AS DATE)`). How constraints enforce data quality at the write layer.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Table Constraints & Generated Columns is an essential mechanism under SQL & DataFrames. CHECK constraints, NOT NULL, PRIMARY KEY (informational), FOREIGN KEY (informational). Generated columns with expressions (e.g., `date GENERATED ALWAYS AS CAST(timestamp AS DATE)`). How constraints enforce data quality at the write layer.

**Production Code / SQL Implementation:**
```sql
-- Generated partition/clustering columns + CHECK / NOT NULL enforcement at write time
CREATE TABLE IF NOT EXISTS prod_catalog.silver.payments_enforced (
  payment_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  event_date DATE GENERATED ALWAYS AS (CAST(event_ts AS DATE)),
  amount_usd DECIMAL(12, 2) NOT NULL,
  CONSTRAINT positive_amount CHECK (amount_usd > 0)
)
USING DELTA
CLUSTER BY (event_date);
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks SQL & DataFrames.
- CHECK constraints, NOT NULL, PRIMARY KEY (informational), FOREIGN KEY (informational). Generated columns with expressions (e.g., `date GENERATED ALWAYS AS CAST(timestamp AS DATE)`). How constraints enforce data quality at the write layer.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.13: Auto Loader: File Discovery (Data Ingestion)

**Question & Concept Overview:**  
File notification mode (cloud events, efficient at scale, requires setup) vs. directory listing mode (simpler, slower with millions of files). When to use each. Why Auto Loader is the default for production ingestion.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Auto Loader: File Discovery is an essential mechanism under Data Ingestion. File notification mode (cloud events, efficient at scale, requires setup) vs. directory listing mode (simpler, slower with millions of files). When to use each. Why Auto Loader is the default for production ingestion.

**Production Code / SQL Implementation:**
```python
# Auto Loader File Notification mode (SQS / Event Grid) for >1M files/day pipelines
high_scale_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.useNotifications", "true")
    .option("cloudFiles.maxFilesPerTrigger", 2000)
    .option("cloudFiles.schemaLocation", "/Volumes/prod_catalog/bronze/meta/clickstream_schema")
    .load("abfss://raw@datalake.dfs.core.windows.net/clickstream/")
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- File notification mode (cloud events, efficient at scale, requires setup) vs. directory listing mode (simpler, slower with millions of files). When to use each. Why Auto Loader is the default for production ingestion.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.14: Auto Loader: Schema Evolution & Rescued Data (Data Ingestion)

**Question & Concept Overview:**  
How schema inference works from the first batch. `cloudFiles.schemaEvolutionMode` options (addNewColumns, rescue, failOnNewColumns, none). The `_rescued_data` column for capturing mismatches instead of failing.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Auto Loader: Schema Evolution & Rescued Data is an essential mechanism under Data Ingestion. How schema inference works from the first batch. `cloudFiles.schemaEvolutionMode` options (addNewColumns, rescue, failOnNewColumns, none). The `_rescued_data` column for capturing mismatches instead of failing.

**Production Code / SQL Implementation:**
```python
# Quarantine unexpected fields safely in _rescued_data instead of aborting SLA streams
resilient_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("rescuedDataColumn", "_rescued_data")
    .option("cloudFiles.schemaHints", "customer_id BIGINT, amount DECIMAL(12,2)")
    .option("cloudFiles.schemaLocation", "/Volumes/prod_catalog/bronze/meta/payments_schema")
    .load("/Volumes/prod_catalog/bronze/landing/payments/")
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- How schema inference works from the first batch. `cloudFiles.schemaEvolutionMode` options (addNewColumns, rescue, failOnNewColumns, none). The `_rescued_data` column for capturing mismatches instead of failing.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.15: Multi-Hop Medallion Architecture (Data Ingestion)

**Question & Concept Overview:**  
Bronze (raw, append-only), Silver (cleaned, deduplicated, typed), Gold (business aggregates). Why this pattern exists. When it's overkill. How each layer serves different consumers with different freshness requirements.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Multi-Hop Medallion Architecture is an essential mechanism under Data Ingestion. Bronze (raw, append-only), Silver (cleaned, deduplicated, typed), Gold (business aggregates). Why this pattern exists. When it's overkill. How each layer serves different consumers with different freshness requirements.

**Production Code / SQL Implementation:**
```python
from pyspark.sql import functions as F

# Bronze -> Silver -> Gold clear separation of immutable landing, clean entities, and BI marts
bronze = spark.readStream.table("prod_catalog.bronze.events_raw")
silver = (
    bronze.filter("event_id IS NOT NULL")
    .withColumn("event_date", F.to_date("event_ts"))
    .dropDuplicates(["event_id"])
)
(
    silver.writeStream
    .option("checkpointLocation", "/Volumes/prod_catalog/silver/checkpoints/events")
    .trigger(availableNow=True)
    .toTable("prod_catalog.silver.events_clean")
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- Bronze (raw, append-only), Silver (cleaned, deduplicated, typed), Gold (business aggregates). Why this pattern exists. When it's overkill. How each layer serves different consumers with different freshness requirements.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.16: Incremental Processing Patterns (Data Ingestion)

**Question & Concept Overview:**  
Processing only new/changed data. Techniques: Auto Loader (file-level), Change Data Feed (row-level), watermark-based (time-based), merge keys (hash-based). Cost vs. latency tradeoffs for each.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Incremental Processing Patterns is an essential mechanism under Data Ingestion. Processing only new/changed data. Techniques: Auto Loader (file-level), Change Data Feed (row-level), watermark-based (time-based), merge keys (hash-based). Cost vs. latency tradeoffs for each.

**Production Code / SQL Implementation:**
```python
# Incremental Silver -> Gold pipeline driven by Delta Change Data Feed (CDF)
cdf_stream = (
    spark.readStream.format("delta")
    .option("readChangeFeed", "true")
    .option("startingVersion", 120)
    .table("prod_catalog.silver.orders_clean")
    .filter(F.col("_change_type").isin("insert", "update_postimage"))
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- Processing only new/changed data. Techniques: Auto Loader (file-level), Change Data Feed (row-level), watermark-based (time-based), merge keys (hash-based). Cost vs. latency tradeoffs for each.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.17: Lakehouse Federation (Data Ingestion)

**Question & Concept Overview:**  
Querying external databases (PostgreSQL, MySQL, SQL Server, Snowflake) without copying data. Query pushdown optimization. Connection objects and security. When federation beats ETL and when it doesn't.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Lakehouse Federation is an essential mechanism under Data Ingestion. Querying external databases (PostgreSQL, MySQL, SQL Server, Snowflake) without copying data. Query pushdown optimization. Connection objects and security. When federation beats ETL and when it doesn't.

**Production Code / SQL Implementation:**
```sql
-- Query remote PostgreSQL operational DB via Unity Catalog Foreign Catalog (zero ETL copy)
CREATE CONNECTION IF NOT EXISTS pg_crm_conn TYPE postgresql
OPTIONS (
  host 'crm-replica.internal.company.com',
  port '5432',
  user secret('prod-kv', 'pg-ro-user'),
  password secret('prod-kv', 'pg-ro-pass')
);

CREATE FOREIGN CATALOG IF NOT EXISTS crm_federated
USING CONNECTION pg_crm_conn
OPTIONS (database 'crm_prod');

SELECT account_id, plan_tier FROM crm_federated.public.accounts WHERE is_active = true;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Data Ingestion.
- Querying external databases (PostgreSQL, MySQL, SQL Server, Snowflake) without copying data. Query pushdown optimization. Connection objects and security. When federation beats ETL and when it doesn't.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.18: Structured Streaming Fundamentals (Streaming)

**Question & Concept Overview:**  
How Structured Streaming on Databricks uses Delta Lake as both source and sink. The `readStream`/`writeStream` API. Why Delta-to-Delta streaming is the most common production pattern. Integration with Auto Loader as a file source.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Structured Streaming Fundamentals is an essential mechanism under Streaming. How Structured Streaming on Databricks uses Delta Lake as both source and sink. The `readStream`/`writeStream` API. Why Delta-to-Delta streaming is the most common production pattern. Integration with Auto Loader as a file source.

**Production Code / SQL Implementation:**
```python
from pyspark.sql import functions as F

# Stateful streaming deduplication with bounded watermark state -> Delta Sink
dedup_events = (
    spark.readStream.table("prod_catalog.bronze.telemetry")
    .withWatermark("event_ts", "30 minutes")
    .dropDuplicates(["device_id", "event_ts"])
)
query = (
    dedup_events.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/Volumes/prod_catalog/silver/checkpoints/telemetry")
    .toTable("prod_catalog.silver.telemetry")
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- How Structured Streaming on Databricks uses Delta Lake as both source and sink. The `readStream`/`writeStream` API. Why Delta-to-Delta streaming is the most common production pattern. Integration with Auto Loader as a file source.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.19: Triggers (Streaming)

**Question & Concept Overview:**  
`processingTime` (recurring micro-batches at fixed intervals). `availableNow` (process all available data then stop; replaces deprecated `once`). Choosing the right trigger for latency vs. cost.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Triggers is an essential mechanism under Streaming. `processingTime` (recurring micro-batches at fixed intervals). `availableNow` (process all available data then stop; replaces deprecated `once`). Choosing the right trigger for latency vs. cost.

**Production Code / SQL Implementation:**
```python
# Trigger.availableNow processes all queued micro-batches then stops cleanly (FinOps best fit)
(
    spark.readStream.table("prod_catalog.bronze.orders")
    .writeStream.format("delta")
    .option("checkpointLocation", "/Volumes/prod_catalog/silver/checkpoints/orders_avail")
    .trigger(availableNow=True)
    .toTable("prod_catalog.silver.orders")
)

# For low-latency SLA pipelines: recurring micro-batch interval
# .trigger(processingTime="10 seconds")
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- `processingTime` (recurring micro-batches at fixed intervals). `availableNow` (process all available data then stop; replaces deprecated `once`). Choosing the right trigger for latency vs. cost.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.20: Output Modes (Streaming)

**Question & Concept Overview:**  
Append (new rows only, default). Complete (full result table, aggregations only). Update (changed rows only). Which modes work with which operations and sinks.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Output Modes is an essential mechanism under Streaming. Append (new rows only, default). Complete (full result table, aggregations only). Update (changed rows only). Which modes work with which operations and sinks.

**Production Code / SQL Implementation:**
```python
from pyspark.sql import functions as F

# Watermarked aggregation using Append mode emits rows only once window closes cleanly
windowed_counts = (
    spark.readStream.table("prod_catalog.silver.clicks")
    .withWatermark("click_ts", "10 minutes")
    .groupBy(F.window("click_ts", "5 minutes"), F.col("campaign_id"))
    .count()
)
(
    windowed_counts.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/Volumes/prod_catalog/gold/checkpoints/clicks_5m")
    .toTable("prod_catalog.gold.campaign_clicks_5m")
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- Append (new rows only, default). Complete (full result table, aggregations only). Update (changed rows only). Which modes work with which operations and sinks.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.21: Stream-Static Joins (Streaming)

**Question & Concept Overview:**  
Joining streaming DataFrames with batch DataFrames. Static side re-read each micro-batch. Use cases: enriching events with dimension data. Outer join limitations on the streaming side.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Stream-Static Joins is an essential mechanism under Streaming. Joining streaming DataFrames with batch DataFrames. Static side re-read each micro-batch. Use cases: enriching events with dimension data. Outer join limitations on the streaming side.

**Production Code / SQL Implementation:**
```python
from pyspark.sql import functions as F

# Enrich high-throughput event stream against latest snapshot of Silver dimension table
events_stream = spark.readStream.table("prod_catalog.bronze.page_views")
dim_users = spark.read.table("prod_catalog.silver.dim_users")  # Re-read each micro-batch

# Left outer join preserves unmatched stream events; use F.broadcast for small dimensions
enriched = events_stream.join(F.broadcast(dim_users), on="user_id", how="left")
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- Joining streaming DataFrames with batch DataFrames. Static side re-read each micro-batch. Use cases: enriching events with dimension data. Outer join limitations on the streaming side.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.22: Windowed Aggregations (Streaming)

**Question & Concept Overview:**  
Tumbling windows (fixed, non-overlapping), sliding windows (fixed, overlapping), session windows (gap-based). Combining windows with watermarks for bounded state.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Windowed Aggregations is an essential mechanism under Streaming. Tumbling windows (fixed, non-overlapping), sliding windows (fixed, overlapping), session windows (gap-based). Combining windows with watermarks for bounded state.

**Production Code / SQL Implementation:**
```python
from pyspark.sql import functions as F

# 10-minute sliding windows advancing every 5 minutes with a 15-minute late-data watermark
sliding_metrics = (
    spark.readStream.table("prod_catalog.silver.sensor_readings")
    .withWatermark("reading_ts", "15 minutes")
    .groupBy(
        F.window("reading_ts", "10 minutes", "5 minutes"),
        F.col("sensor_id"),
    )
    .agg(F.avg("temperature_c").alias("avg_temp_c"), F.count("*").alias("sample_count"))
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- Tumbling windows (fixed, non-overlapping), sliding windows (fixed, overlapping), session windows (gap-based). Combining windows with watermarks for bounded state.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.23: foreachBatch Pattern (Streaming)

**Question & Concept Overview:**  
Using `foreachBatch()` to apply arbitrary batch logic to each micro-batch. Use cases: writing to multiple sinks, MERGE operations in streaming, calling external APIs. Exactly-once considerations.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, foreachBatch Pattern is an essential mechanism under Streaming. Using `foreachBatch()` to apply arbitrary batch logic to each micro-batch. Use cases: writing to multiple sinks, MERGE operations in streaming, calling external APIs. Exactly-once considerations.

**Production Code / SQL Implementation:**
```python
def upsert_microbatch_to_silver(microbatch_df, batch_id: int) -> None:
    dedup_batch = microbatch_df.dropDuplicates(["order_id"])
    dedup_batch.createOrReplaceTempView("src_updates")
    microbatch_df.sparkSession.sql(
        """
        MERGE INTO prod_catalog.silver.orders AS tgt
        USING src_updates AS src
        ON tgt.order_id = src.order_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )


(
    spark.readStream.table("prod_catalog.bronze.orders")
    .writeStream.foreachBatch(upsert_microbatch_to_silver)
    .option("checkpointLocation", "/Volumes/prod_catalog/silver/checkpoints/orders_merge")
    .trigger(availableNow=True)
    .start()
)
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- Using `foreachBatch()` to apply arbitrary batch logic to each micro-batch. Use cases: writing to multiple sinks, MERGE operations in streaming, calling external APIs. Exactly-once considerations.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.24: Streaming Tables in Lakeflow Pipelines (Streaming)

**Question & Concept Overview:**  
How streaming tables in Lakeflow Declarative Pipelines abstract away checkpoint and state management. The difference between streaming tables and raw Structured Streaming. When to use each approach.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Streaming Tables in Lakeflow Pipelines is an essential mechanism under Streaming. How streaming tables in Lakeflow Declarative Pipelines abstract away checkpoint and state management. The difference between streaming tables and raw Structured Streaming. When to use each approach.

**Production Code / SQL Implementation:**
```sql
-- Lakeflow Declarative Pipeline (DLT) managed Streaming Table + Materialized View Gold
CREATE OR REFRESH STREAMING TABLE prod_catalog.bronze.raw_orders
AS SELECT *, current_timestamp() AS ingested_at
FROM STREAM read_files(
  '/Volumes/prod_catalog/bronze/landing/orders/',
  format => 'json'
);

CREATE OR REFRESH MATERIALIZED VIEW prod_catalog.gold.daily_order_totals
AS SELECT DATE(order_ts) AS order_date, COUNT(*) AS orders, SUM(amount_usd) AS revenue
FROM prod_catalog.bronze.raw_orders
GROUP BY 1;
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Streaming.
- How streaming tables in Lakeflow Declarative Pipelines abstract away checkpoint and state management. The difference between streaming tables and raw Structured Streaming. When to use each approach.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---

### Q2.25: Predicate Pushdown & Data Skipping (Performance & Cost)

**Question & Concept Overview:**  
How Spark skips reading files/partitions that can't match filter predicates. File-level min/max column statistics. What breaks pushdown (casting, functions on filter columns). How Liquid Clustering keys maximize skipping.

**Detailed Technical Explanation:**  
In enterprise Databricks lakehouses, Predicate Pushdown & Data Skipping is an essential mechanism under Performance & Cost. How Spark skips reading files/partitions that can't match filter predicates. File-level min/max column statistics. What breaks pushdown (casting, functions on filter columns). How Liquid Clustering keys maximize skipping.

**Production Code / SQL Implementation:**
```sql
-- Column statistics min/max + Liquid Clustering skip >95% of Parquet files automatically
EXPLAIN COST
SELECT order_id, customer_id, amount_usd
FROM prod_catalog.silver.orders
WHERE order_date BETWEEN DATE '2026-11-01' AND DATE '2026-11-07'
  AND region = 'EU-WEST';
```

**Key Invariants & Architectural Best Practices:**
- Core production concept in Databricks Performance & Cost.
- How Spark skips reading files/partitions that can't match filter predicates. File-level min/max column statistics. What breaks pushdown (casting, functions on filter columns). How Liquid Clustering keys maximize skipping.
- Essential architectural pattern for enterprise lakehouse systems.

**Certification Alignment:** `Databricks Certified Data Engineer Associate / Professional`

---
