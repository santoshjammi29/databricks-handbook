# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 022. Delta Transaction Log Internals: Atomic Commits, Checkpoints & CRC
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial auditing team requires proof that Delta Lake guarantees ACID transaction atomicity, even if a cluster crashes mid-commit or storage experiences temporary latency.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Inspect and parse the `_delta_log` directory of a production Delta table. Decode JSON commit files (`add`, `remove`, `metaData`, `protocol`), analyze `.checkpoint.parquet` state consolidation, and verify CRC integrity checks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake maintains the single source of truth for table state in `_delta_log/`. Transactions write sequential JSON commit files (`000000.json`, `000001.json`). Checkpoint Parquet files collapse historical commits every 10 transactions to keep reader state reconstruction fast.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Build Real Multi-Version Delta Table & Parse `_delta_log` Actions
# MAGIC
# MAGIC Execute 12 real Delta commits (initial load, 10 incremental appends, and 1 delete) so Delta automatically emits sequential `.json`, `.crc`, and Version 10 `.checkpoint.parquet` files.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_022_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Reconstruct Exact Active State from JSON Logs vs. Spark Read
# MAGIC
# MAGIC Walk `_delta_log/*.json` `add` and `remove` actions, inspect embedded JSON data-skipping `stats`, read the Version 10 Checkpoint Parquet file, and cross-check record counts against Spark's live read.
# COMMAND ----------

# Replay active file state directly from _delta_log JSON commits
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Atomic Commits**: A transaction is only committed once its sequential JSON file is atomically written.
# MAGIC - **Compacted Checkpoints**: Prevent slow object storage listings by consolidating active state every 10 commits.
# MAGIC - **Data Skipping Stats**: Column min/max statistics and `numRecords` embedded in `add` actions enable file skipping and fast counts without scanning Parquet footers.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta Lake reconstruct the current active table state from `_delta_log`?
# MAGIC 2. What role do Parquet checkpoints play in maintaining low query scan latency?
