"""
Module 10: Production Incidents, Triage & Architecture Blueprints (Notebooks 099 - 105)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "10_production_incidents_and_blueprints"
MODULE_NAME = "Module 10: Production Incidents, Triage & Architecture Blueprints"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "099",
            "title": "Production Incident 01: Driver & Executor OutOfMemory (OOM) Forensic Triage",
            "filename": "099_production_incident_01_driver_and_executor_oom_forensic_triage.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "At 03:00 AM, a scheduled production pipeline generating daily financial reports fails with `java.lang.OutOfMemoryError: Java heap space`. The on-call data engineer is paged and must restore pipeline execution.",
            "problem_statement": "Contrast unbounded driver `.collect()` memory anti-patterns against memory-safe distributed Delta writes, bounded driver samples (`limit(N)`), and executor partition-size diagnostics (`spark_partition_id()`).",
            "architectural_notes": "Driver OOM occurs when unaggregated partitions are pulled to the driver via `.collect()`, `.toPandas()`, or misconfigured `broadcast()` thresholds. Executor OOM occurs when skewed partitions overload single task execution slots. Distributed aggregation + balanced partitioning eliminate heap exhaustion.",
            "sections": [
                {
                    "title": "1. Executor Partition Skew Telemetry & Driver-Safe Distributed Aggregation",
                    "explanation": "Write synthetic financial transactions to Delta, inspect per-partition row distribution via `F.spark_partition_id()`, aggregate strictly on executors before bounded driver inspection, and prove balanced executor memory distribution.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_099_", dir=globals().get("HANDBOOK_TMP_DIR")))
tx_path = str(lab_dir / "tx_events_delta")

(
    spark.range(0, 4000)
    .withColumn("region", F.element_at(F.array(F.lit("US"), F.lit("EU"), F.lit("APAC"), F.lit("LATAM")), ((F.col("id") % 4) + 1).cast("int")))
    .withColumn("amount", (F.col("id") * 1.1).cast("double"))
    .repartition(4)
    .write.format("delta")
    .save(tx_path)
)

tx_df = spark.read.format("delta").load(tx_path)

# SAFE DIAGNOSTIC: Measure partition size balance ON EXECUTORS without pulling raw rows to driver!
part_counts = [
    r["cnt"]
    for r in tx_df.groupBy(F.spark_partition_id().alias("part_id")).agg(F.count("*").alias("cnt")).collect()
]
# SAFE EXPORT: Push heavy aggregation to executors first, then pull tiny summary rows
summary_rows = (
    tx_df.groupBy("region")
    .agg(F.count("*").alias("tx_count"), F.round(F.sum("amount"), 2).alias("total_amount"))
    .orderBy("region")
    .limit(10)
    .collect()
)

print(f"Executor partition counts: {part_counts}")
print(f"Driver summary row count : {len(summary_rows)} (agg instead of 4000 raw rows)")
assert len(part_counts) >= 2 and max(part_counts) / min(part_counts) <= 1.5
assert sum(r["tx_count"] for r in summary_rows) == 4000
""",
                }
            ],
            "key_takeaways": [
                "Ban Unbounded `.collect()`: Push `groupBy` / `agg` to executors and pull only tiny summary rows or `.limit(N)` previews.",
                "Diagnose Partition Skew: Check `spark_partition_id()` counts and Spark UI Max-vs-Median task duration ratios.",
                "Off-Heap Safety: Keep large joins off driver broadcast when table sizes exceed `autoBroadcastJoinThreshold`.",
            ],
            "interview_questions": [
                "How do you determine from Spark UI and cluster logs whether an OOM occurred on the driver or an executor?",
                "What Spark configuration settings govern driver maximum result sizes?",
            ],
        },
        {
            "nb_id": "100",
            "title": "Production Incident 02: Concurrent Modification OCC Conflict Resolution in Delta",
            "filename": "100_production_incident_02_concurrent_modification_occ_conflict_resolution_in_delta.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import random",
                "import tempfile",
                "import threading",
                "import time",
                "from concurrent.futures import ThreadPoolExecutor",
                "from pathlib import Path",
            ],
            "business_scenario": "Two high-throughput microservices attempt to update customer records and append new telemetry simultaneously, causing sporadic `ConcurrentAppendException` errors and transaction rollbacks.",
            "problem_statement": "Execute our jittered exponential-backoff OCC retry wrapper against concurrent Delta writers (`ThreadPoolExecutor`), recover cleanly from snapshot conflicts, and verify Deletion Vectors + Row Tracking enablement.",
            "architectural_notes": "Delta Lake validates overlapping partition commits atomically. Adding jittered exponential retries (`execute_with_occ_retry`) absorbs transient OCC collisions while `delta.enableDeletionVectors` and `delta.enableRowTracking` isolate file-level concurrency conflicts.",
            "sections": [
                {
                    "title": "1. Live OCC Conflict Storm Recovery with Jittered Exponential Retry Wrapper",
                    "explanation": "Launch concurrent `replaceWhere` commits on the same partition wrapped in `execute_with_occ_retry`, assert 100% commit success, and enable Row Tracking + Deletion Vectors on the target table.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_100_", dir=globals().get("HANDBOOK_TMP_DIR")))
