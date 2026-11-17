# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 093. Compute Right-Sizing: Detecting Zombie Clusters & Low-CPU Utilization
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise cluster audit discovered 15 interactive clusters that were left running overnight with 0% CPU utilization, wasting $1,200 per day in idle compute.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query compute and billing system tables to detect zombie clusters (active clusters with zero queries or < 10% CPU utilization for > 2 hours) and automate notifications.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Right-sizing requires correlating cluster uptime from `system.compute.clusters` with query execution counts from `system.compute.query_history` to identify idle compute resources.
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
# MAGIC ### 1. Zombie Cluster Detection Algorithm
# MAGIC
# MAGIC Simulate identifying idle clusters running with zero active queries.
# COMMAND ----------

clusters_telemetry = [
    {"cluster_id": "cl-001", "name": "prod-etl-stream", "uptime_hours": 24, "queries_run": 14500, "status": "HEALTHY_ACTIVE"},
    {"cluster_id": "cl-002", "name": "analyst-sandbox-1", "uptime_hours": 14, "queries_run": 0, "status": "ZOMBIE_IDLE"},
    {"cluster_id": "cl-003", "name": "dev-scratch", "uptime_hours": 8, "queries_run": 2, "status": "LOW_UTILIZATION"}
]

zombies = [c for c in clusters_telemetry if c["queries_run"] == 0 and c["uptime_hours"] > 2]
print(f"Detected Zombie Idle Clusters: {len(zombies)}")
for z in zombies:
    print(f"  ALERT: {z['name']} ({z['cluster_id']}) has been idle for {z['uptime_hours']} hours!")

assert len(zombies) == 1
assert zombies[0]["cluster_id"] == "cl-002"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Eliminate Zombie Spend**: Enforce automated 15-minute auto-termination to kill idle clusters.
# MAGIC - **Right-Sizing Audits**: Downsize worker VM types from 8-core to 4-core if average CPU stays under 20%.
# MAGIC - **Automated Remediation**: Terminate zombie clusters programmatically via Databricks REST API.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you correlate compute cluster runtime with actual query activity to identify idle resources?
# MAGIC 1. What cluster policy settings prevent developers from disabling auto-termination?
