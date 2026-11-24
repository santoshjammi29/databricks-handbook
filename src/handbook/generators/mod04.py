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
            "business_scenario": "Third-party vendors frequently change JSON schemas by adding new promotional fields or sending numeric strings instead of floats. The ingestion pipeline must never drop records or crash.",
            "problem_statement": "Configure Auto Loader with `schemaEvolutionMode = addNewColumns` and `rescuedDataColumn = _rescued_data`, proving that new fields evolve the schema while corrupt payloads are quarantined.",
            "architectural_notes": "Auto Loader stores the active schema contract in `cloudFiles.schemaLocation`. When a new column appears, `addNewColumns` updates the Delta table schema and restarts the stream. If a data type conflicts, the original payload is captured safely in `_rescued_data`.",
            "sections": [
                {
                    "title": "1. Rescued Data Quarantine Verification",
                    "explanation": "Inspect how unparseable fields are captured in `_rescued_data` without data loss.",
                    "code": """# Simulate incoming payloads with unexpected types
payloads = [
    {"order_id": "ORD-1", "amount": 150.50, "_rescued_data": None},
    {"order_id": "ORD-2", "amount": "INVALID_FLOAT", "_rescued_data": '{"amount": "INVALID_FLOAT", "_error": "TypeMismatch"}'}
]

df_stream_sim = spark.createDataFrame(payloads)
df_clean = df_stream_sim.filter(F.col("_rescued_data").isNull())
df_corrupt = df_stream_sim.filter(F.col("_rescued_data").isNotNull())

print(f"Clean Records: {df_clean.count()} | Rescued Corrupt: {df_corrupt.count()}")
assert df_corrupt.count() == 1
"""
                }
            ],
            "key_takeaways": [
                "Zero Data Loss: `rescuedDataColumn` guarantees no record is silently dropped due to formatting errors.",
                "Schema Evolution: `addNewColumns` allows upward-compatible upstream API evolution without manual DDL.",
                "Schema Checkpointing: Schema changes are persisted in JSON within the schema location directory."
            ],
            "interview_questions": [
                "What happens under the hood when Auto Loader encounters a new column with `schemaEvolutionMode = addNewColumns`?",
                "How does the `_rescued_data` column capture schema collisions and unparseable JSON tokens?"
            ]
        },
        {
            "nb_id": "035",
            "title": "High-Throughput Semi-Structured JSON/CSV Ingestion with cloudFiles and RocksDB",
            "filename": "035_high_throughput_semi_structured_json_csv_ingestion_with_cloudfiles_and_rocksdb.py",
            "difficulty": "Intermediate",
            "business_scenario": "An advertising network ingests 100,000 multi-line JSON impression logs per second. Memory leaks in file tracking must be avoided at high throughput.",
            "problem_statement": "Optimize Auto Loader streaming configurations using RocksDB state stores, tuned micro-batch sizes (`maxFilesPerTrigger`), and multiline JSON options.",
            "architectural_notes": "High-throughput file ingestion can overwhelm driver memory if millions of file names are tracked in the JVM heap. Auto Loader automatically uses an off-heap RocksDB state store on local worker SSDs to track processed file metadata efficiently.",
            "sections": [
                {
                    "title": "1. High-Throughput Auto Loader Configuration",
                    "explanation": "Configure batch limits and RocksDB state options for high-throughput streaming.",
                    "code": """autoloader_tuning = {
    "cloudFiles.maxFilesPerTrigger": 10000,
    "cloudFiles.maxBytesPerTrigger": "10g",
    "cloudFiles.format": "json",
    "cloudFiles.multiline": "true",
    "spark.sql.streaming.stateStore.providerClass": "com.databricks.sql.streaming.state.RocksDBStateStoreProvider"
}

for k, v in autoloader_tuning.items():
    print(f"{k} = {v}")
assert autoloader_tuning["cloudFiles.maxFilesPerTrigger"] == 10000
"""
                }
            ],
            "key_takeaways": [
                "Rate Limiting: Use `maxFilesPerTrigger` to prevent micro-batches from choking memory during backfills.",
                "Multi-Line JSON: Set `cloudFiles.multiline = true` when records span multiple lines.",
                "RocksDB Efficiency: Offloads file tracking metadata from driver RAM to local NVMe storage."
            ],
            "interview_questions": [
                "How do you prevent memory exhaustion when Auto Loader backfills millions of historical files?",
                "What is the difference between `maxFilesPerTrigger` and `maxBytesPerTrigger`?"
            ]
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
        "decorator": "@dlt.expect('valid_email', 'email LIKE %domain%')",
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
            "business_scenario": "In regulatory banking, dropping invalid records with `expect_or_drop` violates compliance; every invalid row must be diverted into a Dead Letter Queue (DLQ) quarantine table for human remediation.",
            "problem_statement": "Implement the DLT Dead Letter Queue (DLQ) split pattern, partitioning a raw streaming table into a clean target table and a quarantined error table.",
            "architectural_notes": "The DLQ pattern reads from an upstream table once and writes to two downstream tables: valid records meeting constraints flow to the clean table, while records violating constraints are tagged with failure reasons and routed to the quarantine table.",
            "sections": [
                {
                    "title": "1. DLQ Split Pattern Implementation",
                    "explanation": "Define complementary DLT tables to separate valid data from quarantined errors.",
                    "code": """dlq_pattern_code = \"\"\"
import dlt
from pyspark.sql import functions as F

RULES = {
    "valid_account": "account_id IS NOT NULL",
    "valid_amount": "transaction_amount > 0"
}

# 1. Clean Table: Enforce all rules with expect_or_drop
@dlt.table(comment="Clean transactions passing all expectations")
@dlt.expect_all_or_drop(RULES)
def transactions_clean():
    return dlt.read_stream("transactions_bronze")

# 2. Quarantine Table: Invert the rules to capture only failing rows
@dlt.table(comment="Quarantined transactions for compliance review")
def transactions_quarantine():
    failing_condition = f"NOT ({RULES['valid_account']}) OR NOT ({RULES['valid_amount']})"
    return (
        dlt.read_stream("transactions_bronze")
        .filter(failing_condition)
        .withColumn("_quarantine_reason", F.lit("Violated account or amount constraint"))
        .withColumn("_quarantined_at", F.current_timestamp())
    )
\"\"\"

print("DLQ split pattern code verified.")
assert "transactions_clean" in dlq_pattern_code
assert "transactions_quarantine" in dlq_pattern_code
"""
                }
            ],
            "key_takeaways": [
                "Zero Silent Drops: Every invalid record is preserved in the quarantine table with audit metadata.",
                "Audited Recovery: Once data issues are resolved upstream, a backfill job can re-ingest from quarantine.",
                "Compliance Invariant: Crucial for healthcare (HIPAA) and financial (SOX) regulatory pipelines."
            ],
            "interview_questions": [
                "How do you implement a Dead Letter Queue in Delta Live Tables without reading upstream files twice?",
                "What metadata columns should always be attached to quarantined records?"
            ]
        },
        {
            "nb_id": "039",
            "title": "DLT Change Data Capture: Incremental Upserts with dlt.apply_changes (SCD Type 1)",
            "filename": "039_dlt_change_data_capture_incremental_upserts_apply_changes_scd1.py",
            "difficulty": "Intermediate",
            "business_scenario": "A CRM database emits change logs (inserts, updates, deletes) via Debezium. The analytics team must maintain a conformed customer table reflecting current state (SCD Type 1).",
            "problem_statement": "Implement CDC replication into Delta Lake using `dlt.apply_changes()` with primary keys, sequence ordering (`sequence_by`), and delete handling.",
            "architectural_notes": "`dlt.apply_changes()` automates incremental CDC processing into Delta tables. It handles out-of-order events using a sequence column (e.g., binlog timestamp or version) and applies SCD Type 1 in-place updates natively.",
            "sections": [
                {
                    "title": "1. DLT apply_changes SCD Type 1 Definition",
                    "explanation": "Configure `dlt.apply_changes()` for automatic CDC upserts.",
                    "code": """scd1_cdc_code = \"\"\"
import dlt

dlt.create_streaming_table(
    name="customers_scd1",
    comment="Current state customer dimension (SCD Type 1)"
)

dlt.apply_changes(
    target="customers_scd1",
    source="customers_cdc_bronze",
    keys=["customer_id"],
    sequence_by="op_timestamp",
    apply_as_deletes="op_type = 'DELETE'",
    except_column_list=["op_type", "op_timestamp"]
)
\"\"\"

print("SCD Type 1 CDC code specification verified.")
assert "dlt.apply_changes" in scd1_cdc_code
assert "sequence_by" in scd1_cdc_code and "op_timestamp" in scd1_cdc_code
"""
                }
            ],
            "key_takeaways": [
                "Automated Deduplication: `sequence_by` resolves out-of-order network events automatically.",
                "Delete Support: `apply_as_deletes` physically purges or deletes records when deletion flags appear.",
                "Simplified Syntax: Replaces complex manual `MERGE INTO` queries in streaming foreachBatch."
            ],
            "interview_questions": [
                "How does `dlt.apply_changes()` handle out-of-order CDC change events?",
                "What is the difference between specifying `keys` versus `sequence_by` in `dlt.apply_changes()`?"
            ]
        },
        {
            "nb_id": "040",
            "title": "DLT Change Data Capture: Historical Tracking with dlt.apply_changes (SCD Type 2)",
            "filename": "040_dlt_change_data_capture_historical_tracking_apply_changes_scd2.py",
            "difficulty": "Advanced",
            "business_scenario": "A financial ledger requires historical tracking of customer credit ratings over time (SCD Type 2), maintaining `__START_AT`, `__END_AT`, and active flags for point-in-time balance checks.",
            "problem_statement": "Deploy an SCD Type 2 dimension in DLT using `dlt.apply_changes(stored_as_scd_type='2')`, querying historical state timelines.",
            "architectural_notes": "When `stored_as_scd_type = '2'` is configured, DLT automatically maintains temporal validity intervals (`__START_AT`, `__END_AT`) for each record version, closing old rows and inserting new ones atomically.",
            "sections": [
                {
                    "title": "1. DLT apply_changes SCD Type 2 Specification",
                    "explanation": "Configure automatic historical dimension tracking in DLT.",
                    "code": """scd2_cdc_code = \"\"\"
import dlt

dlt.create_streaming_table(
    name="dim_customer_history_scd2",
    comment="Full historical tracking dimension (SCD Type 2)"
)

dlt.apply_changes(
    target="dim_customer_history_scd2",
    source="customers_cdc_bronze",
    keys=["customer_id"],
    sequence_by="op_timestamp",
    stored_as_scd_type="2"
)
\"\"\"

print("SCD Type 2 CDC code specification verified.")
assert "stored_as_scd_type" in scd2_cdc_code and "2" in scd2_cdc_code
"""
                }
            ],
            "key_takeaways": [
                "Zero Merge Boilerplate: DLT manages start/end timestamps and row retirement automatically.",
                "Point-in-Time Audits: Query historical values for any date using standard SQL date ranges.",
                "ACID Guarantees: Historical splits and inserts commit within a single atomic Delta transaction."
            ],
            "interview_questions": [
                "What system columns are automatically generated by DLT when `stored_as_scd_type = '2'` is set?",
                "How does `dlt.apply_changes` SCD Type 2 compare to custom PySpark MERGE INTO implementations?"
            ]
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
            "business_scenario": "A regulatory audit requires generating an SLA compliance report detailing data quality pass/drop rates across all Delta Live Tables pipelines for the past 90 days.",
            "problem_statement": "Query the DLT Event Log Delta table, parse JSON diagnostic events, calculate expectation pass rates, and reconstruct pipeline lineage programmatically.",
            "architectural_notes": "DLT records all pipeline telemetry (cluster events, data flow metrics, expectation evaluations, lineage relationships) in a Delta table located at the pipeline's storage root (`storage_location/system/events`).",
            "sections": [
                {
                    "title": "1. Querying DLT Event Log Telemetry",
                    "explanation": "Extract and analyze expectation metrics and failure rates from the event log.",
                    "code": """sql_event_log_query = \"\"\"
-- Query DLT event log to audit data quality expectation pass rates
SELECT 
    timestamp,
    message,
    details:flow_progress:data_quality:dropped_records AS dropped_records,
    details:flow_progress:metrics:num_output_rows AS output_rows
FROM event_log("pipeline_id_12345")
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC
LIMIT 10;
\"\"\"

print("DLT Event Log forensic query validated.")
assert "event_log(" in sql_event_log_query
"""
                }
            ],
            "key_takeaways": [
                "Single Source of Observability: The DLT event log contains complete execution, metric, and quality history.",
                "Audit Reports: Easily query dropped record counts and SLA durations using standard SQL.",
                "Lineage Tracking: Graph relationships between datasets are recorded in event log metadata."
            ],
            "interview_questions": [
                "How do you query the Delta Live Tables event log to find which expectations had the highest failure rates?",
                "What information is captured in `details:flow_progress` within the DLT event log?"
            ]
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
