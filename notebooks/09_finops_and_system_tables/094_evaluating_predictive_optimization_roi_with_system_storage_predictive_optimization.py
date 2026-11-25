# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 094. Evaluating Predictive Optimization ROI with system.storage.predictive_optimization
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Leadership wants to verify that enabling Predictive Optimization in Unity Catalog actually saves money on storage and improves query performance rather than consuming excess serverless DBUs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a Spark SQL ROI calculation over predictive-optimization operation telemetry (`OPTIMIZE`, `VACUUM`), measuring small files eliminated, terabytes reclaimed, and net storage-vs-compute savings.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `system.storage.predictive_optimization_operations_history` records every background `OPTIMIZE`, `VACUUM`, and `ANALYZE` execution along with `usage_quantity` (DBUs) and storage bytes reclaimed.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Predictive Optimization Net ROI Query in Spark SQL
# MAGIC
# MAGIC Aggregate files eliminated, storage GB reclaimed, and net monthly savings (`storage_saved_usd - dbu_cost_usd`) across managed tables.
# COMMAND ----------

po_ops = [
    ("fact_events", "OPTIMIZE", 1800, 0, 14.0),
    ("fact_events", "VACUUM", 0, 2400 * 1024 * 1024 * 1024, 2.0),
    ("dim_users", "OPTIMIZE", 120, 0, 1.5),
]
spark.createDataFrame(
    po_ops, ["table_name", "operation_type", "files_compacted", "bytes_purged", "dbus_used"]
).createOrReplaceTempView("po_history")

roi_df = spark.sql("""
    SELECT
        table_name,
        SUM(files_compacted) AS files_eliminated,
        ROUND(SUM(bytes_purged) / POW(1024, 3), 2) AS gb_reclaimed,
        ROUND(SUM(dbus_used) * 0.40, 2) AS po_compute_cost_usd,
        ROUND((SUM(bytes_purged) / POW(1024, 3)) * 0.023, 2) AS monthly_storage_saved_usd
    FROM po_history
    GROUP BY table_name
    ORDER BY files_eliminated DESC
""")

roi_rows = {r["table_name"]: r for r in roi_df.collect()}
fact_row = roi_rows["fact_events"]
print(f"fact_events -> files_eliminated={fact_row['files_eliminated']}, gb_reclaimed={fact_row['gb_reclaimed']}, storage_saved=${fact_row['monthly_storage_saved_usd']}")
assert fact_row["files_eliminated"] == 1800
assert fact_row["monthly_storage_saved_usd"] > fact_row["po_compute_cost_usd"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Quantifiable Hygiene**: Measure exact small-file reduction and purged GBs per table.
# MAGIC - **Positive Net ROI**: Reclaiming terabytes via automated `VACUUM` directly offsets serverless maintenance DBUs.
# MAGIC - **Faster Reads**: Eliminating thousands of tiny Parquet files cuts object-store listing latency dramatically.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What metrics are recorded in `system.storage.predictive_optimization_operations_history`?
# MAGIC 2. How do you evaluate whether automated compaction is reducing downstream query scan times?
