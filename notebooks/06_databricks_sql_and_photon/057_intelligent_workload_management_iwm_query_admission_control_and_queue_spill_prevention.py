# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 057. Intelligent Workload Management (IWM): Query Admission Control & Queue Spill Prevention
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC During quarter-end financial closes, 50 analysts run massive queries simultaneously. Without admission control, clusters run out of memory, crash, and drop connections.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the mechanics of Databricks SQL Intelligent Workload Management (IWM), analyzing dynamic query admission control, queueing behavior, and memory spill mitigation.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC IWM uses ML-based runtime prediction to govern query admission on SQL Warehouses. Instead of letting all queries run concurrently and thrash RAM, IWM queues incoming queries and schedules them smoothly.
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
# MAGIC ### 1. IWM Admission Control Mechanics Model
# MAGIC
# MAGIC Simulate query admission decisions based on predicted memory and cluster capacity.
# COMMAND ----------

class MockIWMAdmissionController:
    def __init__(self, max_concurrent_queries=10, max_memory_gb=64):
        self.max_queries = max_concurrent_queries
        self.max_ram = max_memory_gb
        self.active_queries = 0
        self.active_ram = 0

    def admit_query(self, query_id: str, estimated_ram_gb: int) -> str:
        if self.active_queries < self.max_queries and (self.active_ram + estimated_ram_gb) <= self.max_ram:
            self.active_queries += 1
            self.active_ram += estimated_ram_gb
            return f"Query {query_id}: ADMITTED (Running on cluster)"
        else:
            return f"Query {query_id}: QUEUED (Waiting for capacity to prevent memory spill)"

iwm = MockIWMAdmissionController(max_concurrent_queries=2, max_memory_gb=32)
print(iwm.admit_query("Q1", 16))
print(iwm.admit_query("Q2", 12))
print(iwm.admit_query("Q3", 8)) # Should queue

assert "QUEUED" in iwm.admit_query("Q3", 8)
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Spill Prevention**: Queuing queries temporarily is faster than letting multiple queries spill gigabytes to disk.
# MAGIC - **Fast Auto-Scaling**: IWM signals the warehouse cluster manager to launch additional clusters when queue depths grow.
# MAGIC - **Zero Cluster Crashes**: Protects cluster stability under severe concurrent load.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is Intelligent Workload Management (IWM) in Databricks SQL Warehouses?
# MAGIC 1. How does IWM differentiate between quick BI lookups and long-running heavy aggregation queries?
