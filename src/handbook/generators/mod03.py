"""
Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm (Notebooks 022 - 032)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

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
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A financial auditing team requires proof that Delta Lake guarantees ACID transaction atomicity, even if a cluster crashes mid-commit or storage experiences temporary latency.",
            "problem_statement": "Inspect and parse the `_delta_log` directory of a production Delta table. Decode JSON commit files (`add`, `remove`, `metaData`, `protocol`), analyze `.checkpoint.parquet` state consolidation, and verify CRC integrity checks.",
            "architectural_notes": "Delta Lake maintains the single source of truth for table state in `_delta_log/`. Transactions write sequential JSON commit files (`000000.json`, `000001.json`). Checkpoint Parquet files collapse historical commits every 10 transactions to keep reader state reconstruction fast.",
            "sections": [
                {
                    "title": "1. Build Real Multi-Version Delta Table & Parse `_delta_log` Actions",
                    "explanation": "Execute 12 real Delta commits (initial load, 10 incremental appends, and 1 delete) so Delta automatically emits sequential `.json`, `.crc`, and Version 10 `.checkpoint.parquet` files.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_022_", dir=globals().get("HANDBOOK_TMP_DIR")))
tbl_path = str(lab_dir / "ledger_delta")

# Commit v0: Initial 500-row ledger load
(
    spark.range(0, 500)
    .withColumn("account_bucket", (F.col("id") % 5).cast("int"))
    .coalesce(1)
    .write.format("delta")
    .mode("overwrite")
    .save(tbl_path)
)

# Commits v1..v10: 10 incremental appends of 25 rows each (triggers v10 checkpoint!)
for batch_id in range(1, 11):
    offset = 500 + (batch_id - 1) * 25
    (
        spark.range(offset, offset + 25)
        .withColumn("account_bucket", (F.col("id") % 5).cast("int"))
        .coalesce(1)
        .write.format("delta")
        .mode("append")
        .save(tbl_path)
    )

# Commit v11: Delete rows with id < 50 (emits remove + add actions)
spark.sql(f"DELETE FROM delta.`{tbl_path}` WHERE id < 50")

log_dir = lab_dir / "ledger_delta" / "_delta_log"
json_commits = sorted(p for p in log_dir.glob("*.json") if p.stem.isdigit())
crc_files = sorted(log_dir.glob("*.crc"))
checkpoint_files = sorted(log_dir.glob("*.checkpoint.parquet"))
last_checkpoint = json.loads((log_dir / "_last_checkpoint").read_text(encoding="utf-8"))

print(f"Sequential JSON commits found: {len(json_commits)} (v00..v{len(json_commits)-1:02d})")
print(f"CRC integrity checksum files : {len(crc_files)}")
print(f"Parquet checkpoint files     : {[p.name for p in checkpoint_files]}")
print(f"_last_checkpoint pointer     : {last_checkpoint}")

assert len(json_commits) == 12
assert len(crc_files) >= 11
assert len(checkpoint_files) >= 1 and last_checkpoint["version"] == 10
""",
                },
                {
                    "title": "2. Reconstruct Exact Active State from JSON Logs vs. Spark Read",
                    "explanation": "Walk `_delta_log/*.json` `add` and `remove` actions, inspect embedded JSON data-skipping `stats`, read the Version 10 Checkpoint Parquet file, and cross-check record counts against Spark's live read.",
                    "code": """# Replay active file state directly from _delta_log JSON commits
active_files: dict[str, int] = {}
meta_seen = False
protocol_seen = False

for commit_file in json_commits:
    for line in commit_file.read_text(encoding="utf-8").splitlines():
        action = json.loads(line)
        if "protocol" in action:
            protocol_seen = True
        if "metaData" in action:
            meta_seen = True
        if "add" in action:
            add_act = action["add"]
            stats = json.loads(add_act["stats"])
            active_files[add_act["path"]] = int(stats["numRecords"])
        elif "remove" in action:
            active_files.pop(action["remove"]["path"], None)

reconstructed_rows = sum(active_files.values())
actual_spark_rows = spark.read.format("delta").load(tbl_path).count()
ckpt_df = spark.read.parquet(str(checkpoint_files[0]))
ckpt_add_count = ckpt_df.filter(F.col("add").isNotNull()).count()

print(f"Active Parquet files in table: {len(active_files)}")
print(f"Reconstructed numRecords sum : {reconstructed_rows}")
print(f"Live Delta reader count()    : {actual_spark_rows}")
print(f"Checkpoint add action rows   : {ckpt_add_count}")

assert protocol_seen and meta_seen
assert reconstructed_rows == actual_spark_rows
assert ckpt_add_count > 0
""",
                },
            ],
            "key_takeaways": [
                "Atomic Commits: A transaction is only committed once its sequential JSON file is atomically written.",
                "Compacted Checkpoints: Prevent slow object storage listings by consolidating active state every 10 commits.",
                "Data Skipping Stats: Column min/max statistics and `numRecords` embedded in `add` actions enable file skipping and fast counts without scanning Parquet footers.",
            ],
            "interview_questions": [
                "How does Delta Lake reconstruct the current active table state from `_delta_log`?",
                "What role do Parquet checkpoints play in maintaining low query scan latency?",
            ],
        },
        {
            "nb_id": "023",
            "title": "Optimistic Concurrency Control (OCC) & Row-Level Concurrency Conflicts",
            "filename": "023_optimistic_concurrency_control_occ_and_row_level_concurrency_conflicts.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "import threading",
                "import time",
                "from concurrent.futures import ThreadPoolExecutor",
                "from pathlib import Path",
            ],
            "business_scenario": "Multiple streaming ingestion jobs and nightly batch GDPR deletion jobs run concurrently against the customer master table, causing intermittent `ConcurrentModificationException` failures.",
            "problem_statement": "Demonstrate the mechanics of Delta Lake Optimistic Concurrency Control (OCC), reproduce a concurrent conflicting commit, resolve it via partition isolation and bounded retries, and inspect Row Tracking metadata.",
            "architectural_notes": "Delta Lake uses OCC: transactions read a snapshot, prepare changes, and attempt to commit. If another writer modified conflicting partitions or files during that window without Row-Level Concurrency (Deletion Vectors + Row Tracking), Delta raises `ConcurrentAppendException` / `ConcurrentModificationException`.",
            "sections": [
                {
                    "title": "1. Bad vs. Good: Reproduce Real OCC Conflicts vs. Disjoint Partition Isolation",
                    "explanation": "Trigger genuine concurrent `replaceWhere` commits against the same `region='US'` partition using a thread barrier (exposing `ConcurrentAppendException`), then contrast with disjoint `US` vs. `EU` partition writes.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_023_", dir=globals().get("HANDBOOK_TMP_DIR")))
occ_path = str(lab_dir / "occ_customers")

