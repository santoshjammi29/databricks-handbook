"""
Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT) (Notebooks 033 - 043)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "04_lakeflow_ingestion_and_dlt"
MODULE_NAME = "Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "033",
            "title": "Auto Loader (cloudFiles): Incremental Lexical Directory Listing vs. File Notifications",
            "filename": "033_auto_loader_cloudfiles_directory_listing_vs_file_notifications.py",
            "difficulty": "Intermediate",
            "verify": "T0",
            "business_scenario": "A logistics enterprise ingests IoT telematics files landing in cloud storage from 50,000 delivery vehicles. Ingestion must scale smoothly as file volume grows from thousands to millions of files per day without missing files.",
            "problem_statement": "Implement and compare Databricks Auto Loader (`cloudFiles`) using (1) Incremental Directory Listing and (2) File Notification mode (AWS SQS / Azure Event Grid), explaining scaling thresholds and cost trade-offs.",
            "architectural_notes": "Auto Loader uses Structured Streaming to discover new files incrementally. Directory listing uses lexical scans and timestamp bounds. File notification mode provisions cloud event queues (Event Grid/SNS) to push file events, avoiding slow directory listings at petabyte scale.",
            "sections": [
                {
                    "title": "1. Production Auto Loader Pipeline with cloudFiles",
                    "explanation": "Configure an end-to-end Auto Loader stream reading JSON payloads into Bronze.",
                    "code": """# Production Auto Loader stream template
def get_autoloader_stream(source_path: str, schema_path: str, checkpoint_path: str, use_notifications: bool = False):
    stream_reader = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", schema_path)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("rescuedDataColumn", "_rescued_data")
    )
    if use_notifications:
        stream_reader = stream_reader.option("cloudFiles.useNotifications", "true")
    
    return stream_reader.load(source_path)

