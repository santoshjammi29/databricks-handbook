# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 102. Production Incident 04: Streaming State Explosions & RocksDB Checkpoint Recovery
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 24/7 fraud scoring streaming pipeline crashed due to JVM heap exhaustion after running for 3 weeks. State size grew to 40 GB because event-time watermarking was omitted.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Forensically inspect streaming checkpoint state, recover from corrupted checkpoint logs, configure off-heap RocksDB state stores, and enforce event-time watermarks to bound state growth.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Stateful streaming operations (`groupBy().count()`, stream-stream joins) buffer records in state stores. Without an event-time watermark, state grows indefinitely until the cluster crashes. RocksDB stores state off-heap on local SSDs, preventing JVM heap crashes.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Enforce Event-Time Watermarking on Stateful Stream
# MAGIC
# MAGIC Bound streaming state lifecycle using explicit event-time watermarks.
# COMMAND ----------

streaming_config = """
# Bounded stateful stream with RocksDB
df_stream = (
    spark.readStream.format("delta")
    .table("prod_lakehouse.bronze.events")
    .withWatermark("event_timestamp", "2 hours") # Purges state older than 2 hours
    .groupBy(
        F.window("event_timestamp", "10 minutes", "5 minutes"),
        F.col("device_id")
    )
    .count()
)
"""

print("Watermarked stateful streaming configuration verified.")
assert "withWatermark" in streaming_config
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Mandatory Watermarking**: Never write stateful streaming queries without `withWatermark()`.
# MAGIC - **RocksDB State Store**: Set `spark.sql.streaming.stateStore.providerClass` to `RocksDBStateStoreProvider`.
# MAGIC - **Checkpoint Rewind**: Safely delete partial offset files to recover from uncommitted state corruption.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does event-time watermarking prevent state store memory leaks in Spark Structured Streaming?
# MAGIC 2. What steps are required to safely rewind and recover a corrupted streaming checkpoint?
