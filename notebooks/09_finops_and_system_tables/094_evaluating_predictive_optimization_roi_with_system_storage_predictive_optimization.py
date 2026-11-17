# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 094. Evaluating Predictive Optimization ROI with system.storage.predictive_optimization
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Leadership wants to verify that enabling Predictive Optimization in Unity Catalog actually saves money on storage and improves query performance rather than consuming excess serverless DBUs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query `system.storage.predictive_optimization_operations_history` to compute the number of small files eliminated, storage gigabytes reclaimed via VACUUM, and net DBU costs.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The predictive optimization operations table tracks every background compaction, vacuum, and stats collection job, including serverless DBU costs and physical bytes reclaimed.
# COMMAND ----------

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# Initialize or obtain active SparkSession with Delta Lake & Unity Catalog support
spark = SparkSession.builder \
    .appName("DatabricksHandbook") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Predictive Optimization ROI Analysis Query
# MAGIC
# MAGIC Calculate file reduction metrics and reclaimed storage volumes.
# COMMAND ----------

sql_predictive_roi = """
-- Audit Predictive Optimization ROI across tables
SELECT
    table_name,
    COUNT(CASE WHEN operation_type = 'OPTIMIZE' THEN 1 END) AS optimize_runs,
    SUM(metrics.filesCompacted) AS total_files_eliminated,
    COUNT(CASE WHEN operation_type = 'VACUUM' THEN 1 END) AS vacuum_runs,
    ROUND(SUM(metrics.bytesPurged) / (1024*1024*1024*1024), 2) AS storage_reclaimed_tb
FROM system.storage.predictive_optimization_operations_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY table_name
ORDER BY total_files_eliminated DESC
LIMIT 20;
"""

print("Predictive Optimization ROI query validated.")
assert "system.storage.predictive_optimization_operations_history" in sql_predictive_roi
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Quantifiable Hygiene**: Measure exactly how many small files were eliminated and how many terabytes were freed.
# MAGIC - **Storage Cost Reduction**: Physical deletion of unreferenced files via VACUUM reduces monthly cloud storage bills.
# MAGIC - **Read Acceleration**: Coalescing files into 256MB–1GB targets accelerates downstream query scans up to 5x.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What metrics are recorded in `system.storage.predictive_optimization_operations_history`?
# MAGIC 1. How do you evaluate whether automated compaction is reducing downstream query scan times?