spark.createDataFrame(
    [(1, "US", "v0"), (2, "EU", "v0")], ["id", "region", "tag"]
).write.format("delta").partitionBy("region").save(occ_path)

# GOOD PATTERN: Concurrent appends/overwrites isolated to DISJOINT partitions ('US' vs 'EU')
def write_partition(region: str, rec_id: int, label: str) -> str:
    (
        spark.createDataFrame([(rec_id, region, label)], ["id", "region", "tag"])
        .write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"region = '{region}'")
        .save(occ_path)
    )
    return region

with ThreadPoolExecutor(max_workers=2) as pool:
    results = [
        f.result()
        for f in [
            pool.submit(write_partition, "US", 10, "isolated"),
            pool.submit(write_partition, "EU", 20, "isolated"),
        ]
    ]

print(f"Disjoint partition writes committed cleanly: {results}")
assert spark.read.format("delta").load(occ_path).count() == 2

# BAD PATTERN: Multiple unsynchronized writers overwrite the SAME partition concurrently
conflicts_seen = 0
for wave in range(3):
    barrier = threading.Barrier(4)

    def colliding_write(idx: int) -> None:
        barrier.wait()
        (
            spark.createDataFrame([(100 + idx, "US", f"wave_{wave}_{idx}")], ["id", "region", "tag"])
            .write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", "region = 'US'")
            .save(occ_path)
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        for fut in [pool.submit(colliding_write, i) for i in range(4)]:
            try:
                fut.result()
            except Exception as exc:
                if "Concurrent" in type(exc).__name__ or "DELTA_CONCURRENT" in str(exc):
                    conflicts_seen += 1
    if conflicts_seen > 0:
        break

print(f"Real OCC conflict exceptions observed on shared partition: {conflicts_seen}")
assert conflicts_seen >= 1, "Expected at least one real Delta ConcurrentAppendException!"
""",
                },
                {
                    "title": "2. Production Resolution: OCC Retry Wrapper & Row Tracking Preparation",
                    "explanation": "Wrap conflicting updates with bounded jittered retries so parallel writers converge cleanly, and enable `delta.enableRowTracking` + `delta.enableDeletionVectors` to inspect stable `_metadata.row_id` tracking.",
                    "code": """# Bounded retry pattern for transient OCC conflicts
def write_partition_with_retry(rec_id: int, max_attempts: int = 6) -> int:
    for attempt in range(1, max_attempts + 1):
        try:
            (
                spark.createDataFrame([(rec_id, "APAC", f"ok_{attempt}")], ["id", "region", "tag"])
                .write.format("delta")
                .mode("append")
                .save(occ_path)
            )
            return attempt
        except Exception as exc:
            if "Concurrent" not in type(exc).__name__ and "DELTA_CONCURRENT" not in str(exc):
                raise
            if attempt == max_attempts:
                raise
            time.sleep(0.05 * attempt)
    return max_attempts

with ThreadPoolExecutor(max_workers=3) as pool:
    attempts = [f.result() for f in [pool.submit(write_partition_with_retry, 300 + i) for i in range(3)]]

apac_count = spark.read.format("delta").load(occ_path).filter("region = 'APAC'").count()
print(f"APAC concurrent writes committed via retry loop; attempts={attempts}, apac_rows={apac_count}")
assert apac_count == 3

# Enable Row Tracking + Deletion Vectors for Delta 3.x fine-grained row lineage
rt_path = str(lab_dir / "rlc_orders")
spark.sql(f\"\"\"
    CREATE TABLE t023_rlc (order_id INT, status STRING) USING DELTA
    LOCATION '{rt_path}'
    TBLPROPERTIES (
        'delta.enableDeletionVectors' = 'true',
        'delta.enableRowTracking' = 'true'
    )
\"\"\")
spark.sql("INSERT INTO t023_rlc VALUES (1, 'PENDING'), (2, 'PAID')")
tracked_df = spark.sql(
    "SELECT order_id, _metadata.row_id AS row_id, _metadata.row_commit_version AS commit_ver FROM t023_rlc ORDER BY order_id"
)
row_ids = [r["row_id"] for r in tracked_df.collect()]
print(f"Assigned stable Delta Row IDs: {row_ids}")
assert len(set(row_ids)) == 2
""",
                },
            ],
            "key_takeaways": [
                "OCC Semantics: Writers assume no conflicts; validation happens atomically at commit time.",
                "Row-Level Concurrency: Enable `delta.enableRowTracking = true` and `delta.enableDeletionVectors = true` to avoid file-level conflicts on row updates.",
                "Partition Isolation & Retries: Isolating writes by partition eliminates conflicts structurally, while bounded OCC retries absorb transient overlaps.",
            ],
            "interview_questions": [
                "Under what exact conditions will two concurrent transactions trigger a `ConcurrentModificationException` in Delta Lake?",
                "How does Row-Level Concurrency (RLC) resolve conflicts that previously failed under Copy-on-Write?",
            ],
        },
        {
            "nb_id": "024",
            "title": "Deletion Vectors (MoR): Bitmap Invalidation vs. Copy-on-Write Rewrite Overhead",
            "filename": "024_deletion_vectors_mor_bitmap_invalidation_vs_copy_on_write_rewrite_overhead.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A high-churn customer loyalty table processes 50,000 updates per hour. Under traditional Copy-on-Write, each update rewrote 200 MB files, resulting in 10 TB of disk writes per day and severe write amplification.",
            "problem_statement": "Enable Deletion Vectors on a Delta table, execute point deletes, measure Copy-on-Write vs. Merge-on-Read Parquet write amplification from `_delta_log`, and physically purge invalid rows using `REORG TABLE ... APPLY (PURGE)`.",
            "architectural_notes": "Deletion Vectors (DVs) convert Delta Lake DML from Copy-on-Write (CoW) to Merge-on-Read (MoR). In MoR, deleted rows are recorded in a lightweight roaring bitmap (`.bin` Deletion Vector file) without rewriting the Parquet data file until `OPTIMIZE` or `REORG TABLE ... APPLY (PURGE)`.",
            "sections": [
                {
                    "title": "1. Bad (Copy-on-Write) vs. Good (Merge-on-Read Deletion Vectors)",
                    "explanation": "Create two identical 10,000-row Delta tables (2 Parquet files each)—one with Deletion Vectors disabled and one enabled—then execute an identical 1% DELETE and inspect `_delta_log/000001.json`.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_024_", dir=globals().get("HANDBOOK_TMP_DIR")))
cow_path = str(lab_dir / "cow_loyalty")
dv_path = str(lab_dir / "dv_loyalty")

spark.sql(f\"\"\"
    CREATE TABLE t024_cow (id LONG, bucket INT, payload STRING) USING DELTA
    LOCATION '{cow_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
\"\"\")
spark.sql(f\"\"\"
    CREATE TABLE t024_dv (id LONG, bucket INT, payload STRING) USING DELTA
    LOCATION '{dv_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
\"\"\")

base_df = (
    spark.range(0, 10000)
    .withColumn("bucket", (F.col("id") % 2).cast("int"))
    .withColumn("payload", F.concat(F.lit("loyalty_member_profile_"), F.col("id").cast("string")))
    .coalesce(2)
)
base_df.write.format("delta").mode("append").save(cow_path)
base_df.write.format("delta").mode("append").save(dv_path)

# Delete only 100 rows (1% of dataset) from both tables
spark.sql("DELETE FROM t024_cow WHERE id % 100 = 0")
spark.sql("DELETE FROM t024_dv WHERE id % 100 = 0")

def inspect_delete_commit(table_root: Path) -> tuple[int, int, int]:
    v2_actions = [
        json.loads(line)
        for line in (table_root / "_delta_log" / "00000000000000000002.json").read_text().splitlines()
    ]
    rewritten_bytes = 0
    new_parquet_files = 0
    dv_bitmaps = 0
    for act in v2_actions:
        if "add" in act:
            add_act = act["add"]
            if add_act.get("deletionVector"):
                dv_bitmaps += 1
            else:
                new_parquet_files += 1
                rewritten_bytes += int(add_act["size"])
    return new_parquet_files, dv_bitmaps, rewritten_bytes

cow_new_pq, cow_dvs, cow_bytes = inspect_delete_commit(Path(cow_path))
dv_new_pq, dv_dvs, dv_bytes = inspect_delete_commit(Path(dv_path))

print(f"Copy-on-Write : rewrote {cow_new_pq} Parquet files ({cow_bytes:,} bytes), DVs={cow_dvs}")
print(f"Merge-on-Read : rewrote {dv_new_pq} Parquet files ({dv_bytes:,} bytes), DVs={dv_dvs}")

assert cow_new_pq >= 1 and cow_bytes > 0 and cow_dvs == 0
assert dv_new_pq == 0 and dv_bytes == 0 and dv_dvs >= 1
assert spark.table("t024_dv").count() == spark.table("t024_cow").count() == 9900
""",
                },
                {
                    "title": "2. Physical GDPR Row Purge with `REORG TABLE ... APPLY (PURGE)`",
                    "explanation": "Reclaim storage and physically remove masked-out rows from Parquet files using `REORG TABLE ... APPLY (PURGE)` while keeping logical row counts invariant.",
                    "code": """dv_bin_before = list(Path(dv_path).glob("*.bin"))
spark.sql("REORG TABLE t024_dv APPLY (PURGE)")

remaining_dv_actions = 0
latest_log = sorted((Path(dv_path) / "_delta_log").glob("*.json"))[-1]
for line in latest_log.read_text(encoding="utf-8").splitlines():
    act = json.loads(line)
    if "add" in act and act["add"].get("deletionVector"):
        remaining_dv_actions += 1

final_dv_count = spark.table("t024_dv").count()
print(f"DV bitmap files created on DELETE : {len(dv_bin_before)}")
print(f"DV annotations after REORG PURGE  : {remaining_dv_actions}")
print(f"Final logical row count preserved : {final_dv_count}")

assert len(dv_bin_before) >= 1
assert remaining_dv_actions == 0
assert final_dv_count == 9900
""",
                },
            ],
            "key_takeaways": [
                "Zero Parquet Rewrites on DML: Deletion Vectors write lightweight `.bin` roaring bitmaps instead of rewriting multi-hundred-MB Parquet files.",
                "Logical Consistency: Spark SQL transparently filters masked row offsets on read with exact CoW equivalence.",
                "GDPR Compliance: Run `REORG TABLE my_table APPLY (PURGE)` to physically rewrite touched files and remove tombstoned data.",
            ],
            "interview_questions": [
                "How do Deletion Vectors work at the read engine level in Photon and Apache Spark?",
                "When should you run `REORG TABLE ... APPLY (PURGE)` on a table with Deletion Vectors enabled?",
            ],
        },
        {
            "nb_id": "025",
            "title": "Liquid Clustering (`CLUSTER BY`): Hilbert Curves, Dynamic ZCubes & Hive Migration",
            "filename": "025_liquid_clustering_cluster_by_hilbert_curves_and_hive_migration.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A 500 TB telecommunications event lake is partitioned using legacy Hive directory paths (`year/month/day/country`). Due to small file explosions and query skew, queries on `device_id` take 45 minutes.",
            "problem_statement": "Compare legacy over-partitioned Hive directory layouts against Delta Liquid Clustering (`CLUSTER BY`), execute incremental `OPTIMIZE`, and dynamically evolve clustering keys without rewriting data.",
            "architectural_notes": "Liquid Clustering replaces Hive partitioning and Z-Ordering using multi-dimensional space-filling clustering incrementally during `OPTIMIZE`. It avoids small-file directory explosions and allows dynamic key evolution via `ALTER TABLE ... CLUSTER BY`.",
            "sections": [
                {
                    "title": "1. Bad (Over-Partitioned Hive Layout) vs. Good (`CLUSTER BY` Liquid Clustering)",
                    "explanation": "Write identical telemetry batches into a multi-column Hive-partitioned Delta table (producing file fragmentation) vs. a Liquid Clustered table compacted incrementally with `OPTIMIZE`.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_025_", dir=globals().get("HANDBOOK_TMP_DIR")))
hive_path = str(lab_dir / "hive_events")
liquid_path = str(lab_dir / "liquid_events")

events_df = (
    spark.range(0, 600)
    .withColumn("event_date", F.when(F.col("id") % 2 == 0, "2026-11-20").otherwise("2026-11-21"))
    .withColumn("region", F.element_at(F.array(F.lit("US"), F.lit("EU"), F.lit("APAC")), ((F.col("id") % 3) + 1).cast("int")))
    .withColumn("device_id", F.concat(F.lit("dev_"), (F.col("id") % 10).cast("string")))
    .withColumn("metric_val", (F.col("id") * 1.5).cast("double"))
)

# BAD PATTERN: Multi-column Hive partitioning creates dozens of tiny sub-directory Parquet files
events_df.write.format("delta").partitionBy("event_date", "region", "device_id").save(hive_path)
hive_files = spark.sql(f"DESCRIBE DETAIL delta.`{hive_path}`").select("numFiles").first()["numFiles"]

# GOOD PATTERN: Liquid Clustering without rigid physical directories
spark.sql(f\"\"\"
    CREATE TABLE t025_liquid (
        id LONG,
        event_date STRING,
        region STRING,
        device_id STRING,
        metric_val DOUBLE
    ) USING DELTA
    LOCATION '{liquid_path}'
    CLUSTER BY (device_id, event_date)
\"\"\")
events_df.write.format("delta").mode("append").save(liquid_path)
spark.sql("OPTIMIZE t025_liquid")
liquid_files = spark.sql("DESCRIBE DETAIL t025_liquid").select("numFiles").first()["numFiles"]

print(f"Hive partitioned active files : {hive_files}")
print(f"Liquid Clustered compacted files: {liquid_files}")
assert liquid_files < hive_files
assert spark.table("t025_liquid").count() == 600
""",
                },
                {
                    "title": "2. Non-Destructive Key Evolution via `ALTER TABLE ... CLUSTER BY`",
                    "explanation": "Evolve clustering keys dynamically as query access patterns shift—without rewriting historical data files—then append new rows and verify `DESCRIBE DETAIL` reflects the updated clustering metadata.",
                    "code": """spark.sql("ALTER TABLE t025_liquid CLUSTER BY (region, device_id)")
spark.sql(
    "INSERT INTO t025_liquid VALUES (9001, '2026-11-22', 'EU', 'dev_99', 42.5)"
)
spark.sql("OPTIMIZE t025_liquid")

detail_row = spark.sql("DESCRIBE DETAIL t025_liquid").select("clusteringColumns", "numFiles").first()
evolved_cols = detail_row["clusteringColumns"]
total_rows = spark.table("t025_liquid").count()

print(f"Evolved clusteringColumns: {evolved_cols}")
print(f"Total rows after append   : {total_rows}")
assert evolved_cols == ["region", "device_id"]
assert total_rows == 601
""",
                },
            ],
            "key_takeaways": [
                "Zero Table Rewrites: Evolve clustering keys dynamically via `ALTER TABLE ... CLUSTER BY` without rewriting existing Parquet files.",
                "Small-File Immunity: Liquid Clustering eliminates directory fragmentation caused by high-cardinality Hive partitions.",
                "Incremental Maintenance: `OPTIMIZE` clusters newly arrived unclustered data incrementally.",
            ],
            "interview_questions": [
                "How does Liquid Clustering differ from traditional Hive directory partitioning and Z-Ordering?",
                "Why is Liquid Clustering particularly effective for streaming and high-frequency append workloads?",
            ],
        },
        {
            "nb_id": "026",
            "title": "Delta Change Data Feed (CDF): Batch & Streaming Micro-Batch Deduplicated Merges",
            "filename": "026_delta_change_data_feed_cdf_batch_and_streaming_micro_batch_deduplicated_merges.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from delta.tables import DeltaTable",
                "from pyspark.sql import Window, functions as F",
            ],
            "business_scenario": "A downstream data mart must consume only changes (inserts, updates, deletes) from the upstream customer master table. Re-scanning the 500M row table daily is cost-prohibitive.",
            "problem_statement": "Enable Delta Change Data Feed (`delta.enableChangeDataFeed = true`), execute multiple upstream mutations (`INSERT`, `UPDATE`, `DELETE`), filter out `update_preimage`, deduplicate multiple changes per key by `_commit_version DESC`, and merge into Gold.",
            "architectural_notes": "When CDF is enabled, Delta Lake records row-level change events across DML commits. Reading with `.option('readChangeFeed', 'true')` exposes `_change_type` (`insert`, `update_preimage`, `update_postimage`, `delete`), `_commit_version`, and `_commit_timestamp`.",
            "sections": [
                {
                    "title": "1. Enable CDF & Emit Multi-Version Inserts, Updates & Deletes",
                    "explanation": "Create a CDF-enabled Silver customer table, apply two consecutive updates to the same customer key plus an insert and a delete, and inspect the raw change feed stream.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_026_", dir=globals().get("HANDBOOK_TMP_DIR")))
silver_path = str(lab_dir / "silver_customers")
gold_path = str(lab_dir / "gold_customers")

spark.sql(f\"\"\"
    CREATE TABLE t026_silver (customer_id INT, email STRING, tier STRING) USING DELTA
    LOCATION '{silver_path}'
    TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
\"\"\")

# Initial baseline (v1) + mirror baseline to Gold
spark.sql("INSERT INTO t026_silver VALUES (101, 'a@v1.com', 'BASIC'), (102, 'b@v1.com', 'PRO'), (103, 'c@v1.com', 'BASIC')")
spark.read.format("delta").load(silver_path).write.format("delta").save(gold_path)

# Incremental Silver mutations after baseline:
# v2: update 101 twice across versions to test deduplication, delete 103, insert 104
spark.sql("UPDATE t026_silver SET email = 'a@v2.com' WHERE customer_id = 101")
spark.sql("UPDATE t026_silver SET email = 'a@final.com', tier = 'ENTERPRISE' WHERE customer_id = 101")
spark.sql("DELETE FROM t026_silver WHERE customer_id = 103")
spark.sql("INSERT INTO t026_silver VALUES (104, 'd@new.com', 'PRO')")

cdf_raw = (
    spark.read.format("delta")
    .option("readChangeFeed", "true")
    .option("startingVersion", 2)
    .load(silver_path)
)
change_types = {r["_change_type"] for r in cdf_raw.select("_change_type").distinct().collect()}
print(f"Captured CDF change types: {sorted(change_types)}")
assert {"insert", "update_preimage", "update_postimage", "delete"} <= change_types
""",
                },
                {
                    "title": "2. Filter `update_preimage`, Deduplicate by Version & Execute Delta MERGE",
                    "explanation": "Prevent non-deterministic merge conflicts by discarding `update_preimage` rows, ranking per `customer_id` by `_commit_version DESC`, merging into Gold, and verifying exact table parity.",
                    "code": """latest_window = Window.partitionBy("customer_id").orderBy(F.col("_commit_version").desc())
net_changes = (
    cdf_raw.filter(F.col("_change_type") != "update_preimage")
    .withColumn("_rn", F.row_number().over(latest_window))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

DeltaTable.forPath(spark, gold_path).alias("t").merge(
    net_changes.alias("s"), "t.customer_id = s.customer_id"
).whenMatchedDelete(condition="s._change_type = 'delete'").whenMatchedUpdate(
    condition="s._change_type != 'delete'",
    set={"email": "s.email", "tier": "s.tier"},
).whenNotMatchedInsert(
    condition="s._change_type != 'delete'",
    values={"customer_id": "s.customer_id", "email": "s.email", "tier": "s.tier"},
).execute()

gold_rows = [tuple(r) for r in spark.read.format("delta").load(gold_path).orderBy("customer_id").collect()]
silver_rows = [tuple(r) for r in spark.read.format("delta").load(silver_path).orderBy("customer_id").collect()]

print(f"Gold table rows synced via CDF: {gold_rows}")
assert gold_rows == silver_rows
assert len(gold_rows) == 3
""",
                },
            ],
            "key_takeaways": [
                "Row-Level CDC: Exposes exact inserts, updates, and deletes without full-table diffs.",
                "Deduplication Rule: Filter out `update_preimage` and take `_commit_version DESC` row_number == 1 before merging to avoid `UnsupportedOperationException` on duplicate keys.",
                "Exact Parity: Incremental CDF MERGE keeps Gold synchronized with Silver across updates and hard deletes.",
            ],
            "interview_questions": [
                "What extra metadata columns are returned when reading a Delta table with `readChangeFeed = true`?",
                "Why must you filter out `update_preimage` and deduplicate multiple versions per key before executing `MERGE INTO`?",
            ],
        },
        {
            "nb_id": "027",
            "title": "Predictive Optimization: Serverless Automatic Compaction, VACUUM & ANALYZE",
            "filename": "027_predictive_optimization_serverless_automatic_compaction_vacuum_and_analyze.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A large platform operates 2,000 Delta tables. Data engineering spends 20% of their sprint cycles writing and monitoring scheduled `OPTIMIZE` and `VACUUM` maintenance jobs.",
            "problem_statement": "Demonstrate the small-file compaction mechanics (`OPTIMIZE` + `VACUUM` file reclamation) that Unity Catalog Predictive Optimization automates serverlessly, and compute compaction ROI over local telemetry views.",
            "architectural_notes": "Unity Catalog Predictive Optimization uses ML telemetry over `system.storage.predictive_optimization_operations_history` to automatically execute serverless `OPTIMIZE`, `VACUUM`, and `ANALYZE`. Note: `ALTER CATALOG ... ENABLE PREDICTIVE OPTIMIZATION` requires Databricks Unity Catalog; locally we execute the underlying `OPTIMIZE` compaction, fragmentation detection, and Spark SQL ROI evaluation.",
            "sections": [
                {
                    "title": "1. Fragmentation Detection, `OPTIMIZE` Compaction & Dry-Run Reclaimable Bytes",
                    "explanation": "Write 10 tiny uncompacted commits into a Delta table, inspect fragmentation via `DESCRIBE DETAIL`, compact with `OPTIMIZE`, and quantify tombstoned unreferenced Parquet files.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_027_", dir=globals().get("HANDBOOK_TMP_DIR")))
frag_path = str(lab_dir / "fragmented_orders")

for i in range(10):
    (
        spark.range(i * 10, (i + 1) * 10)
        .withColumn("batch_id", F.lit(i))
        .coalesce(1)
        .write.format("delta")
        .mode("append")
        .save(frag_path)
    )

before_files = spark.sql(f"DESCRIBE DETAIL delta.`{frag_path}`").select("numFiles").first()["numFiles"]
spark.sql(f"OPTIMIZE delta.`{frag_path}`")
after_files = spark.sql(f"DESCRIBE DETAIL delta.`{frag_path}`").select("numFiles").first()["numFiles"]

# Track unreferenced Parquet files eligible for VACUUM retention cleanup
disk_parquets = len([p for p in Path(frag_path).glob("*.parquet")])
print(f"Files before OPTIMIZE         : {before_files}")
print(f"Active files after OPTIMIZE   : {after_files}")
print(f"Total Parquet files on disk   : {disk_parquets} (stale versions await VACUUM)")

assert before_files == 10
assert after_files == 1
assert disk_parquets > after_files
""",
                },
                {
                    "title": "2. Predictive Optimization Operations Telemetry ROI Query",
                    "explanation": "Evaluate automated compaction vs. storage savings ratios using Spark SQL over a local predictive-optimization telemetry view matching the UC operations schema.",
                    "code": """# In Unity Catalog, `ALTER CATALOG prod_lakehouse ENABLE PREDICTIVE OPTIMIZATION`
# records telemetry in `system.storage.predictive_optimization_operations_history`.
telemetry_rows = [
    ("sales_fact", "COMPACTION", 240, 12.5, 4800, 1.8),
    ("events_raw", "VACUUM", 0, 1.2, 18500, 3.1),
    ("customers_dim", "ANALYZE", 0, 0.4, 0, 0.9),
]
spark.createDataFrame(
    telemetry_rows,
    ["table_name", "operation_type", "files_compacted", "dbus_consumed", "mb_reclaimed", "runtime_minutes"],
).createOrReplaceTempView("po_ops_history")

roi_df = spark.sql(\"\"\"
    SELECT
        operation_type,
        COUNT(*) AS ops_count,
        SUM(files_compacted) AS total_files_compacted,
        ROUND(SUM(mb_reclaimed) / 1024.0, 2) AS gb_reclaimed,
        ROUND(SUM(dbus_consumed), 2) AS total_dbus
    FROM po_ops_history
    GROUP BY operation_type
    ORDER BY total_dbus DESC
\"\"\")
roi_map = {r["operation_type"]: r for r in roi_df.collect()}
print(f"Compaction ops DBUs={roi_map['COMPACTION']['total_dbus']}, files={roi_map['COMPACTION']['total_files_compacted']}")
assert roi_map["COMPACTION"]["total_files_compacted"] == 240
assert roi_map["VACUUM"]["gb_reclaimed"] > 15.0
""",
                },
            ],
            "key_takeaways": [
                "Zero Maintenance Pipelines: Eliminates custom cron-based `OPTIMIZE`, `VACUUM`, and `ANALYZE` boilerplate for UC managed tables.",
                "Cost-Aware Execution: Predictive Optimization evaluates compaction fragmentation vs. DBU expense automatically.",
                "Auditable Telemetry: Production Databricks workspaces expose operation metrics in `system.storage.predictive_optimization_operations_history`.",
            ],
            "interview_questions": [
                "How does Predictive Optimization determine when it is cost-effective to compact a Delta table?",
                "Which system table records Predictive Optimization operations history?",
            ],
        },
        {
            "nb_id": "028",
            "title": "Delta UniForm: Asynchronous Iceberg Metadata Manifest Generation & Trino Access",
            "filename": "028_delta_uniform_asynchronous_iceberg_metadata_manifest_generation_and_trino_access.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A data platform must serve both Databricks users and an external Snowflake / Trino analytics cluster without duplicating 100 TB of Parquet data across Delta and Iceberg formats.",
            "problem_statement": "Configure Delta tables with `IcebergCompatV2` + column mapping invariants required by Delta Universal Format (UniForm), verify physical column-mapped Parquet schemas locally, and validate zero-duplication data file pointers in `_delta_log`.",
            "architectural_notes": "Delta UniForm writes standard Delta commits to `_delta_log` and asynchronously emits Apache Iceberg metadata (`metadata.json` and Avro manifests) pointing to the exact same Parquet files. Asynchronous Iceberg metadata emission requires `'delta.universalFormat.enabledFormats' = 'iceberg'` on Databricks Unity Catalog or an attached `delta-iceberg` runtime artifact; in local OSS Delta 3.2, `IcebergCompatV2` and `delta.columnMapping.mode = 'name'` validate all storage-layer schema invariants.",
            "sections": [
                {
                    "title": "1. Enforce Column Mapping & `IcebergCompatV2` Invariants Locally",
                    "explanation": "Create a Delta table with `'delta.columnMapping.mode' = 'name'` and `'delta.enableIcebergCompatV2' = 'true'`, write records, and verify Iceberg compatibility properties and schema evolution.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_028_", dir=globals().get("HANDBOOK_TMP_DIR")))
uni_path = str(lab_dir / "uniform_metrics")

# Create Delta table enforcing strict Iceberg v2 storage invariants
spark.sql(f\"\"\"
    CREATE TABLE t028_uniform (
        customer_id BIGINT,
        lifetime_value DOUBLE,
        segment STRING
    ) USING DELTA
    LOCATION '{uni_path}'
    TBLPROPERTIES (
        'delta.columnMapping.mode' = 'name',
        'delta.enableIcebergCompatV2' = 'true'
    )
\"\"\")

spark.createDataFrame(
    [(1001, 12500.50, "ENTERPRISE"), (1002, 420.00, "SMB"), (1003, 9800.75, "MIDMARKET")],
    ["customer_id", "lifetime_value", "segment"],
).coalesce(1).write.format("delta").mode("append").save(uni_path)

# IcebergCompatV2 allows safe metadata-only column renames via Column Mapping
spark.sql("ALTER TABLE t028_uniform RENAME COLUMN segment TO customer_segment")

props = dict(spark.sql("SHOW TBLPROPERTIES t028_uniform").collect())
cols = spark.table("t028_uniform").columns
print(f"Table IcebergCompatV2 property: {props.get('delta.enableIcebergCompatV2')}")
print(f"Renamed columns via name-mapping: {cols}")

assert props.get("delta.enableIcebergCompatV2") == "true"
assert props.get("delta.columnMapping.mode") == "name"
assert "customer_segment" in cols
""",
                },
                {
                    "title": "2. Verify Zero-Copy Single Parquet Storage Across Manifests",
                    "explanation": "Read active file paths from `_delta_log/*.json` and confirm every referenced Parquet file exists once on disk without duplicated format copies.",
                    "code": """log_entries = []
for fpath in sorted((Path(uni_path) / "_delta_log").glob("*.json")):
    for line in fpath.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if "add" in entry:
            log_entries.append(entry["add"]["path"])

existing_parquets = [p.name for p in Path(uni_path).glob("*.parquet")]
input_files = [Path(f).name for f in spark.table("t028_uniform").inputFiles()]

print(f"Delta log Parquet paths : {log_entries}")
print(f"Physical Parquet files  : {existing_parquets}")
assert set(input_files) <= set(existing_parquets)
assert len(existing_parquets) == 1
assert spark.table("t028_uniform").count() == 3
""",
                },
            ],
            "key_takeaways": [
                "Single Copy of Data: Delta, Snowflake, Trino, and BigQuery read the exact same underlying Parquet files.",
                "Storage Invariants: `delta.columnMapping.mode = 'name'` and `delta.enableIcebergCompatV2 = 'true'` guarantee type and schema compatibility for Iceberg readers.",
                "Asynchronous Generation: In Unity Catalog, adding `'delta.universalFormat.enabledFormats' = 'iceberg'` emits Avro manifests asynchronously without blocking Delta writers.",
            ],
            "interview_questions": [
                "How does Delta UniForm enable Snowflake and AWS Athena to query Delta tables as Apache Iceberg?",
                "Are writes to the Delta table delayed while Iceberg metadata manifests are being generated in UniForm?",
            ],
        },
        {
            "nb_id": "029",
            "title": "Shallow Clones vs. Deep Clones: Zero-Copy Sandboxes, Testing & Disaster Recovery",
            "filename": "029_shallow_clones_vs_deep_clones_zero_copy_sandboxes_testing_and_disaster_recovery.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import json",
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A data science team needs a sandbox copy of a 10 TB production dataset to test experimental machine learning models. Duplicating 10 TB of data would take hours and cost thousands in cloud storage.",
            "problem_statement": "Execute real `SHALLOW CLONE` in Delta SQL, verify zero copied Parquet files inside the clone directory, prove mutation isolation against the source table, and contrast with physically decoupled replicas (`DEEP CLONE` in Databricks).",
            "architectural_notes": "A `SHALLOW CLONE` copies only `_delta_log` metadata, referencing existing parent Parquet files in place—making creation instant at zero initial storage cost. (`DEEP CLONE` copies both metadata and physical Parquet files in Databricks Runtime; locally in OSS Delta we model a decoupled physical snapshot alongside `SHALLOW CLONE`.)",
            "sections": [
                {
                    "title": "1. Execute Real `SHALLOW CLONE` & Verify Zero-Copy Disk Footprint",
                    "explanation": "Create a production Delta table with Parquet files on disk, run `CREATE OR REPLACE TABLE ... SHALLOW CLONE ...`, and confirm zero physical `.parquet` data files are duplicated in the sandbox folder.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_029_", dir=globals().get("HANDBOOK_TMP_DIR")))
prod_path = str(lab_dir / "prod_orders")
sandbox_path = str(lab_dir / "sandbox_orders")

spark.range(0, 1000).write.format("delta").save(prod_path)
spark.sql(f"CREATE TABLE t029_prod USING DELTA LOCATION '{prod_path}'")

spark.sql(f"CREATE OR REPLACE TABLE t029_sandbox SHALLOW CLONE t029_prod LOCATION '{sandbox_path}'")

prod_parquets = list(Path(prod_path).glob("*.parquet"))
sandbox_parquets = list(Path(sandbox_path).glob("*.parquet"))
sandbox_v0 = (Path(sandbox_path) / "_delta_log" / "00000000000000000000.json").read_text(encoding="utf-8")

print(f"Parent Parquet count : {len(prod_parquets)}")
print(f"Shallow Clone Parquets: {len(sandbox_parquets)} (0 physical copies!)")
assert len(prod_parquets) >= 1
assert len(sandbox_parquets) == 0
assert "prod_orders" in sandbox_v0
assert spark.table("t029_sandbox").count() == 1000
""",
                },
                {
                    "title": "2. Prove Mutation Isolation & Physical Decoupling for Disaster Recovery",
                    "explanation": "Mutate the shallow clone (delete 400 rows + append 50 rows), assert the production parent remains unchanged at 1,000 rows, and contrast with a physically decoupled replica.",
                    "code": """spark.sql("DELETE FROM t029_sandbox WHERE id < 400")
spark.sql("INSERT INTO t029_sandbox SELECT id + 2000 AS id FROM range(50)")

prod_count = spark.table("t029_prod").count()
sandbox_count = spark.table("t029_sandbox").count()

# Model physically decoupled replica (equivalent to DBR `DEEP CLONE` independent Parquet copy)
dr_path = str(lab_dir / "dr_orders_replica")
spark.table("t029_prod").write.format("delta").save(dr_path)
dr_parquets = list(Path(dr_path).glob("*.parquet"))
dr_count = spark.read.format("delta").load(dr_path).count()

print(f"Production rows after sandbox mutations: {prod_count}")
print(f"Sandbox rows after mutations           : {sandbox_count}")
print(f"Decoupled DR Parquet files             : {len(dr_parquets)} ({dr_count} rows)")

assert prod_count == 1000
assert sandbox_count == 650
assert len(dr_parquets) >= 1 and dr_count == 1000
""",
                },
            ],
            "key_takeaways": [
                "Instant Sandboxes: Shallow clones copy only metadata pointers, creating zero-byte-overhead clones in seconds.",
                "Isolation Guaranteed: Deletes and inserts inside a shallow clone never mutate the parent table.",
                "Disaster Recovery: Physically decoupled copies (`DEEP CLONE` on Databricks) replicate Parquet data so `VACUUM` on source cannot break DR.",
            ],
            "interview_questions": [
                "What happens to a Shallow Clone if someone runs `VACUUM` on the source parent table?",
                "Can you clone a specific historical version of a Delta table using Time Travel syntax?",
            ],
        },
        {
            "nb_id": "030",
            "title": "Schema Evolution (`mergeSchema`) vs. Enforcement & Table Constraints",
            "filename": "030_schema_evolution_mergeschema_vs_enforcement_and_table_constraints.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "An API integration team frequently alters incoming JSON payloads, adding new tracking fields. The data pipeline must enforce data types on core columns while allowing safe addition of new fields without crashing.",
            "problem_statement": "Prove Delta Schema Enforcement blocks unexpected columns by default, unlock safe column evolution with `.option('mergeSchema', 'true')`, and enforce domain invariants via real `ALTER TABLE ... ADD CONSTRAINT ... CHECK` constraints.",
            "architectural_notes": "Delta Lake validates schemas at commit time (Schema-on-Write). Unexpected columns fail immediately unless `mergeSchema = true` is explicitly passed. Table `CHECK` constraints enforce row-level business invariants directly inside Delta's write execution path.",
            "sections": [
                {
                    "title": "1. Schema Enforcement Protection vs. Controlled `mergeSchema` Evolution",
                    "explanation": "Verify Delta blocks unannounced columns by default (capturing `AnalysisException`), then evolve cleanly with `mergeSchema = 'true'` and verify existing rows backfill with `NULL`.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_030_", dir=globals().get("HANDBOOK_TMP_DIR")))
orders_path = str(lab_dir / "orders_schema")

spark.createDataFrame(
    [(1, "C100", 125.0), (2, "C101", 80.5)], ["order_id", "customer_id", "amount"]
).write.format("delta").save(orders_path)
spark.sql(f"CREATE TABLE t030_orders USING DELTA LOCATION '{orders_path}'")

drifted_df = spark.createDataFrame(
    [(3, "C102", 210.0, "SAVE10")], ["order_id", "customer_id", "amount", "discount_code"]
)

# BAD / DEFAULT: Strict schema enforcement rejects surprise columns
rejected = False
try:
    drifted_df.write.format("delta").mode("append").save(orders_path)
except Exception as exc:
    rejected = "schema mismatch" in str(exc).lower() or "AnalysisException" in type(exc).__name__

print(f"Schema Enforcement rejected extra column cleanly: {rejected}")
assert rejected is True

# GOOD: Controlled schema evolution adds column safely
drifted_df.write.format("delta").mode("append").option("mergeSchema", "true").save(orders_path)
evolved_df = spark.read.format("delta").load(orders_path)
null_backfilled = evolved_df.filter("discount_code IS NULL").count()

print(f"Evolved columns: {evolved_df.columns}, existing null backfills: {null_backfilled}")
assert evolved_df.columns == ["order_id", "customer_id", "amount", "discount_code"]
assert null_backfilled == 2 and evolved_df.count() == 3
""",
                },
                {
                    "title": "2. Transactional Business Rules with Delta `CHECK` Constraints",
                    "explanation": "Add a storage-layer `CHECK (amount > 0)` invariant, confirm invalid negative transactions fail atomically with zero partial corruption, and verify row count stability.",
                    "code": """spark.sql("ALTER TABLE t030_orders ADD CONSTRAINT valid_amount CHECK (amount > 0)")

constraint_blocked = False
try:
    spark.sql("INSERT INTO t030_orders VALUES (4, 'C103', -49.99, 'BAD')")
except Exception as exc:
    constraint_blocked = "CHECK constraint" in str(exc) or "DELTA_VIOLATE_CONSTRAINT" in str(exc)

spark.sql("INSERT INTO t030_orders VALUES (4, 'C103', 49.99, 'WELCOME')")
final_count = spark.table("t030_orders").count()
min_amount = spark.table("t030_orders").agg({"amount": "min"}).first()[0]

print(f"Invalid row blocked by CHECK constraint: {constraint_blocked}")
print(f"Final count={final_count}, min_amount={min_amount}")
assert constraint_blocked is True
assert final_count == 4 and min_amount > 0
""",
                },
            ],
            "key_takeaways": [
                "Schema Enforcement Default: Prevents silent column pollution from malformed upstream feeds.",
                "Controlled Evolution: Pass `.option('mergeSchema', 'true')` to allowlist safe backward-compatible column additions.",
                "Storage-Layer Constraints: `ALTER TABLE ... ADD CONSTRAINT ... CHECK (...)` guarantees corrupted domain values never commit.",
            ],
            "interview_questions": [
                "What is the difference between `mergeSchema` and `overwriteSchema` in Delta Lake?",
                "How do `CHECK` constraints in Delta Lake compare to traditional RDBMS constraints?",
            ],
        },
        {
            "nb_id": "031",
            "title": "Delta Time Travel: Historical Point-in-Time Auditing, Rollbacks & Log Retention",
            "filename": "031_delta_time_travel_historical_point_in_time_auditing_rollbacks_and_log_retention.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A developer accidentally executed an unconstrained `DELETE FROM prod_customers` in production. Operations must restore the table to the exact state prior to the disaster without data loss.",
            "problem_statement": "Audit historical versions with `DESCRIBE HISTORY`, reproduce an unconstrained `DELETE` disaster, query the intact prior snapshot using `VERSION AS OF`, and execute atomic disaster recovery using `RESTORE TABLE`.",
            "architectural_notes": "Delta Lake preserves immutable historical Parquet snapshots across commits until `VACUUM` deletes expired files. `RESTORE TABLE` records a brand-new forward commit pointing back to the target version, keeping full audit lineage intact.",
            "sections": [
                {
                    "title": "1. Multi-Commit Evolution, Disaster Reproduction & `DESCRIBE HISTORY`",
                    "explanation": "Build 3 committed versions (`v0` load, `v1` enrichment insert, `v2` accidental full-table `DELETE`) and inspect the commit audit trail.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_031_", dir=globals().get("HANDBOOK_TMP_DIR")))
cust_path = str(lab_dir / "silver_customers")

spark.sql(f"CREATE TABLE t031_customers (id LONG, segment STRING) USING DELTA LOCATION '{cust_path}'")
spark.range(0, 100).withColumn("segment", F.lit("CORE")).write.format("delta").mode("append").save(cust_path)
spark.range(100, 125).withColumn("segment", F.lit("VIP")).write.format("delta").mode("append").save(cust_path)

# Oops: unconstrained DELETE wipes the table at version 3!
spark.sql("DELETE FROM t031_customers")

post_disaster_count = spark.table("t031_customers").count()
history_df = spark.sql("DESCRIBE HISTORY t031_customers").select("version", "operation")
ops_by_ver = {r["version"]: r["operation"] for r in history_df.collect()}

print(f"Row count immediately after accidental DELETE: {post_disaster_count}")
print(f"Delta Audit Log versions: {ops_by_ver}")
assert post_disaster_count == 0
assert ops_by_ver[3] == "DELETE"
""",
                },
                {
                    "title": "2. Point-in-Time Inspection (`VERSION AS OF`) & Atomic `RESTORE TABLE`",
                    "explanation": "Verify pre-disaster Version 2 holds all 125 customer records, restore atomically with `RESTORE TABLE t031_customers TO VERSION AS OF 2`, and verify Version 4 captures the `RESTORE` audit entry.",
                    "code": """v2_count = spark.sql("SELECT * FROM t031_customers VERSION AS OF 2").count()
assert v2_count == 125

spark.sql("RESTORE TABLE t031_customers TO VERSION AS OF 2")

restored_count = spark.table("t031_customers").count()
latest_op = (
    spark.sql("DESCRIBE HISTORY t031_customers")
    .orderBy(F.col("version").desc())
    .select("version", "operation")
    .first()
)

print(f"Pre-disaster snapshot (v2) count: {v2_count}")
print(f"Restored live table count       : {restored_count}")
print(f"Latest audit entry              : version={latest_op['version']}, op={latest_op['operation']}")

assert restored_count == 125
assert latest_op["operation"] == "RESTORE"
""",
                },
            ],
            "key_takeaways": [
                "Zero Data Loss Rollback: `RESTORE TABLE` instantaneously reverts bad writes via a metadata pointer update.",
                "Forward-Only Auditability: `RESTORE` appends a new version (`RESTORE`) rather than deleting history.",
                "Retention Guardrails: Configure `delta.deletedFileRetentionDuration` >= 7 days so Time Travel windows stay intact before `VACUUM`.",
            ],
            "interview_questions": [
                "How does Delta Lake execute a `TIMESTAMP AS OF` query under the hood?",
                "What happens if you run `RESTORE TABLE ... TO VERSION AS OF 2` after `VACUUM` has deleted the Parquet files from version 2?",
            ],
        },
        {
            "nb_id": "032",
            "title": "In-Place Parquet to Delta Migration: `CONVERT TO DELTA` & Schema Repair",
            "filename": "032_in_place_parquet_to_delta_migration_convert_to_delta_and_schema_repair.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "An enterprise maintains a 50 TB legacy Apache Parquet data lake. Migrating by rewriting all 50 TB into Delta Lake would take 18 hours and incur high cloud compute and egress costs.",
            "problem_statement": "Write a legacy partitioned Parquet directory on disk, convert it in-place using `CONVERT TO DELTA ... PARTITIONED BY (...)`, prove zero Parquet files were rewritten, and immediately execute ACID updates & Time Travel.",
            "architectural_notes": "`CONVERT TO DELTA` scans Parquet footers and Hive partition folders to synthesize `_delta_log/000000.json` referencing the existing Parquet files in place—avoiding copying or rewriting a single byte of data.",
            "sections": [
                {
                    "title": "1. Generate Partitioned Legacy Parquet Lake & Zero-Copy `CONVERT TO DELTA`",
                    "explanation": "Write raw Parquet partitioned by `(year, month)`, capture exact underlying Parquet file paths before conversion, execute `CONVERT TO DELTA`, and verify identical file paths remain on disk.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_032_", dir=globals().get("HANDBOOK_TMP_DIR")))
pq_path = lab_dir / "historical_telemetry_parquet"

(
    spark.range(0, 400)
    .withColumn("year", F.lit(2026))
    .withColumn("month", F.when(F.col("id") % 2 == 0, 10).otherwise(11).cast("int"))
    .withColumn("reading", (F.col("id") * 2.5).cast("double"))
    .write.mode("overwrite")
    .partitionBy("year", "month")
    .parquet(str(pq_path))
)

before_parquets = sorted(str(p.relative_to(pq_path)) for p in pq_path.rglob("*.parquet") if "_delta_log" not in p.parts)
assert not (pq_path / "_delta_log").exists()

# Zero-copy in-place conversion!
spark.sql(f"CONVERT TO DELTA parquet.`{pq_path}` PARTITIONED BY (year INT, month INT)")

after_parquets = sorted(str(p.relative_to(pq_path)) for p in pq_path.rglob("*.parquet") if "_delta_log" not in p.parts)
table_fmt = spark.sql(f"DESCRIBE DETAIL delta.`{pq_path}`").select("format", "partitionColumns").first()

print(f"Pre-conversion Parquets  : {len(before_parquets)} files")
print(f"Post-conversion format   : {table_fmt['format']}, partitions={table_fmt['partitionColumns']}")
assert (pq_path / "_delta_log" / "00000000000000000000.json").exists()
assert before_parquets == after_parquets
assert table_fmt["format"] == "delta" and table_fmt["partitionColumns"] == ["year", "month"]
""",
                },
                {
                    "title": "2. Post-Conversion ACID DML & Time Travel Verification",
                    "explanation": "Perform an ACID `UPDATE` on the newly converted Delta table and verify Version 0 still retains pre-update legacy values via Time Travel.",
                    "code": """spark.sql(f"UPDATE delta.`{pq_path}` SET reading = -1.0 WHERE id < 10")

updated_neg = spark.read.format("delta").load(str(pq_path)).filter("reading < 0").count()
v0_neg = spark.read.format("delta").option("versionAsOf", 0).load(str(pq_path)).filter("reading < 0").count()

print(f"Updated rows (v1): {updated_neg} negative readings; v0 pre-update negative readings: {v0_neg}")
assert updated_neg == 10
assert v0_neg == 0
""",
                },
            ],
            "key_takeaways": [
                "Zero Copy & Zero Egress: Converts terabytes of Parquet files to Delta metadata in seconds.",
                "Instant ACID Unlock: Converted tables immediately support `MERGE`, `UPDATE`, Time Travel, and Deletion Vectors.",
                "Unified Governance Trap: Once converted, legacy jobs must stop writing raw `.parquet` directly into the folder.",
            ],
            "interview_questions": [
                "How does `CONVERT TO DELTA` convert millions of Parquet files in seconds without copying data?",
                "What happens if an external system writes new raw Parquet files into the directory after `CONVERT TO DELTA` has executed?",
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
