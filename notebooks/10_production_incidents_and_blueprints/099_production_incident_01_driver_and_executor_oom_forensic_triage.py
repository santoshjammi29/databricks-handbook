# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 099. Production Incident 01: Driver & Executor OutOfMemory (OOM) Forensic Triage
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC At 03:00 AM, a scheduled production pipeline generating daily financial reports fails with `java.lang.OutOfMemoryError: Java heap space`. The on-call data engineer is paged and must restore pipeline execution.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Contrast unbounded driver `.collect()` memory anti-patterns against memory-safe distributed Delta writes, bounded driver samples (`limit(N)`), and executor partition-size diagnostics (`spark_partition_id()`).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Driver OOM occurs when unaggregated partitions are pulled to the driver via `.collect()`, `.toPandas()`, or misconfigured `broadcast()` thresholds. Executor OOM occurs when skewed partitions overload single task execution slots. Distributed aggregation + balanced partitioning eliminate heap exhaustion.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Executor Partition Skew Telemetry & Driver-Safe Distributed Aggregation
# MAGIC
# MAGIC Write synthetic financial transactions to Delta, inspect per-partition row distribution via `F.spark_partition_id()`, aggregate strictly on executors before bounded driver inspection, and prove balanced executor memory distribution.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_099_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Ban Unbounded `.collect()`**: Push `groupBy` / `agg` to executors and pull only tiny summary rows or `.limit(N)` previews.
# MAGIC - **Diagnose Partition Skew**: Check `spark_partition_id()` counts and Spark UI Max-vs-Median task duration ratios.
# MAGIC - **Off-Heap Safety**: Keep large joins off driver broadcast when table sizes exceed `autoBroadcastJoinThreshold`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you determine from Spark UI and cluster logs whether an OOM occurred on the driver or an executor?
# MAGIC 2. What Spark configuration settings govern driver maximum result sizes?
