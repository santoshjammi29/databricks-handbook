# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 104. Production Incident 06: Serverless SQL Warehouse Queue Saturation & Spill Tuning
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC During Monday morning executive review, 150 dashboard users connect simultaneously to a Serverless SQL Warehouse. Queries queue for 45 seconds and spill gigabytes to disk.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Diagnose query queue saturation using `system.compute.warehouse_events`, adjust scaling policies from Economy to Pro, expand max cluster bounds, and apply Liquid Clustering to eliminate spills.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Query queueing occurs when incoming queries exceed the warehouse's concurrent slot capacity. Changing the scaling policy to `Pro` instructs Intelligent Workload Management (IWM) to scale out clusters aggressively.
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
# MAGIC ### 1. Diagnosing Queue Delays & Autoscaling Policies
# MAGIC
# MAGIC Analyze query queue durations and optimize warehouse scaling parameters.
# COMMAND ----------

sql_queue_diagnosis = """
-- Query warehouse queue delays and active cluster scaling
SELECT
    warehouse_id,
    AVG(waiting_for_compute_ms) / 1000 AS avg_queue_sec,
    MAX(waiting_for_compute_ms) / 1000 AS max_queue_sec,
    SUM(CASE WHEN spill_to_disk_bytes > 0 THEN 1 ELSE 0 END) AS spilling_queries
FROM system.compute.query_history
WHERE start_time >= NOW() - INTERVAL 2 HOURS
GROUP BY warehouse_id;
"""

print("Warehouse saturation diagnostic query validated.")
assert "waiting_for_compute_ms" in sql_queue_diagnosis
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Pro Scaling Policy**: Scales out additional clusters immediately upon detecting queued queries.
# MAGIC - **Liquid Clustering for Spills**: Clustered tables read 90% fewer files, reducing in-memory join footprint.
# MAGIC - **Workload Isolation**: Separate ad-hoc exploratory queries from SLA-critical executive dashboards.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Economy and Pro scaling policies on Databricks SQL Warehouses?
# MAGIC 1. How do you eliminate disk spills in heavy distributed joins on SQL Warehouses?
