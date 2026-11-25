# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 056. Photon Engine Internals: C++ Vectorized Execution, SIMD Hardware & Memory Off-Heap
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A large-scale enterprise data platform is evaluating whether to enable the Photon Engine for its SQL workloads to justify the incremental DBU price premium with query speedups.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Contrast row-by-row Python UDF serialization overhead (which breaks Catalyst/Photon vectorized codegen) against native Spark columnar SQL expressions + Broadcast Hash Joins on real Delta tables, inspecting the physical plan.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Photon executes vectorized C++ batches over columnar off-heap buffers on Databricks Runtime. Any Python row-by-row UDF breaks Photon vectorization and forces JVM/Python serialization pickling; rewriting expressions in native Spark SQL enables whole-stage codegen and Photon fallback elimination.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bad (Python UDF Blocking Vectorization) vs. Good (Native Columnar Expressions & Broadcast)
# MAGIC
# MAGIC Compare physical execution plans between a row-by-row Python UDF (`BatchEvalPython`) and native Catalyst columnar expressions with a broadcast dimension join.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_056_", dir=globals().get("HANDBOOK_TMP_DIR")))
fact_path = str(lab_dir / "fact_orders")

spark.range(0, 5000).withColumn("sku_id", (F.col("id") % 5).cast("int")).withColumn(
    "gross_amt", (F.col("id") * 1.25).cast("double")
).write.format("delta").save(fact_path)

fact_df = spark.read.format("delta").load(fact_path)
dim_df = spark.createDataFrame(
    [(0, "CORE"), (1, "PRO"), (2, "ENT"), (3, "ADDON"), (4, "SUPPORT")],
    ["sku_id", "tier"],
)

# BAD PATTERN: Row-by-row Python UDF prevents Photon / Tungsten whole-stage codegen
@F.udf(DoubleType())
def tax_udf(val: float) -> float:
    return round(val * 1.08, 2) if val is not None else 0.0

bad_plan = (
    fact_df.withColumn("taxed", tax_udf(F.col("gross_amt")))
    ._jdf.queryExecution()
    .executedPlan()
    .toString()
)

# GOOD PATTERN: Pure columnar SQL expressions + Broadcast Hash Join
good_df = (
    fact_df.join(F.broadcast(dim_df), "sku_id")
    .withColumn("taxed", F.round(F.col("gross_amt") * F.lit(1.08), 2))
    .groupBy("tier")
    .agg(F.round(F.sum("taxed"), 2).alias("total_taxed"))
)
good_plan = good_df._jdf.queryExecution().executedPlan().toString()

bad_sum = round(fact_df.select(F.sum(tax_udf(F.col("gross_amt")))).first()[0], 2)
good_sum = round(good_df.agg(F.sum("total_taxed")).first()[0], 2)

print(f"Python UDF plan uses BatchEvalPython: {'BatchEvalPython' in bad_plan}")
print(f"Columnar Broadcast plan avoids BatchEvalPython: {'BatchEvalPython' not in good_plan}")
assert "BatchEvalPython" in bad_plan
assert "BatchEvalPython" not in good_plan and "BroadcastHashJoin" in good_plan
assert abs(bad_sum - good_sum) < 1.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Avoid Python UDFs**: Every Python UDF breaks native vectorization (BatchEvalPython pickling overhead); prefer built-in Spark SQL expressions.
# MAGIC - **Broadcast Small Dimensions**: Eliminate SortMergeJoin shuffles by broadcasting small lookup tables.
# MAGIC - **Hardware Acceleration**: Photon's vectorized C++ operators natively leverage AVX-512 / ARM NEON SIMD on Databricks.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why was Photon rewritten in C++ instead of optimizing the existing Java/Scala JVM codebase?
# MAGIC 2. How do Python UDFs degrade Catalyst Whole-Stage Codegen and Photon vectorization?
