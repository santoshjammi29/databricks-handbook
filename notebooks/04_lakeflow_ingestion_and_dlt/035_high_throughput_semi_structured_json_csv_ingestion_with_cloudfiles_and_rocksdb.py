# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 035. High-Throughput Semi-Structured JSON/CSV Ingestion with cloudFiles and RocksDB
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An advertising network ingests 100,000 multi-line JSON impression logs per second. Memory leaks in file tracking must be avoided at high throughput.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute incremental rate-limited multi-line JSON streaming (`maxFilesPerTrigger`, `multiLine=true`) into Delta Bronze across multiple waves, inspecting Spark streaming checkpoint commit logs (`offsets/` + `commits/`) guaranteeing exactly-once ingestion.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Auto Loader uses an embedded off-heap RocksDB state store and streaming checkpoint `offsets/` logs on Databricks to prevent JVM heap exhaustion during multi-million file backfills, while `maxFilesPerTrigger` bounds micro-batch memory consumption.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Incremental Rate-Limited Multi-Line JSON Stream & Exactly-Once Replay
# MAGIC
# MAGIC Write 4 multi-line JSON landing files across two waves and ingest with `maxFilesPerTrigger = 1` + `availableNow = True`, verifying batch offset checkpoints prevent duplicate reads on re-run.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_035_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Rate Limiting**: Set `maxFilesPerTrigger` / `maxBytesPerTrigger` so historical backfills do not trigger Executor OOM.
# MAGIC - **Multi-Line JSON**: Enable `.option('multiLine', 'true')` for pretty-printed arrays or multi-line JSON objects.
# MAGIC - **Exactly-Once Checkpointing**: Re-triggering an interrupted stream skips committed offsets deterministically.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you prevent memory exhaustion when Auto Loader backfills millions of historical files?
# MAGIC 2. What is the difference between `maxFilesPerTrigger` and `maxBytesPerTrigger`?
