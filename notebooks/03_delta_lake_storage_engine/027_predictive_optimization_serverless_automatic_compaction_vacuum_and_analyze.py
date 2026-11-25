# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 027. Predictive Optimization: Serverless Automatic Compaction, VACUUM & ANALYZE
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A large platform operates 2,000 Delta tables. Data engineering spends 20% of their sprint cycles writing and monitoring scheduled `OPTIMIZE` and `VACUUM` maintenance jobs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the small-file compaction mechanics (`OPTIMIZE` + `VACUUM` file reclamation) that Unity Catalog Predictive Optimization automates serverlessly, and compute compaction ROI over local telemetry views.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Unity Catalog Predictive Optimization uses ML telemetry over `system.storage.predictive_optimization_operations_history` to automatically execute serverless `OPTIMIZE`, `VACUUM`, and `ANALYZE`. Note: `ALTER CATALOG ... ENABLE PREDICTIVE OPTIMIZATION` requires Databricks Unity Catalog; locally we execute the underlying `OPTIMIZE` compaction, fragmentation detection, and Spark SQL ROI evaluation.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Fragmentation Detection, `OPTIMIZE` Compaction & Dry-Run Reclaimable Bytes
# MAGIC
# MAGIC Write 10 tiny uncompacted commits into a Delta table, inspect fragmentation via `DESCRIBE DETAIL`, compact with `OPTIMIZE`, and quantify tombstoned unreferenced Parquet files.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_027_", dir=globals().get("HANDBOOK_TMP_DIR")))
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
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Predictive Optimization Operations Telemetry ROI Query
# MAGIC
# MAGIC Evaluate automated compaction vs. storage savings ratios using Spark SQL over a local predictive-optimization telemetry view matching the UC operations schema.
# COMMAND ----------

# In Unity Catalog, `ALTER CATALOG prod_lakehouse ENABLE PREDICTIVE OPTIMIZATION`
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

roi_df = spark.sql("""
    SELECT
        operation_type,
        COUNT(*) AS ops_count,
        SUM(files_compacted) AS total_files_compacted,
        ROUND(SUM(mb_reclaimed) / 1024.0, 2) AS gb_reclaimed,
        ROUND(SUM(dbus_consumed), 2) AS total_dbus
    FROM po_ops_history
    GROUP BY operation_type
    ORDER BY total_dbus DESC
""")
roi_map = {r["operation_type"]: r for r in roi_df.collect()}
print(f"Compaction ops DBUs={roi_map['COMPACTION']['total_dbus']}, files={roi_map['COMPACTION']['total_files_compacted']}")
assert roi_map["COMPACTION"]["total_files_compacted"] == 240
assert roi_map["VACUUM"]["gb_reclaimed"] > 15.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Maintenance Pipelines**: Eliminates custom cron-based `OPTIMIZE`, `VACUUM`, and `ANALYZE` boilerplate for UC managed tables.
# MAGIC - **Cost-Aware Execution**: Predictive Optimization evaluates compaction fragmentation vs. DBU expense automatically.
# MAGIC - **Auditable Telemetry**: Production Databricks workspaces expose operation metrics in `system.storage.predictive_optimization_operations_history`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Predictive Optimization determine when it is cost-effective to compact a Delta table?
# MAGIC 2. Which system table records Predictive Optimization operations history?