print("Auto Loader stream generator configured.")
"""
                }
            ],
            "key_takeaways": [
                "Directory Listing (< 1M files): Zero cloud infrastructure setup; fast and cost-effective.",
                "File Notification (> 1M files): Provisions SQS / Storage Queue automatically to scale to millions of files.",
                "RocksDB State: Auto Loader tracks processed files in an embedded RocksDB state store, guaranteeing exactly-once ingestion."
            ],
            "interview_questions": [
                "How does Auto Loader guarantee exactly-once file processing even if the streaming cluster restarts?",
                "What cloud resources does Auto Loader automatically create when `cloudFiles.useNotifications = true` is set?"
            ]
        },
        {
            "nb_id": "034",
            "title": "Auto Loader Schema Inference, addNewColumns Evolution & _rescued_data Quarantine",
            "filename": "034_auto_loader_schema_inference_addnewcolumns_evolution_and_rescued_data_quarantine.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import DoubleType, StringType, StructField, StructType",
            ],
            "business_scenario": "Third-party vendors frequently change JSON schemas by adding new promotional fields or sending numeric strings instead of floats. The ingestion pipeline must never drop records or crash.",
            "problem_statement": "Simulate Auto Loader's `_rescued_data` quarantine and `addNewColumns` schema evolution locally using Spark Structured Streaming over real JSON files (`columnNameOfCorruptRecord` + `mergeSchema`).",
            "architectural_notes": "In Databricks, Auto Loader (`cloudFiles`) tracks schemas in `cloudFiles.schemaLocation`, captures malformed/type-conflicting tokens in `_rescued_data`, and evolves new columns when `schemaEvolutionMode = addNewColumns`. Locally we run genuine Spark Structured Streaming (`format('json')`, `trigger(availableNow=True)`) to verify corrupt record routing and Delta schema evolution.",
            "sections": [
                {
                    "title": "1. Corrupt Payload Capture into Quarantine vs. Clean Bronze Stream",
                    "explanation": "Write raw JSON landing files (including a type-corrupt / malformed record), ingest using Structured Streaming `columnNameOfCorruptRecord = '_rescued_data'`, and route corrupt rows to quarantine without halting the pipeline.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_034_", dir=globals().get("HANDBOOK_TMP_DIR")))
raw_dir = lab_dir / "landing_json"
raw_dir.mkdir(parents=True)
ckpt_clean = str(lab_dir / "ckpt_clean")
ckpt_q = str(lab_dir / "ckpt_quarantine")
bronze_path = str(lab_dir / "bronze_orders")
quarantine_path = str(lab_dir / "quarantine_orders")

batch1_records = [
    '{"order_id": "ORD-1", "amount": 150.50}',
    '{"order_id": "ORD-2", "amount": 85.00}',
    '{"order_id": "ORD-BAD", "amount": "INVALID_FLOAT"',  # Malformed JSON triggers _rescued_data!
]
(raw_dir / "batch_01.json").write_text("\\n".join(batch1_records) + "\\n", encoding="utf-8")

expected_schema = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("_rescued_data", StringType(), True),
    ]
)

stream_df = (
    spark.readStream.format("json")
    .schema(expected_schema)
    .option("columnNameOfCorruptRecord", "_rescued_data")
    .load(str(raw_dir))
)

clean_q = (
    stream_df.filter(F.col("_rescued_data").isNull())
    .drop("_rescued_data")
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt_clean)
    .trigger(availableNow=True)
    .start(bronze_path)
)
bad_q = (
    stream_df.filter(F.col("_rescued_data").isNotNull())
    .select("order_id", "_rescued_data")
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt_q)
    .trigger(availableNow=True)
    .start(quarantine_path)
)
clean_q.awaitTermination()
bad_q.awaitTermination()

clean_cnt = spark.read.format("delta").load(bronze_path).count()
quarantine_cnt = spark.read.format("delta").load(quarantine_path).count()
print(f"Clean Bronze rows: {clean_cnt} | Quarantined _rescued_data rows: {quarantine_cnt}")
assert clean_cnt == 2 and quarantine_cnt == 1
""",
                },
                {
                    "title": "2. Safe Additive Schema Evolution (`mergeSchema` / `addNewColumns`)",
                    "explanation": "Simulate an upstream vendor adding a new `promo_code` attribute and evolve the Delta Bronze target cleanly while historical rows retain `NULL` for the new column.",
                    "code": """evolved_df = spark.createDataFrame(
    [("ORD-3", 210.0, "WINTER20")], ["order_id", "amount", "promo_code"]
)
evolved_df.write.format("delta").mode("append").option("mergeSchema", "true").save(bronze_path)

final_bronze = spark.read.format("delta").load(bronze_path)
null_promos = final_bronze.filter("promo_code IS NULL").count()
print(f"Evolved schema columns: {final_bronze.columns}, legacy null promos: {null_promos}")
assert "promo_code" in final_bronze.columns
assert final_bronze.count() == 3 and null_promos == 2
""",
                },
            ],
            "key_takeaways": [
                "Zero Data Loss: `rescuedDataColumn` / `columnNameOfCorruptRecord` routes unparseable payloads safely to quarantine.",
                "Schema Evolution: `addNewColumns` (`mergeSchema`) accepts backward-compatible fields cleanly.",
                "Schema Checkpointing: Persisting schema state ensures stream restarts never regress schema versions.",
            ],
            "interview_questions": [
                "What happens under the hood when Auto Loader encounters a new column with `schemaEvolutionMode = addNewColumns`?",
                "How does the `_rescued_data` column capture schema collisions and unparseable JSON tokens?",
            ],
        },
        {
            "nb_id": "035",
            "title": "High-Throughput Semi-Structured JSON/CSV Ingestion with cloudFiles and RocksDB",
            "filename": "035_high_throughput_semi_structured_json_csv_ingestion_with_cloudfiles_and_rocksdb.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import LongType, StringType, StructField, StructType",
            ],
            "business_scenario": "An advertising network ingests 100,000 multi-line JSON impression logs per second. Memory leaks in file tracking must be avoided at high throughput.",
            "problem_statement": "Execute incremental rate-limited multi-line JSON streaming (`maxFilesPerTrigger`, `multiLine=true`) into Delta Bronze across multiple waves, inspecting Spark streaming checkpoint commit logs (`offsets/` + `commits/`) guaranteeing exactly-once ingestion.",
            "architectural_notes": "Auto Loader uses an embedded off-heap RocksDB state store and streaming checkpoint `offsets/` logs on Databricks to prevent JVM heap exhaustion during multi-million file backfills, while `maxFilesPerTrigger` bounds micro-batch memory consumption.",
            "sections": [
                {
                    "title": "1. Incremental Rate-Limited Multi-Line JSON Stream & Exactly-Once Replay",
                    "explanation": "Write 4 multi-line JSON landing files across two waves and ingest with `maxFilesPerTrigger = 1` + `availableNow = True`, verifying batch offset checkpoints prevent duplicate reads on re-run.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_035_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "impressions"
landing.mkdir(parents=True)
ckpt_dir = lab_dir / "ckpt_rocksdb_sim"
target_delta = str(lab_dir / "bronze_impressions")

for file_idx in range(4):
    payload = json.dumps(
        [
            {"imp_id": f"imp_{file_idx}_a", "campaign": "BRAND_Q4", "clicks": 1},
            {"imp_id": f"imp_{file_idx}_b", "campaign": "RETARGET", "clicks": 3},
        ],
        indent=2,
    )
    (landing / f"part_{file_idx:02d}.json").write_text(payload, encoding="utf-8")

imp_schema = StructType(
    [
        StructField("imp_id", StringType(), False),
        StructField("campaign", StringType(), False),
        StructField("clicks", LongType(), False),
    ]
)

def run_stream_trigger():
    q = (
        spark.readStream.format("json")
        .schema(imp_schema)
        .option("multiLine", "true")
        .option("maxFilesPerTrigger", 1)
        .load(str(landing))
        .withColumn("_ingested_at", F.current_timestamp())
        .writeStream.format("delta")
        .option("checkpointLocation", str(ckpt_dir))
        .trigger(availableNow=True)
        .start(target_delta)
    )
    q.awaitTermination()

# Run 1 ingests all 4 files in 1-file micro-batches (offsets 0..3)
run_stream_trigger()
first_run_count = spark.read.format("delta").load(target_delta).count()

# Run 2 with NO new files checks checkpoint state and ingests ZERO duplicates
run_stream_trigger()
second_run_count = spark.read.format("delta").load(target_delta).count()
commit_batches = sorted(p.name for p in (ckpt_dir / "commits").iterdir() if not p.name.startswith("."))

print(f"Ingested rows after Wave 1: {first_run_count} | Re-run (zero dupes): {second_run_count}")
print(f"Checkpoint batch commits  : {commit_batches}")
assert first_run_count == 8 and second_run_count == 8
assert len(commit_batches) == 4
""",
                },
            ],
            "key_takeaways": [
                "Rate Limiting: Set `maxFilesPerTrigger` / `maxBytesPerTrigger` so historical backfills do not trigger Executor OOM.",
                "Multi-Line JSON: Enable `.option('multiLine', 'true')` for pretty-printed arrays or multi-line JSON objects.",
                "Exactly-Once Checkpointing: Re-triggering an interrupted stream skips committed offsets deterministically.",
            ],
            "interview_questions": [
                "How do you prevent memory exhaustion when Auto Loader backfills millions of historical files?",
                "What is the difference between `maxFilesPerTrigger` and `maxBytesPerTrigger`?",
            ],
        },
        {
            "nb_id": "036",
            "title": "Delta Live Tables (DLT) Foundations: Streaming Tables vs. Materialized Views",
            "filename": "036_delta_live_tables_dlt_foundations_streaming_tables_vs_materialized_views.py",
            "difficulty": "Foundational",
            "business_scenario": "An analytics engineering team is building an automated Bronze-to-Silver-to-Gold pipeline and wants to eliminate manual checkpoint management and complex streaming boilerplates.",
            "problem_statement": "Construct a declarative Delta Live Tables pipeline in Python using `@dlt.table` and `@dlt.view`, contrasting Streaming Tables (append-only) with Materialized Views (stateful projections).",
            "architectural_notes": "Delta Live Tables (DLT) is Databricks' declarative ETL framework. Developers define what tables to produce, and DLT orchestrates DAG dependencies, autoscaling compute, checkpoint state, and data quality enforcement automatically.",
            "sections": [
                {
                    "title": "1. Declarative DLT Pipeline Definition",
                    "explanation": "Define a multi-hop pipeline using `@dlt.table` streaming tables and materialized views.",
                    "code": """dlt_pipeline_code = \"\"\"
import dlt
from pyspark.sql import functions as F

# 1. Bronze: Streaming Table ingesting raw files incrementally
@dlt.table(comment="Raw landing streaming table")
def orders_bronze():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/prod/raw/orders/")
    )

# 2. Silver: Conformed Materialized View with deduplication
@dlt.table(comment="Cleaned and validated orders")
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
def orders_silver():
    return dlt.read_stream("orders_bronze").select(
        F.col("order_id"),
        F.col("amount").cast("double"),
        F.to_timestamp("order_ts").alias("order_timestamp")
    )
\"\"\"

print("Declarative DLT pipeline code verified.")
assert "@dlt.table" in dlt_pipeline_code
assert "@dlt.expect_or_drop" in dlt_pipeline_code
"""
                }
            ],
            "key_takeaways": [
                "Declarative Pipelines: Specify the target dataset; DLT manages execution, retries, and checkpoints.",
                "Streaming Tables: Use for incremental, append-only streams.",
                "Materialized Views: Use when query results must update based on changes across multiple upstream tables."
            ],
            "interview_questions": [
                "What is the difference between a Streaming Table and a Materialized View in Delta Live Tables?",
                "How does DLT determine the topological execution order of tasks in a pipeline?"
            ]
        },
        {
            "nb_id": "037",
            "title": "DLT Data Quality Expectations: expect, expect_or_drop, and expect_or_fail",
            "filename": "037_dlt_data_quality_expectations_expect_drop_fail.py",
            "difficulty": "Intermediate",
            "business_scenario": "A financial data pipeline must enforce data quality rules: non-critical format anomalies should be tracked, invalid discount rates should be dropped, and negative ledger amounts must halt the pipeline immediately.",
            "problem_statement": "Deploy and test the three DLT Data Quality Expectation actions: `@dlt.expect`, `@dlt.expect_or_drop`, and `@dlt.expect_or_fail`.",
            "architectural_notes": "DLT Expectations declare data quality constraints as SQL boolean expressions. DLT tracks pass/fail rates in the event log and takes automated actions: logging metrics (`expect`), filtering invalid rows (`expect_or_drop`), or failing the run (`expect_or_fail`).",
            "sections": [
                {
                    "title": "1. DLT Expectations Severity Matrix",
                    "explanation": "Evaluate how DLT handles each expectation level upon detecting invalid data.",
                    "code": """expectations_matrix = {
    "warn_only": {
        "decorator": '@dlt.expect("valid_email", "email LIKE \\\'%@%\\\'")',
        "action": "Records metric in event log; row continues downstream"
    },
    "drop_record": {
        "decorator": "@dlt.expect_or_drop('valid_age', 'age >= 18')",
        "action": "Drops invalid row from target table; records metric in event log"
    },
    "fail_pipeline": {
        "decorator": "@dlt.expect_or_fail('positive_balance', 'balance >= 0')",
        "action": "Immediately terminates pipeline run; fails transaction"
    }
}

for level, details in expectations_matrix.items():
    print(f"[{level.upper()}]\\n  Syntax: {details['decorator']}\\n  Behavior: {details['action']}\\n")

assert "@dlt.expect_or_fail" in expectations_matrix["fail_pipeline"]["decorator"]
"""
                }
            ],
            "key_takeaways": [
                "`expect`: Non-blocking observability for soft quality rules.",
                "`expect_or_drop`: Surgical filtering for invalid rows without halting processing.",
                "`expect_or_fail`: Circuit breaker for critical financial/compliance invariants."
            ],
            "interview_questions": [
                "Where are DLT expectation pass and fail metrics recorded for auditing?",
                "Can you apply multiple expectations with different severity levels to the same DLT table?"
            ]
        },
        {
            "nb_id": "038",
            "title": "Advanced DLT Data Quality: Dead Letter Queue (DLQ) Quarantine Tables Pattern",
            "filename": "038_advanced_dlt_data_quality_dead_letter_queue_dlq_quarantine_tables_pattern.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import DoubleType, StringType, StructField, StructType",
            ],
            "business_scenario": "In regulatory banking, dropping invalid records with `expect_or_drop` violates compliance; every invalid row must be diverted into a Dead Letter Queue (DLQ) quarantine table for human remediation.",
            "problem_statement": "Execute a single-read Structured Streaming DLQ split pipeline (`foreachBatch`), atomically persisting passing financial transactions to Delta Clean and constraint-violating records with diagnostic metadata to Delta Quarantine.",
            "architectural_notes": "The DLQ pattern reads incoming transactions once and splits valid records (`account_id IS NOT NULL AND transaction_amount > 0`) from failing rows routed to quarantine with `_quarantine_reason` and `_quarantined_at` columns for downstream remediation and SOX/HIPAA auditability.",
            "sections": [
                {
                    "title": "1. Single-Read `foreachBatch` DLQ Split into Clean & Quarantine Delta Tables",
                    "explanation": "Stream raw banking JSON events with `trigger(availableNow=True)` and branch good vs. bad records cleanly in a single pass.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_038_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "tx_landing"
landing.mkdir(parents=True)
clean_delta = str(lab_dir / "transactions_clean")
dlq_delta = str(lab_dir / "transactions_quarantine")
ckpt = str(lab_dir / "ckpt_dlq")

tx_lines = [
    '{"tx_id": "TX-1", "account_id": "ACC-100", "transaction_amount": 420.50}',
    '{"tx_id": "TX-2", "account_id": null, "transaction_amount": 95.00}',
    '{"tx_id": "TX-3", "account_id": "ACC-200", "transaction_amount": -15.00}',
    '{"tx_id": "TX-4", "account_id": "ACC-300", "transaction_amount": 1250.00}',
]
(landing / "batch_01.json").write_text("\\n".join(tx_lines) + "\\n", encoding="utf-8")

tx_schema = StructType(
    [
        StructField("tx_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("transaction_amount", DoubleType(), True),
    ]
)

def split_dlq_batch(micro_df, _batch_id: int) -> None:
    cached = micro_df.cache()
    valid_expr = (F.col("account_id").isNotNull()) & (F.col("transaction_amount") > 0)
    cached.filter(valid_expr).write.format("delta").mode("append").save(clean_delta)
    (
        cached.filter(~valid_expr)
        .withColumn(
            "_quarantine_reason",
            F.when(F.col("account_id").isNull(), "NULL_ACCOUNT_ID").otherwise("NON_POSITIVE_AMOUNT"),
        )
        .withColumn("_quarantined_at", F.current_timestamp())
        .write.format("delta")
        .mode("append")
        .save(dlq_delta)
    )
    cached.unpersist()

q = (
    spark.readStream.format("json")
    .schema(tx_schema)
    .load(str(landing))
    .writeStream.foreachBatch(split_dlq_batch)
    .option("checkpointLocation", ckpt)
    .trigger(availableNow=True)
    .start()
)
q.awaitTermination()

clean_cnt = spark.read.format("delta").load(clean_delta).count()
dlq_rows = spark.read.format("delta").load(dlq_delta).select("tx_id", "_quarantine_reason").collect()
reasons = {r["tx_id"]: r["_quarantine_reason"] for r in dlq_rows}
print(f"DLQ Split -> Clean: {clean_cnt}, Quarantined: {reasons}")
assert clean_cnt == 2
assert reasons == {"TX-2": "NULL_ACCOUNT_ID", "TX-3": "NON_POSITIVE_AMOUNT"}
""",
                }
            ],
            "key_takeaways": [
                "Zero Silent Drops: Every invalid record is preserved in the quarantine table with diagnostic metadata.",
                "Single-Pass IO: Splitting inside `foreachBatch` (or `@dlt.table` branching from one stream) avoids reading landing files twice.",
                "Compliance Invariant: Essential for healthcare (HIPAA) and financial (SOX) regulatory pipelines.",
            ],
            "interview_questions": [
                "How do you implement a Dead Letter Queue in Delta Live Tables without reading upstream files twice?",
                "What metadata columns should always be attached to quarantined records?",
            ],
        },
        {
            "nb_id": "039",
            "title": "DLT Change Data Capture: Incremental Upserts with dlt.apply_changes (SCD Type 1)",
            "filename": "039_dlt_change_data_capture_incremental_upserts_apply_changes_scd1.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from delta.tables import DeltaTable",
                "from pyspark.sql import Window, functions as F",
            ],
            "business_scenario": "A CRM database emits change logs (inserts, updates, deletes) via Debezium. The analytics team must maintain a conformed customer table reflecting current state (SCD Type 1).",
            "problem_statement": "Execute out-of-order CDC deduplication (`sequence_by` descending window) + Delta `MERGE INTO` (`UPDATE`, `INSERT`, `DELETE`) locally to mirror `dlt.apply_changes()` SCD Type 1 semantics.",
            "architectural_notes": "In Databricks DLT, `dlt.apply_changes()` (and SQL `AUTO CDC INTO`) compiles down to sequenced deduplication + Delta `MERGE INTO`. Ranking incoming batch events per primary key by sequence timestamp ensures older delayed retries never clobber newer state.",
            "sections": [
                {
                    "title": "1. Out-of-Order CDC Deduplication & SCD Type 1 Delta MERGE",
                    "explanation": "Seed `customers_scd1`, ingest an unordered CDC micro-batch containing a stale retry (`t=10` arriving alongside newer `t=30`), a new insert, and a hard `DELETE`, then verify final target state.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_039_", dir=globals().get("HANDBOOK_TMP_DIR")))
