# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 032. In-Place Parquet to Delta Migration: `CONVERT TO DELTA` & Schema Repair
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise maintains a 50 TB legacy Apache Parquet data lake. Migrating by rewriting all 50 TB into Delta Lake would take 18 hours and incur high cloud compute and egress costs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Write a legacy partitioned Parquet directory on disk, convert it in-place using `CONVERT TO DELTA ... PARTITIONED BY (...)`, prove zero Parquet files were rewritten, and immediately execute ACID updates & Time Travel.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `CONVERT TO DELTA` scans Parquet footers and Hive partition folders to synthesize `_delta_log/000000.json` referencing the existing Parquet files in place—avoiding copying or rewriting a single byte of data.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Generate Partitioned Legacy Parquet Lake & Zero-Copy `CONVERT TO DELTA`
# MAGIC
# MAGIC Write raw Parquet partitioned by `(year, month)`, capture exact underlying Parquet file paths before conversion, execute `CONVERT TO DELTA`, and verify identical file paths remain on disk.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_032_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Post-Conversion ACID DML & Time Travel Verification
# MAGIC
# MAGIC Perform an ACID `UPDATE` on the newly converted Delta table and verify Version 0 still retains pre-update legacy values via Time Travel.
# COMMAND ----------

spark.sql(f"UPDATE delta.`{pq_path}` SET reading = -1.0 WHERE id < 10")

updated_neg = spark.read.format("delta").load(str(pq_path)).filter("reading < 0").count()
v0_neg = spark.read.format("delta").option("versionAsOf", 0).load(str(pq_path)).filter("reading < 0").count()

print(f"Updated rows (v1): {updated_neg} negative readings; v0 pre-update negative readings: {v0_neg}")
assert updated_neg == 10
assert v0_neg == 0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Copy & Zero Egress**: Converts terabytes of Parquet files to Delta metadata in seconds.
# MAGIC - **Instant ACID Unlock**: Converted tables immediately support `MERGE`, `UPDATE`, Time Travel, and Deletion Vectors.
# MAGIC - **Unified Governance Trap**: Once converted, legacy jobs must stop writing raw `.parquet` directly into the folder.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does `CONVERT TO DELTA` convert millions of Parquet files in seconds without copying data?
# MAGIC 2. What happens if an external system writes new raw Parquet files into the directory after `CONVERT TO DELTA` has executed?
