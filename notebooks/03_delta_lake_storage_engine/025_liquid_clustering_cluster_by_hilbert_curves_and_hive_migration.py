# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 025. Liquid Clustering (`CLUSTER BY`): Hilbert Curves, Dynamic ZCubes & Hive Migration
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 500 TB telecommunications event lake is partitioned using legacy Hive directory paths (`year/month/day/country`). Due to small file explosions and query skew, queries on `device_id` take 45 minutes.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Compare legacy over-partitioned Hive directory layouts against Delta Liquid Clustering (`CLUSTER BY`), execute incremental `OPTIMIZE`, and dynamically evolve clustering keys without rewriting data.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Liquid Clustering replaces Hive partitioning and Z-Ordering using multi-dimensional space-filling clustering incrementally during `OPTIMIZE`. It avoids small-file directory explosions and allows dynamic key evolution via `ALTER TABLE ... CLUSTER BY`.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bad (Over-Partitioned Hive Layout) vs. Good (`CLUSTER BY` Liquid Clustering)
# MAGIC
# MAGIC Write identical telemetry batches into a multi-column Hive-partitioned Delta table (producing file fragmentation) vs. a Liquid Clustered table compacted incrementally with `OPTIMIZE`.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_025_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
spark.sql(f"""
    CREATE TABLE t025_liquid (
        id LONG,
        event_date STRING,
        region STRING,
        device_id STRING,
        metric_val DOUBLE
    ) USING DELTA
    LOCATION '{liquid_path}'
    CLUSTER BY (device_id, event_date)
""")
events_df.write.format("delta").mode("append").save(liquid_path)
spark.sql("OPTIMIZE t025_liquid")
liquid_files = spark.sql("DESCRIBE DETAIL t025_liquid").select("numFiles").first()["numFiles"]

print(f"Hive partitioned active files : {hive_files}")
print(f"Liquid Clustered compacted files: {liquid_files}")
assert liquid_files < hive_files
assert spark.table("t025_liquid").count() == 600
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Non-Destructive Key Evolution via `ALTER TABLE ... CLUSTER BY`
# MAGIC
# MAGIC Evolve clustering keys dynamically as query access patterns shift—without rewriting historical data files—then append new rows and verify `DESCRIBE DETAIL` reflects the updated clustering metadata.
# COMMAND ----------

spark.sql("ALTER TABLE t025_liquid CLUSTER BY (region, device_id)")
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Table Rewrites**: Evolve clustering keys dynamically via `ALTER TABLE ... CLUSTER BY` without rewriting existing Parquet files.
# MAGIC - **Small-File Immunity**: Liquid Clustering eliminates directory fragmentation caused by high-cardinality Hive partitions.
# MAGIC - **Incremental Maintenance**: `OPTIMIZE` clusters newly arrived unclustered data incrementally.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Liquid Clustering differ from traditional Hive directory partitioning and Z-Ordering?
# MAGIC 2. Why is Liquid Clustering particularly effective for streaming and high-frequency append workloads?
