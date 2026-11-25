# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 059. DBSQL Query Profile Analysis: Diagnosing Scans, Shuffles, Spills & Pruning Efficiency
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An executive dashboard query takes 85 seconds to run. The business demands sub-5-second performance. The engineer must use Query Profile to identify whether the bottleneck is scanning, spilling, or shuffling.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Prove how non-sargable filter expressions (`CAST(order_date AS STRING) LIKE ...`) defeat Delta partition pruning, then inspect Catalyst's physical plan & `inputFiles()` before vs. after rewriting to a sargable equality predicate.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Wrapping a partition or clustering column inside a function/cast blocks partition pushdown and Z-Cube/file min-max pruning, triggering a full table scan (`0% files pruned`). Rewriting predicates on bare indexed columns unlocks instant partition elimination.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bad (Broken Data Skipping Full Scan) vs. Good (Pruned Scan via Bare Indexed Column)
# MAGIC
# MAGIC Write 4 ordered batches (`1..50`, `51..100`, `101..150`, `151..200`) into Delta so `_delta_log` min/max stats span disjoint ranges, then prove `CAST(order_id AS STRING)` forces scanning all 4 files while `order_id = 125` prunes 75% to 1 file.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_059_", dir=globals().get("HANDBOOK_TMP_DIR")))
pruned_path = str(lab_dir / "orders_sorted_delta")

for start_id in (1, 51, 101, 151):
    (
        spark.range(start_id, start_id + 50)
        .withColumnRenamed("id", "order_id")
        .withColumn("amount", (F.col("order_id") * 10).cast("double"))
        .coalesce(1)
        .write.format("delta")
        .mode("append")
        .save(pruned_path)
    )
spark.sql(f"CREATE TABLE t059_orders USING DELTA LOCATION '{pruned_path}'")

# BAD PATTERN: Implicit/explicit cast prevents Delta min/max file skipping & Parquet PushedFilters
bad_df = spark.sql("SELECT * FROM t059_orders WHERE CAST(order_id AS STRING) = '125'")
bad_plan = bad_df._jdf.queryExecution().executedPlan().toString()
bad_files = len(bad_df.inputFiles())

# GOOD PATTERN: Direct filter on bare numeric column enables file-level data skipping
good_df = spark.sql("SELECT * FROM t059_orders WHERE order_id = 125")
good_plan = good_df._jdf.queryExecution().executedPlan().toString()
good_files = len(good_df.inputFiles())

print(f"Bad files read (CAST breaks skipping): {bad_files}")
print(f"Good files read (Delta stats pruned) : {good_files}")
assert bad_files == 4 and good_files == 1
assert "PushedFilters" in good_plan and "EqualTo(order_id,125)" in good_plan
assert good_df.count() == bad_df.count() == 1
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Never Wrap Filter Columns**: Functions like `SUBSTRING(col)`, `YEAR(col)`, or implicit type casts block partition & data-skipping pruning.
# MAGIC - **Verify Query Profile**: Check `PartitionFilters` and `PushedFilters` / `Files Pruned` ratios after SQL rewrites.
# MAGIC - **Eliminate Spills**: Smaller pruned scans drastically reduce shuffle sort/hash memory footprint.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you identify whether a slow query is bottlenecked on I/O scan vs. CPU shuffle in DBSQL Query Profile?
# MAGIC 2. What does 'Rows Spilled to Disk' indicate in a Query Profile?