occ_path = str(lab_dir / "cust_occ_delta")

spark.sql(f\"\"\"
    CREATE TABLE t100_cust (customer_id BIGINT, region STRING, state STRING) USING DELTA
    PARTITIONED BY (region)
    LOCATION '{occ_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true', 'delta.enableRowTracking' = 'true')
\"\"\")
spark.sql("INSERT INTO t100_cust VALUES (1, 'US', 'init')")

def execute_with_occ_retry(operation_func, max_retries: int = 8, base_delay: float = 0.03):
    for attempt in range(1, max_retries + 1):
        try:
            return operation_func()
        except Exception as exc:
            msg = f"{type(exc).__name__} {exc}"
            if "Concurrent" in msg or "DELTA_CONCURRENT" in msg:
                if attempt == max_retries:
                    raise
                time.sleep((base_delay * (2 ** min(attempt - 1, 4))) + random.uniform(0.01, 0.05))
            else:
                raise

barrier = threading.Barrier(4)

def resilient_worker(worker_id: int) -> str:
    barrier.wait()
    def _write():
        (
            spark.createDataFrame([(100 + worker_id, "US", f"worker_{worker_id}")], ["customer_id", "region", "state"])
            .write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", "region = 'US'")
            .save(occ_path)
        )
        return f"worker_{worker_id}"
    return execute_with_occ_retry(_write)

with ThreadPoolExecutor(max_workers=4) as pool:
    committed = [f.result() for f in [pool.submit(resilient_worker, i) for i in range(4)]]

