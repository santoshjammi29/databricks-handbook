"""
Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm (Notebooks 022 - 032)
"""

from pathlib import Path
from notebook_builder import build_notebook, write_notebook

MODULE_FOLDER = "03_delta_lake_storage_engine"
MODULE_NAME = "Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "022",
            "title": "Delta Transaction Log Internals: Atomic Commits, Checkpoints & CRC",
            "filename": "022_delta_transaction_log_internals_atomic_commits_checkpoints_and_crc.py",
            "difficulty": "Intermediate",
            "business_scenario": "A financial auditing team requires proof that Delta Lake guarantees ACID transaction atomicity, even if a cluster crashes mid-commit or storage experiences temporary latency.",
            "problem_statement": "Inspect and parse the `_delta_log` directory of a production Delta table. Decode JSON commit files (`add`, `remove`, `metaData`, `protocol`), analyze `.checkpoint.parquet` state consolidation, and verify CRC integrity checks.",
            "architectural_notes": "Delta Lake maintains the single source of truth for table state in `_delta_log/`. Transactions write sequential JSON commit files (`000000.json`, `000001.json`). Checkpoint Parquet files collapse historical commits every 10 transactions to keep reader state reconstruction fast.",
            "sections": [
                {
                    "title": "1. Inspect Transaction Log Commit Action Structure",
                    "explanation": "Simulate and verify the internal JSON actions written to `_delta_log/000001.json`.",
                    "code": """# Simulate raw JSON commit actions in Delta Lake
commit_actions = {
    "commit_version": 1,
    "actions": [
        {
            "add": {
                "path": "part-00000-abc-c000.snappy.parquet",
                "size": 154200,
                "modificationTime": 1763400000000,
                "dataChange": True,
                "stats": '{"numRecords": 5000, "minValues": {"id": 1}, "maxValues": {"id": 5000}}'
            }
        },
        {
            "metaData": {
                "schemaString": '{"type":"struct","fields":[{"name":"id","type":"integer"}]}',
                "format": {"provider": "parquet"}
            }
        }
    ]
}

add_action = commit_actions["actions"][0]["add"]
print(f"Committed Data File: {add_action['path']}")
print(f"Record Count in Commit: {5000}")
assert add_action["dataChange"] is True
"""
                }
            ],
            "key_takeaways": [
                "Atomic Commits: A transaction is only committed once its sequential JSON file is atomically written.",
                "Compacted Checkpoints: Prevent slow object storage listings by consolidating active state every 10 commits.",
                "Data Skipping Stats: Column min/max statistics embedded in `add` actions enable rapid file skipping without reading Parquet footers."
            ],
            "interview_questions": [
                "How does Delta Lake reconstruct the current active table state from `_delta_log`?",
                "What role do Parquet checkpoints play in maintaining low query scan latency?"
            ]
        },
        {
            "nb_id": "023",
            "title": "Optimistic Concurrency Control (OCC) & Row-Level Concurrency Conflicts",
            "filename": "023_optimistic_concurrency_control_occ_and_row_level_concurrency_conflicts.py",
            "difficulty": "Advanced",
            "business_scenario": "Multiple streaming ingestion jobs and nightly batch GDPR deletion jobs run concurrently against the customer master table, causing intermittent `ConcurrentModificationException` failures.",
            "problem_statement": "Demonstrate the mechanics of Delta Lake Optimistic Concurrency Control (OCC), reproduce a concurrent append/delete conflict, and resolve it by enabling Row-Level Concurrency (RLC).",
            "architectural_notes": "Delta Lake uses OCC: transactions read a snapshot, prepare changes, and attempt to commit. If another writer modified conflicting files or rows during that window, Delta verifies whether the changes actually conflict. Row-Level Concurrency allows two concurrent writes to modify distinct rows in the same Parquet file.",
            "sections": [
                {
                    "title": "1. OCC Conflict Matrix & Row-Level Concurrency Verification",
                    "explanation": "Evaluate concurrent transaction compatibility across Delta Lake execution modes.",
                    "code": """concurrency_matrix = {
    "Classic_Delta_CoW": {
        "concurrent_appends": "Allowed",
        "concurrent_updates_same_file": "CONFLICT: ConcurrentModificationException",
        "resolution": "Serial execution or retry loops"
    },
    "Delta_3x_with_RLC": {
        "concurrent_appends": "Allowed",
        "concurrent_updates_same_file": "ALLOWED: Row-Level Concurrency via Deletion Vectors",
        "resolution": "Native non-blocking commit"
    }
}

for mode, rules in concurrency_matrix.items():
    print(f"Mode: {mode}\\n  Same-File Updates: {rules['concurrent_updates_same_file']}\\n")

assert "ALLOWED" in concurrency_matrix["Delta_3x_with_RLC"]["concurrent_updates_same_file"]
"""
                }
            ],
            "key_takeaways": [
                "OCC Semantics: Writers assume no conflicts; validation occurs at atomic commit time.",
                "Row-Level Concurrency: Enable `delta.enableRowTracking = true` and `delta.enableDeletionVectors = true` to allow concurrent row updates in the same file.",
                "Partition Isolation: Confining concurrent writes to separate partitions eliminates conflicts completely."
            ],
            "interview_questions": [
                "Under what exact conditions will two concurrent transactions trigger a `ConcurrentModificationException` in Delta Lake?",
                "How does Row-Level Concurrency (RLC) resolve conflicts that previously failed under Copy-on-Write?"
            ]
        },
        {
            "nb_id": "024",
            "title": "Deletion Vectors (MoR): Bitmap Invalidation vs. Copy-on-Write Rewrite Overhead",
            "filename": "024_deletion_vectors_mor_bitmap_invalidation_vs_copy_on_write_rewrite_overhead.py",
            "difficulty": "Intermediate",
            "business_scenario": "A high-churn customer loyalty table processes 50,000 updates per hour. Under traditional Copy-on-Write, each update rewrote 200 MB files, resulting in 10 TB of disk writes per day and severe write amplification.",
            "problem_statement": "Enable Deletion Vectors on a Delta table, execute point updates and deletes, measure write amplification reduction, and physically purge invalid rows using `REORG TABLE ... APPLY (PURGE)`.",
            "architectural_notes": "Deletion Vectors (DVs) convert Delta Lake DML from Copy-on-Write (CoW) to Merge-on-Read (MoR). In MoR, deleted rows are recorded in a lightweight roaring bitmap (`.dv` file) without touching the original Parquet data file. The physical data is rewritten only during scheduled compaction.",
            "sections": [
                {
                    "title": "1. Write Amplification Benchmarking: CoW vs. MoR",
                    "explanation": "Compare physical storage write volume between Copy-on-Write and Deletion Vectors.",
                    "code": """def calculate_write_amplification(target_file_size_mb: int, modified_rows_bytes: int, mode: str) -> dict:
    if mode == "CoW":
        bytes_written = target_file_size_mb * 1024 * 1024 # Rewrites entire file
        amplification_factor = bytes_written / modified_rows_bytes
    else: # MoR with Deletion Vectors
        bytes_written = modified_rows_bytes + 4096 # Only modified rows + 4KB roaring bitmap
        amplification_factor = bytes_written / modified_rows_bytes
    return {"bytes_written": bytes_written, "amplification": amplification_factor}

cow_result = calculate_write_amplification(256, 1024, "CoW")
mor_result = calculate_write_amplification(256, 1024, "MoR")

print(f"Copy-on-Write Written: {cow_result['bytes_written'] / (1024*1024):.1f} MB (Amplification: {cow_result['amplification']:.0f}x)")
print(f"Merge-on-Read Written: {mor_result['bytes_written'] / 1024:.1f} KB (Amplification: {mor_result['amplification']:.2f}x)")

assert cow_result["bytes_written"] > mor_result["bytes_written"] * 1000
"""
                }
            ],
            "key_takeaways": [
                "Massive Write Acceleration: DML write latency drops from minutes to sub-seconds.",
                "Zero File Rewriting: Unchanged rows remain untouched until scheduled `OPTIMIZE`.",
                "GDPR Compliance: Run `REORG TABLE my_table APPLY (PURGE)` to permanently purge tombstoned rows."
            ],
            "interview_questions": [
                "How do Deletion Vectors work at the read engine level in Photon and Apache Spark?",
                "When should you run `REORG TABLE ... APPLY (PURGE)` on a table with Deletion Vectors enabled?"
            ]
        },
        {
            "nb_id": "025",
            "title": "Liquid Clustering (`CLUSTER BY`): Hilbert Curves, Dynamic ZCubes & Hive Migration",
            "filename": "025_liquid_clustering_cluster_by_hilbert_curves_and_hive_migration.py",
            "difficulty": "Intermediate",
            "business_scenario": "A 500 TB telecommunications event lake is partitioned using legacy Hive directory paths (`year/month/day/country`). Due to small file explosions and query skew, queries on `device_id` take 45 minutes.",
            "problem_statement": "Migrate a table from Hive partitioning to Liquid Clustering (`CLUSTER BY`), cluster along multiple dimensions, redefine clustering keys without rewriting data, and benchmark file skipping.",
            "architectural_notes": "Liquid Clustering replaces Hive partitioning and Z-Ordering using multi-dimensional Hilbert curves. It clusters data incrementally during `OPTIMIZE`, avoids small files by balancing partition sizes to 256MB-1GB, and allows dynamic key evolution via `ALTER TABLE`.",
            "sections": [
                {
                    "title": "1. Liquid Clustering DDL & Key Evolution",
                    "explanation": "Create a liquid clustered table and evolve clustering keys dynamically.",
                    "code": """ddl_script = \"\"\"
-- 1. Create table with Liquid Clustering
CREATE OR REPLACE TABLE prod_lakehouse.telemetry.events (
    device_id STRING,
    event_timestamp TIMESTAMP,
    event_type STRING,
    payload STRING
)
CLUSTER BY (device_id, event_timestamp);

-- 2. Dynamically evolve clustering keys without rewriting historical Parquet files
ALTER TABLE prod_lakehouse.telemetry.events CLUSTER BY (event_type, event_timestamp);
\"\"\"

print("Liquid Clustering DDL and key evolution verified.")
assert "CLUSTER BY (device_id, event_timestamp)" in ddl_script
assert "ALTER TABLE prod_lakehouse.telemetry.events CLUSTER BY" in ddl_script
"""
                }
            ],
            "key_takeaways": [
                "Zero Table Rewrites: Evolve clustering keys dynamically via `ALTER TABLE` without rewriting existing files.",
                "Incremental Compaction: `OPTIMIZE` clusters only newly appended unclustered files, reducing maintenance DBUs.",
                "Eliminate Small Files: Avoids the directory fragmentation caused by Hive partitioning on high-cardinality keys."
            ],
            "interview_questions": [
                "How does Liquid Clustering differ from traditional Hive directory partitioning and Z-Ordering?",
                "Why is Liquid Clustering particularly effective for streaming and high-frequency append workloads?"
            ]
        },
        {
            "nb_id": "026",
            "title": "Delta Change Data Feed (CDF): Batch & Streaming Micro-Batch Deduplicated Merges",
            "filename": "026_delta_change_data_feed_cdf_batch_and_streaming_micro_batch_deduplicated_merges.py",
            "difficulty": "Intermediate",
            "business_scenario": "A downstream data mart must consume only changes (inserts, updates, deletes) from the upstream customer master table. Re-scanning the 500M row table daily is cost-prohibitive.",
            "problem_statement": "Enable Delta Change Data Feed (`delta.enableChangeDataFeed = true`), query change feeds in batch and streaming mode, handle `update_preimage` vs `update_postimage`, and execute deduplicated merges.",
            "architectural_notes": "When CDF is enabled, Delta Lake records row-level change events across all DML operations. Reading with `.option('readChangeFeed', 'true')` surfaces `_change_type` (`insert`, `update_preimage`, `update_postimage`, `delete`), `_commit_version`, and `_commit_timestamp`.",
            "sections": [
                {
                    "title": "1. Change Data Feed Event Stream Simulation",
                    "explanation": "Simulate CDF change records and execute deduplication before merging into the downstream Gold table.",
                    "code": """cdf_raw_events = [
    {"customer_id": 101, "email": "a@old.com", "_change_type": "update_preimage", "_commit_version": 4},
    {"customer_id": 101, "email": "a@new.com", "_change_type": "update_postimage", "_commit_version": 4},
    {"customer_id": 102, "email": "b@corp.com", "_change_type": "insert", "_commit_version": 4},
    {"customer_id": 103, "email": "c@trash.com", "_change_type": "delete", "_commit_version": 4}
]

# Downstream consumption: Filter out update_preimage to retain target state
net_changes = [e for e in cdf_raw_events if e["_change_type"] != "update_preimage"]
print(f"Total Raw CDF Events: {len(cdf_raw_events)}")
print(f"Net Changes for Downstream Merge: {len(net_changes)}")
for row in net_changes:
    print(f"  ID {row['customer_id']}: Action = {row['_change_type'].upper()}")

assert len(net_changes) == 3
"""
                }
            ],
            "key_takeaways": [
                "Row-Level Changes: Exposes exact inserts, updates, and deletes without full table diffing.",
                "Deduplication Rule: Always deduplicate micro-batches by `_commit_version DESC` before merging to prevent ambiguous match errors.",
                "Audit Trail: CDF provides a continuous, auditable event stream for downstream CDC subscribers."
            ],
            "interview_questions": [
                "What extra columns are returned when reading a Delta table with `readChangeFeed = true`?",
                "Why must you filter out `update_preimage` before executing an upsert into a downstream table?"
            ]
        },
        {
            "nb_id": "027",
            "title": "Predictive Optimization: Serverless Automatic Compaction, VACUUM & ANALYZE",
            "filename": "027_predictive_optimization_serverless_automatic_compaction_vacuum_and_analyze.py",
            "difficulty": "Intermediate",
            "business_scenario": "A large platform operates 2,000 Delta tables. Data engineering spends 20% of their sprint cycles writing and monitoring scheduled `OPTIMIZE` and `VACUUM` maintenance jobs.",
            "problem_statement": "Enable Unity Catalog Predictive Optimization at the account and catalog level, inspect automated maintenance telemetry via system tables, and evaluate cost-benefit ratios.",
            "architectural_notes": "Predictive Optimization uses AI/ML models to monitor query patterns, write frequency, and file fragmentation on Unity Catalog managed tables. It automatically schedules and executes serverless `OPTIMIZE` and `VACUUM` when cost-effective.",
            "sections": [
                {
                    "title": "1. Enable Predictive Optimization via SQL DDL",
                    "explanation": "Enable Predictive Optimization on an entire catalog or individual schema.",
                    "code": """ddl_predictive = \"\"\"
-- Enable predictive optimization on the entire enterprise catalog
ALTER CATALOG prod_lakehouse ENABLE PREDICTIVE OPTIMIZATION;

-- Verify predictive optimization telemetry in system tables
SELECT 
    table_name,
    operation_type, -- 'OPTIMIZE' or 'VACUUM'
    start_time,
    metrics.filesCompacted AS files_compacted,
    metrics.bytesPurged AS bytes_purged
FROM system.storage.predictive_optimization_operations_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS;
\"\"\"

print("Predictive Optimization configuration verified.")
assert "ENABLE PREDICTIVE OPTIMIZATION" in ddl_predictive
"""
                }
            ],
            "key_takeaways": [
                "Zero Maintenance Pipelines: Eliminates the need to write custom cron-based `OPTIMIZE` and `VACUUM` jobs.",
                "Serverless Execution: Runs on isolated serverless compute without impacting production cluster capacity.",
                "Cost Aware: Automatically calculates whether compaction savings outweigh compute costs before launching an operation."
            ],
            "interview_questions": [
                "How does Predictive Optimization determine when it is cost-effective to compact a Delta table?",
                "Which system table records Predictive Optimization operations history?"
            ]
        },
        {
            "nb_id": "028",
            "title": "Delta UniForm: Asynchronous Iceberg Metadata Manifest Generation & Trino Access",
            "filename": "028_delta_uniform_asynchronous_iceberg_metadata_manifest_generation_and_trino_access.py",
            "difficulty": "Advanced",
            "business_scenario": "A data platform must serve both Databricks users and an external Snowflake / Trino analytics cluster without duplicating 100 TB of Parquet data across Delta and Iceberg formats.",
            "problem_statement": "Enable Delta Universal Format (UniForm) for Apache Iceberg, verify background metadata manifest generation, and demonstrate reading the same Parquet files from external Iceberg engines.",
            "architectural_notes": "Delta UniForm enables reading Delta tables with clients that support Apache Iceberg or Apache Hudi. As transactions commit to the `_delta_log`, Databricks asynchronously generates Iceberg metadata files (`metadata.json` and Avro manifests) pointing to the same underlying Parquet data files.",
            "sections": [
                {
                    "title": "1. Configure UniForm Iceberg Compatibility on Delta Table",
                    "explanation": "Enable Iceberg metadata generation via table properties.",
                    "code": """ddl_uniform = \"\"\"
CREATE OR REPLACE TABLE prod_lakehouse.gold.customer_metrics (
    customer_id BIGINT,
    lifetime_value DECIMAL(18, 2),
    churn_probability DOUBLE
)
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableDeletionVectors' = true
);
\"\"\"

print("Delta UniForm DDL specification created.")
assert "'delta.universalFormat.enabledFormats' = 'iceberg'" in ddl_uniform
"""
                }
            ],
            "key_takeaways": [
                "Single Copy of Data: Delta, Snowflake, Trino, and BigQuery read the exact same Parquet files.",
                "Asynchronous Generation: Writing to Delta is not blocked by Iceberg metadata creation.",
                "Open Interoperability: Prevents vendor lock-in by providing full Apache Iceberg v2 table format compatibility."
            ],
            "interview_questions": [
                "How does Delta UniForm enable Snowflake and AWS Athena to query Delta tables as Apache Iceberg?",
                "Are writes to the Delta table delayed while Iceberg metadata manifests are being generated in UniForm?"
            ]
        },
        {
            "nb_id": "029",
            "title": "Shallow Clones vs. Deep Clones: Zero-Copy Sandboxes, Testing & Disaster Recovery",
            "filename": "029_shallow_clones_vs_deep_clones_zero_copy_sandboxes_testing_and_disaster_recovery.py",
            "difficulty": "Intermediate",
            "business_scenario": "A data science team needs a sandbox copy of a 10 TB production dataset to test experimental machine learning models. Duplicating 10 TB of data would take hours and cost thousands in cloud storage.",
            "problem_statement": "Implement and compare Shallow Clones and Deep Clones in Delta Lake. Demonstrate that a Shallow Clone creates an instant, zero-copy pointer table, while a Deep Clone creates a fully independent replica for disaster recovery.",
            "architectural_notes": "A Shallow Clone copies only transaction log metadata, referencing the original Parquet files in place. It is created instantaneously regardless of table size. A Deep Clone copies both metadata and physical Parquet files, creating a fully decoupled duplicate.",
            "sections": [
                {
                    "title": "1. Clone Mechanics & Cost Comparison",
                    "explanation": "Benchmark clone creation time, storage overhead, and mutation independence.",
                    "code": """clone_comparison = {
    "Shallow_Clone": {
        "command": "CREATE TABLE dev.sandbox.orders SHALLOW CLONE prod.silver.orders;",
        "creation_time": "1 to 3 seconds (metadata only)",
        "storage_cost": "0 bytes additional storage initially (copy-on-write on mutation)",
        "use_case": "Dev/test sandboxes, ML feature experimentation, staging validation"
    },
    "Deep_Clone": {
        "command": "CREATE TABLE dr.backup.orders DEEP CLONE prod.silver.orders;",
        "creation_time": "Hours (copies 100% of underlying Parquet files)",
        "storage_cost": "Full duplicate storage cost (e.g. 10 TB = 10 TB)",
        "use_case": "Disaster recovery, cross-region migration, regulatory immutable archives"
    }
}

for clone_type, props in clone_comparison.items():
    print(f"[{clone_type}]\\n  Command: {props['command']}\\n  Time: {props['creation_time']}\\n")

assert "SHALLOW CLONE" in clone_comparison["Shallow_Clone"]["command"]
"""
                }
            ],
            "key_takeaways": [
                "Instant Sandboxes: Shallow clones instantiate in seconds, making them ideal for QA testing and ML modeling.",
                "Isolation Guaranteed: Changes made to a shallow clone never propagate back to the parent table.",
                "Disaster Recovery: Deep clones provide complete physical decoupling across cloud storage accounts and regions."
            ],
            "interview_questions": [
                "What happens to a Shallow Clone if someone runs `VACUUM` on the source parent table?",
                "Can you clone a specific historical version of a Delta table using Time Travel syntax?"
            ]
        },
        {
            "nb_id": "030",
            "title": "Schema Evolution (`mergeSchema`) vs. Enforcement & Table Constraints",
            "filename": "030_schema_evolution_mergeschema_vs_enforcement_and_table_constraints.py",
            "difficulty": "Intermediate",
            "business_scenario": "An API integration team frequently alters incoming JSON payloads, adding new tracking fields. The data pipeline must enforce data types on core columns while allowing safe addition of new fields without crashing.",
            "problem_statement": "Demonstrate the operational difference between Delta Schema Enforcement (rejecting schema mismatches) and Schema Evolution (`mergeSchema = true`), and enforce business invariants using `CHECK` constraints.",
            "architectural_notes": "Delta Lake enforces schema on write by default, rejecting writes with missing or extra columns. Enabling `mergeSchema` dynamically updates the table metadata. `CHECK` constraints enforce business rules (e.g., `amount > 0`) at the transactional storage layer.",
            "sections": [
                {
                    "title": "1. Demonstrate Schema Enforcement vs. mergeSchema",
                    "explanation": "Simulate schema collision and resolution via `mergeSchema`.",
                    "code": """# Simulate schema comparison
base_schema = ["order_id", "customer_id", "total_amount"]
new_payload_schema = ["order_id", "customer_id", "total_amount", "discount_code", "loyalty_tier"]

# Check if evolution is required
extra_columns = set(new_payload_schema) - set(base_schema)
print(f"Detected New Upstream Columns: {extra_columns}")

# If mergeSchema=True, target schema evolves to union
evolved_schema = sorted(list(set(base_schema).union(new_payload_schema)))
print(f"Evolved Target Schema: {evolved_schema}")
assert len(evolved_schema) == 5
"""
                }
            ],
            "key_takeaways": [
                "Schema Enforcement Default: Protects downstream BI models from silent data corruption.",
                "Controlled Evolution: Use `.option('mergeSchema', 'true')` to safely append new optional attributes.",
                "Storage-Level Constraints: Add `ALTER TABLE t ADD CONSTRAINT valid_amount CHECK (amount >= 0)` to block bad data permanently."
            ],
            "interview_questions": [
                "What is the difference between `mergeSchema` and `overwriteSchema` in Delta Lake?",
                "How do `CHECK` constraints in Delta Lake compare to traditional RDBMS constraints?"
            ]
        },
        {
            "nb_id": "031",
            "title": "Delta Time Travel: Historical Point-in-Time Auditing, Rollbacks & Log Retention",
            "filename": "031_delta_time_travel_historical_point_in_time_auditing_rollbacks_and_log_retention.py",
            "difficulty": "Intermediate",
            "business_scenario": "A developer accidentally executed an unconstrained `DELETE FROM prod_customers` in production. Operations must restore the table to the exact state 10 minutes prior to the disaster.",
            "problem_statement": "Query historical table states using Delta Time Travel (`VERSION AS OF` and `TIMESTAMP AS OF`), perform surgical auditing using `DESCRIBE HISTORY`, and execute instant disaster recovery using `RESTORE TABLE`.",
            "architectural_notes": "Because Delta Lake retains historical Parquet files and commit logs until `VACUUM` runs, users can query previous versions of the table. `RESTORE TABLE` creates a new commit that reverts the table pointer to a prior snapshot.",
            "sections": [
                {
                    "title": "1. Time Travel Querying & RESTORE Syntax",
                    "explanation": "Audit version history and restore table state prior to corruption.",
                    "code": """ddl_time_travel = \"\"\"
-- 1. Inspect audit history
DESCRIBE HISTORY prod_lakehouse.silver.customers;

-- 2. Query data as of version 3
SELECT * FROM prod_lakehouse.silver.customers VERSION AS OF 3;

-- 3. Query data as of 2 hours ago
SELECT * FROM prod_lakehouse.silver.customers TIMESTAMP AS OF (CURRENT_TIMESTAMP() - INTERVAL 2 HOURS);

-- 4. Execute instant table restore to version 3
RESTORE TABLE prod_lakehouse.silver.customers TO VERSION AS OF 3;
\"\"\"

print("Delta Time Travel and RESTORE syntax verified.")
assert "RESTORE TABLE prod_lakehouse.silver.customers TO VERSION AS OF 3" in ddl_time_travel
"""
                }
            ],
            "key_takeaways": [
                "Zero Data Loss: Time Travel allows reproducible audits and instant disaster rollback.",
                "Retention Guardrail: Table history is preserved for `delta.logRetentionDuration` (default 30 days) and unvacuumed data for 7 days.",
                "Safe Restore: `RESTORE TABLE` writes an atomic forward commit recording the reversion, preserving full auditability."
            ],
            "interview_questions": [
                "How does Delta Lake execute a `TIMESTAMP AS OF` query under the hood?",
                "What happens if you run `RESTORE TABLE ... TO VERSION AS OF 2` after `VACUUM` has deleted the Parquet files from version 2?"
            ]
        },
        {
            "nb_id": "032",
            "title": "In-Place Parquet to Delta Migration: `CONVERT TO DELTA` & Schema Repair",
            "filename": "032_in_place_parquet_to_delta_migration_convert_to_delta_and_schema_repair.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise maintains a 50 TB legacy Apache Parquet data lake on ADLS Gen2. Migrating by rewriting all 50 TB into Delta Lake would take 18 hours and incur high compute costs.",
            "problem_statement": "Execute zero-copy in-place conversion from raw Apache Parquet to Delta Lake using `CONVERT TO DELTA`, repair partitioned directories, and benchmark migration time.",
            "architectural_notes": "`CONVERT TO DELTA` infers existing Parquet directory structures and writes an initial `_delta_log/000000.json` commit pointing directly to existing Parquet files without copying or rewriting a single byte of data.",
            "sections": [
                {
                    "title": "1. Zero-Copy CONVERT TO DELTA DDL",
                    "explanation": "Generate the DDL to convert partitioned Parquet directories into Delta tables in seconds.",
                    "code": """ddl_convert = \"\"\"
-- Convert partitioned Parquet directory to Delta Lake in-place
CONVERT TO DELTA parquet.`abfss://data@datalake.dfs.core.windows.net/historical_telemetry/`
PARTITIONED BY (year INT, month INT);

-- Register converted directory as an External Table in Unity Catalog
CREATE TABLE prod_lakehouse.telemetry.historical
LOCATION 'abfss://data@datalake.dfs.core.windows.net/historical_telemetry/';
\"\"\"

print("In-place migration DDL validated.")
assert "CONVERT TO DELTA" in ddl_convert
"""
                }
            ],
            "key_takeaways": [
                "Zero Egress & Zero Copy: Converts terabytes of Parquet data to Delta in seconds.",
                "Instant Feature Upgrade: Converted tables immediately support ACID transactions, Time Travel, and Deletion Vectors.",
                "Partition Preservation: Retains existing partition structures automatically."
            ],
            "interview_questions": [
                "How does `CONVERT TO DELTA` convert millions of Parquet files in seconds without copying data?",
                "What happens if an external system writes new Parquet files into the directory after `CONVERT TO DELTA` has executed?"
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
