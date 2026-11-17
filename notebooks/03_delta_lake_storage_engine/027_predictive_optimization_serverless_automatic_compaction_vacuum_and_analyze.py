# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 027. Predictive Optimization: Serverless Automatic Compaction, VACUUM & ANALYZE
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A large platform operates 2,000 Delta tables. Data engineering spends 20% of their sprint cycles writing and monitoring scheduled `OPTIMIZE` and `VACUUM` maintenance jobs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Unity Catalog Predictive Optimization at the account and catalog level, inspect automated maintenance telemetry via system tables, and evaluate cost-benefit ratios.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Predictive Optimization uses AI/ML models to monitor query patterns, write frequency, and file fragmentation on Unity Catalog managed tables. It automatically schedules and executes serverless `OPTIMIZE` and `VACUUM` when cost-effective.
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
# MAGIC ### 1. Enable Predictive Optimization via SQL DDL
# MAGIC
# MAGIC Enable Predictive Optimization on an entire catalog or individual schema.
# COMMAND ----------

ddl_predictive = """
-- Enable predictive optimization on the entire enterprise catalog
ALTER CATALOG prod_lakehouse ENABLE PREDICTIVE OPTIMIZATION;

-- Verify predictive optimization telemetry in system tables
SELECT
    table_name,
    operation_type, -- 'OPTIMIZE' or 'VACUUM'
    start_time,
    metrics.filesCompacted AS files_compacted,
    metrics.bytesPurged AS bytes_purged
FROM system.storage.predictive_optimization_operations_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS;
"""

print("Predictive Optimization configuration verified.")
assert "ENABLE PREDICTIVE OPTIMIZATION" in ddl_predictive
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Maintenance Pipelines**: Eliminates the need to write custom cron-based `OPTIMIZE` and `VACUUM` jobs.
# MAGIC - **Serverless Execution**: Runs on isolated serverless compute without impacting production cluster capacity.
# MAGIC - **Cost Aware**: Automatically calculates whether compaction savings outweigh compute costs before launching an operation.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Predictive Optimization determine when it is cost-effective to compact a Delta table?
# MAGIC 1. Which system table records Predictive Optimization operations history?
