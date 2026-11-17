# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 051. Serverless Workflows: Zero-Startup-Latency Scheduling & Managed Concurrency
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise runs 500 small batch jobs every hour. On classic compute, each job spends 5 minutes booting VMs to execute 30 seconds of code. Infrastructure waste exceeds 80%.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy and benchmark Serverless Workflows, demonstrating instant task execution (< 5 seconds), automated horizontal scaling, and complete elimination of VM provisioning overhead.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Serverless compute for Lakeflow Jobs provisions pre-warmed container micro-VMs in seconds. It scales worker capacity dynamically to match workload demand and scales to zero immediately upon job completion.
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
# MAGIC ### 1. Serverless vs. Classic Job Compute Latency Model
# MAGIC
# MAGIC Calculate time and cost savings achieved by migrating to Serverless Workflows.
# COMMAND ----------

def evaluate_serverless_savings(daily_jobs: int, avg_execution_sec: int):
    # Classic: 300 seconds startup + execution
    classic_runtime_sec = (300 + avg_execution_sec) * daily_jobs
    # Serverless: 3 seconds startup + execution
    serverless_runtime_sec = (3 + avg_execution_sec) * daily_jobs

    saved_seconds = classic_runtime_sec - serverless_runtime_sec
    saved_hours = saved_seconds / 3600
    return {"classic_hours": classic_runtime_sec / 3600, "serverless_hours": serverless_runtime_sec / 3600, "saved_hours": saved_hours}

savings = evaluate_serverless_savings(daily_jobs=500, avg_execution_sec=60)
print(f"Classic Daily Compute Hours: {savings['classic_hours']:.1f} hrs")
print(f"Serverless Daily Compute Hours: {savings['serverless_hours']:.1f} hrs")
print(f"Daily Wasted Compute Hours Eliminated: {savings['saved_hours']:.1f} hrs")
assert savings["serverless_hours"] < savings["classic_hours"] / 4
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Instant Start**: Tasks start in 2-4 seconds instead of 4-7 minutes.
# MAGIC - **Zero Cluster Configuration**: No need to tune VM node types, DBR versions, or driver memory.
# MAGIC - **Optimized for Micro-Batches**: Drastically reduces costs for short, frequent jobs.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Serverless compute for Workflows eliminate VM provisioning latency?
# MAGIC 1. What are the networking and storage access prerequisites for enabling Serverless Workflows?
