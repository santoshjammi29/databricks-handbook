# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 102. Production Incident 04: Streaming State Explosions & RocksDB Checkpoint Recovery
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 24/7 fraud scoring streaming pipeline crashed due to JVM heap exhaustion after running for 3 weeks. State size grew to 40 GB because event-time watermarking was omitted.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a stateful Structured Streaming tumbling-window aggregation bounded by `.withWatermark('event_ts', '1 hour')` across sequential JSON batches and verify expired late events outside the watermark are bounded/evicted cleanly.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Stateful streaming operations (`groupBy().count()`, stream-stream joins) buffer keys in RocksDB state stores. Specifying `withWatermark()` lets Spark track `max_event_time - delay`, commit finalized windows, and evict expired window state cleanly.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bounded Event-Time Watermark & Late-Event Eviction Verification
# MAGIC
# MAGIC Ingest Wave 1 events establishing an advanced event-time watermark, then send Wave 2 with an on-time advance and a 2.5-hour late zombie record, confirming expired window eviction cleanly.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_102_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 10:05:00"}\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 10:15:00"}\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 12:10:00"}\n',
    encoding="utf-8",
)
run_windowed_batch()

# Wave 2: arrives with 09:30 late poison event (before watermark 11:10 -> MUST be evicted!) + 12:20 advance
(landing / "wave2.json").write_text(
    '{"device_id": "dev_late_dropped", "event_ts_str": "2026-11-20 09:30:00"}\n'
    '{"device_id": "dev_active", "event_ts_str": "2026-11-20 12:20:00"}\n',
    encoding="utf-8",
)
run_windowed_batch()

gold_df = spark.read.format("delta").load(out_delta)
emitted = gold_df.filter("device_id = 'dev_active'").select("event_count").collect()
late_count = gold_df.filter("device_id = 'dev_late_dropped'").count()

print(f"Finalized bounded window rows for dev_active: {[r['event_count'] for r in emitted]}, late_dropped={late_count}")
assert len(emitted) == 1 and emitted[0]["event_count"] == 2
assert late_count == 0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Mandatory Watermarking**: Never run unbounded stateful aggregations without `.withWatermark()`.
# MAGIC - **RocksDB State Store**: Offload multi-gigabyte state keys from JVM heap onto local worker NVMe SSDs.
# MAGIC - **Predictable Late Handling**: Records arriving behind the watermark are dropped safely rather than leaking infinite state.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does event-time watermarking prevent state store memory leaks in Spark Structured Streaming?
# MAGIC 2. What steps are required to safely rewind and recover a corrupted streaming checkpoint?