props = dict(spark.sql("SHOW TBLPROPERTIES t100_cust").collect())
final_count = spark.table("t100_cust").count()
print(f"All {len(committed)} concurrent writers succeeded cleanly; rows={final_count}")
assert len(committed) == 4 and final_count == 1
assert props.get("delta.enableDeletionVectors") == "true" and props.get("delta.enableRowTracking") == "true"
""",
                }
            ],
            "key_takeaways": [
                "Enable Row-Level Concurrency: Turn on `delta.enableDeletionVectors = true` and `delta.enableRowTracking = true`.",
                "Exponential Jitter Retries: Random jitter prevents thundering-herd retries on colliding transactions.",
                "Partition-Pruned Updates: Narrow `MERGE` / `replaceWhere` scopes down to disjoint partitions whenever possible.",
            ],
            "interview_questions": [
                "Why is random jitter essential when implementing exponential backoff retries for Delta Lake OCC conflicts?",
                "How does Row-Level Concurrency eliminate the need for manual write serialization?",
            ],
        },
        {
            "nb_id": "101",
            "title": "Production Incident 03: Straggler Tasks & Extreme Data Skew Salting Remediation",
            "filename": "101_production_incident_03_straggler_tasks_and_extreme_data_skew_salting_remediation.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": ["from pyspark.sql import functions as F"],
            "business_scenario": "A 100-node cluster executes a join between transactions and merchant dimensions. 99 out of 100 tasks finish in 5 seconds, but Task 100 hangs for 55 minutes due to extreme key skew on 'Amazon' merchant ID.",
            "problem_statement": "Diagnose the 99% straggler task using the Spark UI, inspect shuffle distribution percentiles, and implement two-phase deterministic key salting to redistribute skewed keys uniformly.",
            "architectural_notes": "When one key has millions of records while other keys have hundreds, standard hash partitioning routes all millions of records to a single worker core. Key salting appends a pseudo-random suffix to the skewed key, distributing it across $N$ worker buckets.",
            "sections": [
                {
                    "title": "1. Two-Phase Deterministic Key Salting Implementation",
                    "explanation": "Salt the large skewed DataFrame and replicate the lookup table across salt buckets.",
                    "code": """# Two-phase key salting pattern
SALT_FACTOR = 16

# 1. Salt large skewed table
df_large_salted = spark.createDataFrame([("AMAZON", 100.0), ("AMAZON", 250.0), ("EBAY", 45.0)], ["merchant", "amount"]) \\
    .withColumn("_salt", F.concat(F.col("merchant"), F.lit("_"), F.floor(F.rand() * SALT_FACTOR)))

# 2. Replicate dimension table across all salt factors
df_dim = spark.createDataFrame([("AMAZON", "Retail"), ("EBAY", "Auction")], ["merchant", "category"])
df_dim_replicated = df_dim \\
    .withColumn("_salts", F.array([F.lit(i) for i in range(SALT_FACTOR)])) \\
    .withColumn("_sub_salt", F.explode("_salts")) \\
    .withColumn("_salt", F.concat(F.col("merchant"), F.lit("_"), F.col("_sub_salt"))) \\
    .drop("_salts", "_sub_salt")