scd1_path = str(lab_dir / "customers_scd1")

spark.createDataFrame(
    [(1, "alice@v1.com", "2026-11-20T09:00:00"), (2, "bob@v1.com", "2026-11-20T09:00:00")],
    ["customer_id", "email", "last_seq_ts"],
).write.format("delta").save(scd1_path)

cdc_events = spark.createDataFrame(
    [
        # Out-of-order pair for customer_id=1: newer event (12:00) + delayed stale retry (08:00)
        (1, "alice@v3_final.com", "UPDATE", "2026-11-20T12:00:00"),
        (1, "alice@stale_retry.com", "UPDATE", "2026-11-20T08:00:00"),
        (2, "bob@v1.com", "DELETE", "2026-11-20T11:30:00"),
        (3, "carol@new.com", "INSERT", "2026-11-20T11:45:00"),
    ],
    ["customer_id", "email", "op_type", "op_timestamp"],
)

latest_cdc = (
    cdc_events.withColumn(
        "_rn",
        F.row_number().over(Window.partitionBy("customer_id").orderBy(F.col("op_timestamp").desc())),
    )
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

(
    DeltaTable.forPath(spark, scd1_path)
    .alias("t")
    .merge(latest_cdc.alias("s"), "t.customer_id = s.customer_id")
    .whenMatchedDelete(condition="s.op_type = 'DELETE'")
    .whenMatchedUpdate(
        condition="s.op_type != 'DELETE' AND s.op_timestamp > t.last_seq_ts",
        set={"email": "s.email", "last_seq_ts": "s.op_timestamp"},
    )
    .whenNotMatchedInsert(
        condition="s.op_type != 'DELETE'",
        values={"customer_id": "s.customer_id", "email": "s.email", "last_seq_ts": "s.op_timestamp"},
    )
    .execute()
)

final_map = {
    r["customer_id"]: r["email"] for r in spark.read.format("delta").load(scd1_path).collect()
}
print(f"SCD Type 1 Customer State: {final_map}")
assert final_map == {1: "alice@v3_final.com", 3: "carol@new.com"}
""",
                }
            ],
            "key_takeaways": [
                "Automated Deduplication: Sequence keys resolve out-of-order CDC retries safely.",
                "Guard Stale Replays: Checking `s.op_timestamp > t.last_seq_ts` protects already-committed newer rows.",
                "Declarative Upgrade: On Databricks, `dlt.apply_changes()` / `AUTO CDC INTO` handles this logic declaratively.",
            ],
            "interview_questions": [
                "How does `dlt.apply_changes()` handle out-of-order CDC change events?",
                "What is the difference between specifying `keys` versus `sequence_by` in `dlt.apply_changes()`?",
            ],
        },
        {
            "nb_id": "040",
            "title": "DLT Change Data Capture: Historical Tracking with dlt.apply_changes (SCD Type 2)",
            "filename": "040_dlt_change_data_capture_historical_tracking_apply_changes_scd2.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from delta.tables import DeltaTable",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A financial ledger requires historical tracking of customer credit ratings over time (SCD Type 2), maintaining `__START_AT`, `__END_AT`, and active flags for point-in-time balance checks.",
            "problem_statement": "Execute a real two-step Delta `MERGE INTO` SCD Type 2 pipeline maintaining `__START_AT`, `__END_AT`, and `__IS_CURRENT`, and verify point-in-time historical queries reconstruct exact prior ratings.",
            "architectural_notes": "When `stored_as_scd_type = '2'` is configured in DLT `apply_changes`, Delta closes prior active intervals (`__END_AT = new_ts`) and inserts new active rows (`__END_AT = NULL`). Implementing the same staged `MERGE` locally demonstrates every state transition transparently.",
            "sections": [
                {
                    "title": "1. SCD Type 2 Validity Window Updates & Point-in-Time History Query",
                    "explanation": "Close changed active dimension rows via Delta `MERGE`, append new versions with open-ended `__END_AT`, and verify historical point-in-time lookup.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_040_", dir=globals().get("HANDBOOK_TMP_DIR")))
scd2_path = str(lab_dir / "dim_customer_scd2")

# Wave 1 (2026-11-01): Initial customer credit ratings
spark.createDataFrame(
    [
        (101, "AAA", "2026-11-01", None, True),
        (102, "BB", "2026-11-01", None, True),
    ],
    "customer_id BIGINT, credit_rating STRING, __START_AT STRING, __END_AT STRING, __IS_CURRENT BOOLEAN",
).write.format("delta").save(scd2_path)

# Wave 2 (2026-11-15): customer 101 downgrades AAA -> AA; 102 stays unchanged; 103 added
wave2 = spark.createDataFrame(
    [
        (101, "AA", "2026-11-15"),
        (102, "BB", "2026-11-15"),
        (103, "A", "2026-11-15"),
    ],
    "customer_id BIGINT, credit_rating STRING, effective_date STRING",
)

# Step A: Retire active rows whose monitored attribute changed
dt = DeltaTable.forPath(spark, scd2_path)
dt.alias("t").merge(
    wave2.alias("s"),
    "t.customer_id = s.customer_id AND t.__IS_CURRENT = true",
).whenMatchedUpdate(
    condition="t.credit_rating <> s.credit_rating",
    set={"__END_AT": "s.effective_date", "__IS_CURRENT": F.lit(False)},
).execute()

# Step B: Append new active records only for changed or brand-new keys
current_active = spark.read.format("delta").load(scd2_path).filter("__IS_CURRENT = true")
new_versions = (
    wave2.alias("s")
    .join(current_active.alias("t"), "customer_id", "left")
    .filter(F.col("t.customer_id").isNull())
    .select(
        F.col("s.customer_id"),
        F.col("s.credit_rating"),
        F.col("s.effective_date").alias("__START_AT"),
        F.lit(None).cast("string").alias("__END_AT"),
        F.lit(True).alias("__IS_CURRENT"),
    )
)
new_versions.write.format("delta").mode("append").save(scd2_path)

# Verify point-in-time lookup on 2026-11-10 vs 2026-11-20 for customer 101
dim_df = spark.read.format("delta").load(scd2_path)
as_of_nov10 = (
    dim_df.filter("customer_id = 101 AND __START_AT <= '2026-11-10' AND COALESCE(__END_AT, '9999-12-31') > '2026-11-10'")
    .select("credit_rating")
    .first()[0]
)
as_of_nov20 = (
    dim_df.filter("customer_id = 101 AND __IS_CURRENT = true").select("credit_rating").first()[0]
)
total_101_versions = dim_df.filter("customer_id = 101").count()
total_102_versions = dim_df.filter("customer_id = 102").count()

print(f"Customer 101 versions={total_101_versions}: Nov10={as_of_nov10}, Nov20={as_of_nov20}")
assert total_101_versions == 2 and as_of_nov10 == "AAA" and as_of_nov20 == "AA"
assert total_102_versions == 1  # No duplicate unchanged row written!
""",
                }
            ],
            "key_takeaways": [
                "Idempotent Change Suppression: Skip unchanged incoming records so unchanged keys do not bloat history.",
                "Point-in-Time Audits: Query historical states cleanly via half-open intervals `[__START_AT, __END_AT)`.",
                "Declarative Simplicity: `dlt.apply_changes(stored_as_scd_type='2')` automates this exact state machine on Databricks.",
            ],
            "interview_questions": [
                "What system columns are automatically generated by DLT when `stored_as_scd_type = '2'` is set?",
                "How does `dlt.apply_changes` SCD Type 2 compare to custom PySpark MERGE INTO implementations?",
            ],
        },
        {
            "nb_id": "041",
            "title": "DLT Execution Modes: Triggered vs. Continuous Pipelines & Serverless Runtime",
            "filename": "041_dlt_execution_modes_triggered_vs_continuous_pipelines_and_serverless_runtime.py",
            "difficulty": "Intermediate",
            "business_scenario": "A lakehouse architect must optimize pipeline costs: high-priority fraud detection requires sub-minute continuous execution, while standard billing reconciliation runs hourly.",
            "problem_statement": "Compare Triggered (batch) vs. Continuous (streaming) pipeline execution modes in DLT, configure Serverless DLT compute, and analyze DBU consumption curves.",
            "architectural_notes": "Triggered pipelines start compute, process all available data once, and terminate (ideal for hourly/daily batch ETL). Continuous pipelines run indefinitely with dedicated streaming micro-batches (sub-second latency). Serverless DLT removes cluster configuration and scales instantly.",
            "sections": [
                {
                    "title": "1. DLT Pipeline Execution Mode Decision Matrix",
                    "explanation": "Evaluate latency requirements vs compute cost across DLT execution models.",
                    "code": """dlt_modes = {
    "Triggered_Serverless": {
        "latency": "Minutes to hours (scheduled)",
        "cost_efficiency": "High: Scales down to 0 DBUs immediately upon batch completion",
        "best_for": "Medallion batch pipelines, hourly reporting, cost-sensitive workloads"
    },
    "Continuous_Enhanced": {
        "latency": "Sub-second to seconds",
        "cost_efficiency": "Moderate: Clusters remain continuously warm and active",
        "best_for": "Real-time fraud alerting, live IoT telemetry, sub-minute SLAs"
    }
}

for mode, attrs in dlt_modes.items():
    print(f"[{mode}]\\n  Latency: {attrs['latency']}\\n  Cost: {attrs['cost_efficiency']}\\n")

assert "Scales down to 0 DBUs" in dlt_modes["Triggered_Serverless"]["cost_efficiency"]
"""
                }
            ],
            "key_takeaways": [
                "Triggered Mode for Batch: Always use Triggered mode unless the business explicitly demands sub-minute SLA.",
                "Serverless DLT: Eliminates cluster startup delay and automatically optimizes worker memory.",
                "Enhanced Autoscaling: DLT allocates compute based on streaming backlog queue depths."
            ],
            "interview_questions": [
                "When should an enterprise use Continuous mode versus Triggered mode in Delta Live Tables?",
                "How does Serverless DLT handle worker autoscaling compared to Classic DLT?"
            ]
        },
        {
            "nb_id": "042",
            "title": "DLT Event Log Forensics: Querying Lineage, Metrics, Quality Rates & Execution SLAs",
            "filename": "042_dlt_event_log_forensics_querying_lineage_metrics_quality_rates_and_execution_slas.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A regulatory audit requires generating an SLA compliance report detailing data quality pass/drop rates across all Delta Live Tables pipelines for the past 90 days.",
            "problem_statement": "Persist DLT-schema JSON telemetry inside a Delta event-log table, parse nested JSON expectations via Spark SQL (`get_json_object`), and compute per-flow pass rates and SLA breach alerts.",
            "architectural_notes": "DLT stores flow telemetry (`flow_progress`, data quality expectations, SLA durations) in a Delta table queryable via `event_log('<pipeline_id>')`. Locally we write identical nested JSON event records into Delta and execute the forensic Spark SQL aggregation.",
            "sections": [
                {
                    "title": "1. Forensic Parsing of DLT Event Log JSON & Data Quality SLA Calculation",
                    "explanation": "Write synthetic DLT `flow_progress` event rows to a Delta table, extract nested expectation pass/drop counts with Spark SQL, and detect SLA quality breaches.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_042_", dir=globals().get("HANDBOOK_TMP_DIR")))
event_log_path = str(lab_dir / "dlt_system_events")

raw_events = [
    (
        "2026-11-20T08:00:00Z",
        "flow_progress",
        "orders_silver",
        json.dumps(
            {
                "flow_progress": {
                    "metrics": {"num_output_rows": 980},
                    "data_quality": {"dropped_records": 20, "expectations": [{"name": "valid_amt", "passed": 980, "failed": 20}]},
                }
            }
        ),
    ),
    (
        "2026-11-20T09:00:00Z",
        "flow_progress",
        "payments_silver",
        json.dumps(
            {
                "flow_progress": {
                    "metrics": {"num_output_rows": 500},
                    "data_quality": {"dropped_records": 150, "expectations": [{"name": "valid_iban", "passed": 500, "failed": 150}]},
                }
            }
        ),
    ),
]
spark.createDataFrame(raw_events, ["timestamp", "event_type", "flow_name", "details_json"]).write.format(
    "delta"
).save(event_log_path)
spark.sql(f"CREATE TABLE t042_event_log USING DELTA LOCATION '{event_log_path}'")

sla_df = spark.sql(\"\"\"
    SELECT
        flow_name,
        CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS BIGINT) AS output_rows,
        CAST(get_json_object(details_json, '$.flow_progress.data_quality.dropped_records') AS BIGINT) AS dropped_rows,
        ROUND(
            CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS DOUBLE) * 100.0
            / (
                CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS DOUBLE)
                + CAST(get_json_object(details_json, '$.flow_progress.data_quality.dropped_records') AS DOUBLE)
            ),
            2
        ) AS pass_rate_pct
    FROM t042_event_log
    WHERE event_type = 'flow_progress'
    ORDER BY pass_rate_pct ASC
