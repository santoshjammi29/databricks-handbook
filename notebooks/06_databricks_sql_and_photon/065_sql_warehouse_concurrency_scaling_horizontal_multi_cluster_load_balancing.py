# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 065. SQL Warehouse Concurrency Scaling: Horizontal Multi-Cluster Load Balancing
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A company has 1,000 active Power BI users refreshing dashboards at the start of business. A single SQL warehouse cluster saturates, queueing queries and causing dashboard timeouts.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure horizontal multi-cluster load balancing on a Serverless SQL Warehouse, tune maximum cluster bounds (1 to 10), and analyze scaling policies (Economy vs. Pro).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks SQL Warehouses scale horizontally by adding identical compute clusters behind a shared load balancer. When query concurrency exceeds single-cluster capacity, additional clusters launch automatically to handle the queue.
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
# MAGIC ### 1. Multi-Cluster Sizing & Scaling Policy Model
# MAGIC
# MAGIC Simulate warehouse cluster autoscaling under variable query concurrency.
# COMMAND ----------

def evaluate_warehouse_scaling(active_queries: int, queries_per_cluster: int = 10, min_clusters: int = 1, max_clusters: int = 5):
    needed_clusters = (active_queries + queries_per_cluster - 1) // queries_per_cluster
    allocated_clusters = max(min_clusters, min(needed_clusters, max_clusters))
    is_queued = needed_clusters > max_clusters
    return {"allocated_clusters": allocated_clusters, "is_queued": is_queued}

peak_load = evaluate_warehouse_scaling(active_queries=45, queries_per_cluster=10, min_clusters=1, max_clusters=5)
print(f"Under 45 Concurrent Queries:")
print(f"  Allocated Clusters: {peak_load['allocated_clusters']}")
print(f"  Queued: {peak_load['is_queued']}")
assert peak_load["allocated_clusters"] == 5
assert not peak_load["is_queued"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Horizontal Concurrency**: Add clusters to handle concurrent users without increasing individual VM size.
# MAGIC - **Scaling Policy**: `Pro` scales out immediately for low latency; `Economy` scales conservatively to save cost.
# MAGIC - **Sub-Second Scale-Down**: Serverless clusters scale down rapidly once concurrency subsides.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does multi-cluster autoscaling in Databricks SQL prevent query queueing during peak hours?
# MAGIC 1. When should an engineer increase cluster T-shirt size versus increasing the maximum cluster count?