# 3. Uniform join on salted key
df_joined = df_large_salted.join(df_dim_replicated, on="_salt").drop("_salt")
df_joined.show()
assert df_joined.count() == 3
"""
                }
            ],
            "key_takeaways": [
                "Straggler Diagnostic: Check Spark UI Task Duration percentiles: if Max >> Median, you have severe skew.",
                "AQE Skew Join: Verify `spark.sql.adaptive.skewJoin.enabled = true` is active.",
                "Two-Phase Salting: Use deterministic salting when AQE cannot split non-equi joins or custom transformations."
            ],
            "interview_questions": [
                "How does Adaptive Query Execution (AQE) detect and resolve join skew at runtime?",
                "What is the mathematical principle behind key salting in distributed hash joins?"
            ]
        },
        {
            "nb_id": "102",
            "title": "Production Incident 04: Streaming State Explosions & RocksDB Checkpoint Recovery",
            "filename": "102_production_incident_04_streaming_state_explosions_and_rocksdb_checkpoint_recovery.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import StringType, StructField, StructType",
            ],
            "business_scenario": "A 24/7 fraud scoring streaming pipeline crashed due to JVM heap exhaustion after running for 3 weeks. State size grew to 40 GB because event-time watermarking was omitted.",
            "problem_statement": "Execute a stateful Structured Streaming tumbling-window aggregation bounded by `.withWatermark('event_ts', '1 hour')` across sequential JSON batches and verify expired late events outside the watermark are bounded/evicted cleanly.",
            "architectural_notes": "Stateful streaming operations (`groupBy().count()`, stream-stream joins) buffer keys in RocksDB state stores. Specifying `withWatermark()` lets Spark track `max_event_time - delay`, commit finalized windows, and evict expired window state cleanly.",
            "sections": [
                {
                    "title": "1. Bounded Event-Time Watermark & Late-Event Eviction Verification",
                    "explanation": "Ingest Wave 1 events establishing an advanced event-time watermark, then send Wave 2 with an on-time advance and a 2.5-hour late zombie record, confirming expired window eviction cleanly.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_102_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "fraud_events"
landing.mkdir(parents=True)
ckpt = str(lab_dir / "ckpt_watermark")
out_delta = str(lab_dir / "gold_fraud_windows")

schema = StructType(
    [
        StructField("device_id", StringType(), False),
        StructField("event_ts_str", StringType(), False),
    ]
)

def run_windowed_batch():
    stream = (
        spark.readStream.format("json")
        .schema(schema)
        .load(str(landing))
        .withColumn("event_ts", F.to_timestamp("event_ts_str"))
        .withWatermark("event_ts", "1 hour")
        .groupBy(F.window("event_ts", "30 minutes"), F.col("device_id"))
        .count()
        .select(
            F.col("device_id"),
            F.col("window.start").alias("win_start"),
            F.col("window.end").alias("win_end"),
            F.col("count").alias("event_count"),
        )
    )
    q = (
        stream.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", ckpt)
        .trigger(availableNow=True)
        .start(out_delta)
    )
    q.awaitTermination()

# Wave 1: two events in [10:00, 10:30) and one at 12:10 advancing end-of-batch watermark to 11:10
(landing / "wave1.json").write_text(
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 10:05:00"}\\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 10:15:00"}\\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 12:10:00"}\\n',
    encoding="utf-8",
)
run_windowed_batch()

# Wave 2: arrives with 09:30 late poison event (before watermark 11:10 -> MUST be evicted!) + 12:20 advance
(landing / "wave2.json").write_text(
    '{"device_id": "dev_late_dropped", "event_ts_str": "2026-11-20 09:30:00"}\\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 12:20:00"}\\n',
    encoding="utf-8",
)
run_windowed_batch()

gold_df = spark.read.format("delta").load(out_delta)
emitted = gold_df.filter("device_id = 'dev_active'").select("event_count").collect()
late_count = gold_df.filter("device_id = 'dev_late_dropped'").count()

print(f"Finalized bounded window rows for dev_active: {[r['event_count'] for r in emitted]}, late_dropped={late_count}")
assert len(emitted) == 1 and emitted[0]["event_count"] == 2
assert late_count == 0
""",
                }
            ],
            "key_takeaways": [
                "Mandatory Watermarking: Never run unbounded stateful aggregations without `.withWatermark()`.",
                "RocksDB State Store: Offload multi-gigabyte state keys from JVM heap onto local worker NVMe SSDs.",
                "Predictable Late Handling: Records arriving behind the watermark are dropped safely rather than leaking infinite state.",
            ],
            "interview_questions": [
                "How does event-time watermarking prevent state store memory leaks in Spark Structured Streaming?",
                "What steps are required to safely rewind and recover a corrupted streaming checkpoint?",
            ],
        },
        {
            "nb_id": "103",
            "title": "Production Incident 05: Auto Loader Schema Drift & Poison Pill Quarantine Forensics",
            "filename": "103_production_incident_05_auto_loader_schema_drift_and_poison_pill_quarantine_forensics.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": ["from pyspark.sql import functions as F"],
            "business_scenario": "An upstream vendor pushed corrupted JSON records with unescaped control characters and string data in numeric fields, halting the production ingestion stream.",
            "problem_statement": "Deploy Auto Loader quarantine pattern with `rescuedDataColumn`, isolate poison pills to a Dead Letter Queue table, and resume streaming ingestion with zero data loss.",
            "architectural_notes": "Poison pill files contain syntax or type violations that crash naive parsers. Auto Loader's `rescuedDataColumn` captures the raw unparseable JSON without failing the stream, allowing downstream quarantine routing.",
            "sections": [
                {
                    "title": "1. Rescued Data Quarantine Extraction",
                    "explanation": "Filter and route poison records to an isolated quarantine table.",
                    "code": """# Simulate separating clean records from poison pills
incoming_records = [
    {"id": 1, "val": 100.0, "_rescued_data": None},
    {"id": 2, "val": 250.0, "_rescued_data": None},
    {"id": 3, "val": None, "_rescued_data": '{"val": "CORRUPTED_HEX_TOKEN"}'}
]

df_incoming = spark.createDataFrame(incoming_records)
df_clean = df_incoming.filter(F.col("_rescued_data").isNull())
df_quarantine = df_incoming.filter(F.col("_rescued_data").isNotNull())

print(f"Clean Records Processed: {df_clean.count()}")
print(f"Poison Pills Quarantined: {df_quarantine.count()}")
assert df_quarantine.count() == 1
"""
                }
            ],
            "key_takeaways": [
                "Zero Stream Halt: Poison pills are isolated without interrupting ingestion for valid records.",
                "Root-Cause Forensics: Quarantined records preserve the exact raw payload and file source metadata.",
                "Automated Alerting: Fire PagerDuty alerts if quarantine table row count increases."
            ],
            "interview_questions": [
                "How does Auto Loader's `_rescued_data` column prevent poison pill pipeline outages?",
                "How do you safely replay quarantined records once upstream bugs are resolved?"
            ]
        },
        {
            "nb_id": "104",
            "title": "Production Incident 06: Serverless SQL Warehouse Queue Saturation & Spill Tuning",
            "filename": "104_production_incident_06_serverless_sql_warehouse_queue_saturation_and_spill_tuning.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "During Monday morning executive review, 150 dashboard users connect simultaneously to a Serverless SQL Warehouse. Queries queue for 45 seconds and spill gigabytes to disk.",
            "problem_statement": "Diagnose query queue saturation and disk spills via Spark SQL over warehouse execution history telemetry, flag overloaded clusters for Economy->Pro upgrade, and verify AQE partition coalescing.",
            "architectural_notes": "When concurrent query demand exceeds slot limits or shuffle partitions spill memory to SSDs, DBSQL P99 latencies degrade sharply. Analyzing `waiting_for_compute_ms` + `spill_to_disk_bytes` alongside AQE partition coalescing restores sub-second response times.",
            "sections": [
                {
                    "title": "1. Warehouse Queue Telemetry Diagnosis & Shuffle Partition Coalescing",
                    "explanation": "Correlate warehouse queue delays and disk spills in Spark SQL, classify congested warehouses for horizontal `Pro` autoscaling, and verify AQE coalesces tiny shuffle partitions.",
                    "code": """# Modeled after Databricks `system.compute.query_history` warehouse metrics
q_logs = [
    ("wh-exec-bi", 42000, 18 * 1024**3, 1800),
    ("wh-exec-bi", 38000, 12 * 1024**3, 1650),
    ("wh-adhoc-dev", 300, 0, 150),
]
spark.createDataFrame(
    q_logs, ["warehouse_id", "waiting_for_compute_ms", "spill_to_disk_bytes", "execution_ms"]
).createOrReplaceTempView("wh_query_history")

triage_df = spark.sql(\"\"\"
    SELECT
        warehouse_id,
        ROUND(AVG(waiting_for_compute_ms) / 1000.0, 2) AS avg_queue_sec,
        ROUND(SUM(spill_to_disk_bytes) / POW(1024, 3), 1) AS total_spill_gb,
        CASE WHEN AVG(waiting_for_compute_ms) > 10000 THEN 'UPGRADE_TO_PRO_AUTOSCALE' ELSE 'HEALTHY' END AS recommendation
    FROM wh_query_history
    GROUP BY warehouse_id
\"\"\")
recs = {r["warehouse_id"]: r["recommendation"] for r in triage_df.collect()}

# Verify Spark AQE coalesces over-partitioned small shuffles instead of spilling overhead
spark.conf.set("spark.sql.shuffle.partitions", "200")
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
agg_df = spark.range(0, 500).withColumn("grp", F.col("id") % 5).groupBy("grp").count()
actual_parts = agg_df.rdd.getNumPartitions()

print(f"Warehouse recommendations: {recs} | Coalesced partitions: {actual_parts}")
assert recs["wh-exec-bi"] == "UPGRADE_TO_PRO_AUTOSCALE" and recs["wh-adhoc-dev"] == "HEALTHY"
assert actual_parts < 200 and agg_df.count() == 5
""",
                }
            ],
            "key_takeaways": [
                "Pro Scaling Policy: Aggressively launches horizontal SQL clusters as soon as query queues form.",
                "Eliminate Spills with Liquid Clustering: Clustered Delta reads minimize shuffle memory footprints.",
                "Workload Isolation: Separate SLA-critical BI warehouses from ad-hoc exploratory endpoints.",
            ],
            "interview_questions": [
                "What is the difference between Economy and Pro scaling policies on Databricks SQL Warehouses?",
                "How do you eliminate disk spills in heavy distributed joins on SQL Warehouses?",
            ],
        },
        {
            "nb_id": "105",
            "title": "Enterprise Lakehouse Master Blueprint: End-to-End Multi-Cloud Production Architecture",
            "filename": "105_enterprise_lakehouse_master_blueprint_end_to_end_multi_cloud_production_architecture.py",
            "difficulty": "Architect",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from delta.tables import DeltaTable",
                "from pyspark.sql import Window, functions as F",
                "from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType",
            ],
            "business_scenario": "A Fortune 50 enterprise requires a unified lakehouse blueprint spanning raw Auto Loader ingestion, DLT conformance, Unity Catalog governance, DABs CI/CD, DBSQL reporting, and Mosaic AI RAG.",
            "problem_statement": "Execute a genuine end-to-end Bronze -> Quarantine & Silver -> Gold Delta Lakehouse pipeline locally: stream raw JSON landing files with corrupt rescue -> quarantine poison pills -> deduplicate & `MERGE INTO` Deletion-Vector Silver (`CHECK` enforced) -> aggregate `CLUSTER BY` Gold KPIs with full row reconciliation.",
            "architectural_notes": "The master blueprint links storage correctness (`Deletion Vectors`, `CHECK` constraints, `CDF`, `CLUSTER BY`), streaming exactly-once checkpointing, idempotent `MERGE INTO`, and additive Gold BI views into one reproducible verifiable pipeline.",
            "sections": [
                {
                    "title": "1. End-to-End Bronze Stream -> Quarantine Split -> Silver Delta MERGE -> Gold KPIs",
                    "explanation": "Execute the full multi-hop medallion pipeline in local Spark + Delta 3.2 and reconcile counts and revenue across Bronze, Quarantine, Silver, and Gold.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_105_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "raw_orders"
landing.mkdir(parents=True)
bronze_path = str(lab_dir / "bronze_orders")
dlq_path = str(lab_dir / "bronze_dlq")
silver_path = str(lab_dir / "silver_orders")
gold_path = str(lab_dir / "gold_region_kpis")

raw_json = [
    '{"order_id": "O-1", "region": "US", "amount": 100.0, "event_seq": 1}',
    '{"order_id": "O-1", "region": "US", "amount": 150.0, "event_seq": 2}',  # Update for O-1!
    '{"order_id": "O-2", "region": "EU", "amount": 250.0, "event_seq": 1}',
    '{"order_id": "O-BAD", "region": "EU", "amount": "CORRUPT"',             # Malformed JSON -> DLQ!
]
(landing / "batch_01.json").write_text("\\n".join(raw_json) + "\\n", encoding="utf-8")

raw_schema = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("region", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("event_seq", LongType(), True),
        StructField("_corrupt", StringType(), True),
    ]
)

# 1. Bronze streaming ingestion with corrupt payload isolation
q = (
    spark.readStream.format("json")
    .schema(raw_schema)
    .option("columnNameOfCorruptRecord", "_corrupt")
    .load(str(landing))
    .writeStream.format("delta")
    .option("checkpointLocation", str(lab_dir / "ckpt_bronze"))
    .trigger(availableNow=True)
    .start(bronze_path)
)
q.awaitTermination()

bronze_df = spark.read.format("delta").load(bronze_path)
bronze_df.filter(F.col("_corrupt").isNotNull()).write.format("delta").save(dlq_path)

# 2. Silver governed Delta table (Deletion Vectors + CDF + CHECK constraint)
spark.sql(f\"\"\"
    CREATE TABLE t105_silver (order_id STRING, region STRING, amount DOUBLE, event_seq BIGINT) USING DELTA
    LOCATION '{silver_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true', 'delta.enableChangeDataFeed' = 'true')
\"\"\")
spark.sql("ALTER TABLE t105_silver ADD CONSTRAINT positive_amt CHECK (amount > 0)")

valid_dedup = (
    bronze_df.filter(F.col("_corrupt").isNull())
    .withColumn("_rn", F.row_number().over(Window.partitionBy("order_id").orderBy(F.col("event_seq").desc())))
    .filter(F.col("_rn") == 1)
    .select("order_id", "region", "amount", "event_seq")
)
DeltaTable.forPath(spark, silver_path).alias("t").merge(
    valid_dedup.alias("s"), "t.order_id = s.order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# 3. Gold Liquid-Clustered BI KPI table
spark.sql(f\"\"\"
    CREATE TABLE t105_gold (region STRING, orders BIGINT, net_revenue DOUBLE) USING DELTA
    LOCATION '{gold_path}'
    CLUSTER BY (region)
\"\"\")
spark.sql(\"\"\"
    INSERT OVERWRITE t105_gold
    SELECT region, COUNT(*) AS orders, SUM(amount) AS net_revenue
    FROM t105_silver
    GROUP BY region
\"\"\")

dlq_cnt = spark.read.format("delta").load(dlq_path).count()
silver_cnt = spark.table("t105_silver").count()
gold_rev = spark.sql("SELECT SUM(net_revenue) FROM t105_gold").first()[0]
silver_rev = spark.sql("SELECT SUM(amount) FROM t105_silver").first()[0]

print(f"Master Medallion Reconciliation -> DLQ={dlq_cnt}, Silver={silver_cnt}, GoldRev=${gold_rev}")
assert dlq_cnt == 1 and silver_cnt == 2
assert gold_rev == silver_rev == 400.0
""",
                }
            ],
            "key_takeaways": [
                "Complete Medallion Integrity: End-to-end streaming Bronze, DLQ quarantine, governed Silver, and clustered Gold reconcile 100%.",
                "Modern Delta Defaults: Enable Deletion Vectors, Change Data Feed, Liquid Clustering, and storage `CHECK` constraints together.",
                "Zero Silent Failures: Corrupt vendor records divert cleanly into DLQ while valid updates upsert idempotently.",
            ],
            "interview_questions": [
                "How do all components of the Databricks Data Intelligence Platform fit together in a modern enterprise architecture?",
                "What are the top three architectural principles that differentiate a successful lakehouse implementation from a failed data swamp?",
            ],
        },
    ]

    for nb_data in notebooks:
        fname = nb_data.pop("filename")
        nb_data["module_folder"] = MODULE_FOLDER
        nb_data["module_name"] = MODULE_NAME
        content = build_notebook(**nb_data)
        write_notebook(out_dir / fname, content)
    print(f"Generated {len(notebooks)} notebooks for {MODULE_FOLDER}")

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent
    generate(base_path)