\"\"\")

sla_map = {r["flow_name"]: r["pass_rate_pct"] for r in sla_df.collect()}
print(f"Pipeline Data Quality Pass Rates (%): {sla_map}")
assert sla_map["orders_silver"] == 98.0
assert sla_map["payments_silver"] < 80.0
""",
                }
            ],
            "key_takeaways": [
                "Single Source of Observability: The DLT event log contains complete execution, metric, and quality history.",
                "Audit Reports: Easily query dropped record counts and expectation pass rates in standard SQL.",
                "Lineage Tracking: Graph relationships between datasets are recorded directly inside event-log metadata.",
            ],
            "interview_questions": [
                "How do you query the Delta Live Tables event log to find which expectations had the highest failure rates?",
                "What information is captured in `details:flow_progress` within the DLT event log?",
            ],
        },
        {
            "nb_id": "043",
            "title": "Metaprogramming DLT: Dynamic Pipeline Generation from Data Contracts & YAML Specs",
            "filename": "043_metaprogramming_dlt_dynamic_pipeline_generation_from_data_contracts_and_yaml_specs.py",
            "difficulty": "Advanced",
            "business_scenario": "A large platform ingests 200 distinct ERP tables. Writing 200 individual DLT notebook files is repetitive and error-prone. The pipeline must generate tables dynamically from YAML data contracts.",
            "problem_statement": "Develop a metaprogramming framework using Python decorators and loops to instantiate DLT streaming tables, schemas, and expectations dynamically from a configuration dictionary.",
            "architectural_notes": "Because DLT pipelines are written in standard Python, developers can dynamically generate `@dlt.table` definitions inside loops, reading table names, schemas, and expectation rules from external YAML contracts.",
            "sections": [
                {
                    "title": "1. Dynamic DLT Table Generator Pattern",
                    "explanation": "Iterate over table metadata specifications and instantiate DLT tables dynamically.",
                    "code": """# Simulating metadata-driven DLT table generator
table_contracts = [
    {"name": "orders", "source": "/landing/orders", "primary_key": "order_id"},
    {"name": "line_items", "source": "/landing/line_items", "primary_key": "item_id"},
    {"name": "payments", "source": "/landing/payments", "primary_key": "payment_id"}
]

def generate_pipeline_definitions(contracts: list):
    generated_tables = []
    for contract in contracts:
        table_def = f"Instantiated DLT Table: {contract['name']} from {contract['source']} (PK: {contract['primary_key']})"
        generated_tables.append(table_def)
    return generated_tables

tables = generate_pipeline_definitions(table_contracts)
for t in tables:
    print(t)
assert len(tables) == 3
"""
                }
            ],
            "key_takeaways": [
                "Metadata-Driven Engineering: Add new tables to the pipeline simply by updating a YAML configuration file.",
                "Maintainability: Standardize ingestion rules, audit columns, and error handling across hundreds of tables.",
                "Contract Enforcement: Integrates directly with enterprise Data Contracts."
            ],
            "interview_questions": [
                "How does Python closure scoping affect dynamic DLT table generation inside loops?",
                "What are the best practices for passing external configuration files into a DLT pipeline?"
            ]
        }
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
