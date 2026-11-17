# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 006. Databricks REST API 2.1 Programmatic Workspace & Compute Lifecycle Management
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A platform engineering team requires an automated REST API daemon that audits all running clusters, restarts stalled worker nodes, and purges empty workspace directories.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop modular Python client code interacting with Databricks REST API 2.1 endpoints (`/api/2.1/clusters/list`, `/api/2.1/jobs/runs/cancel`, `/api/2.0/workspace/list`) with retry backoff and error handling.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The REST API 2.1 exposes granular control plane endpoints. The official Databricks SDK for Python (`databricks-sdk`) wraps these endpoints with type safety and automatic pagination.
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
# MAGIC ### 1. Programmatic Cluster Auditing with REST API Payload Simulation
# MAGIC
# MAGIC Query cluster endpoints and inspect state transitions (RUNNING, TERMINATED, RESIZING).
# COMMAND ----------

import datetime

# Mock cluster response payload matching REST API 2.1
mock_api_clusters = {
    "clusters": [
        {"cluster_id": "0101-120000-abc123", "cluster_name": "prod-etl-01", "state": "RUNNING", "num_workers": 4},
        {"cluster_id": "0101-120001-xyz789", "cluster_name": "adhoc-analyst", "state": "TERMINATED", "num_workers": 0},
        {"cluster_id": "0101-120002-def456", "cluster_name": "zombie-dev", "state": "RUNNING", "num_workers": 8}
    ]
}

# Filter running clusters
running = [c for c in mock_api_clusters["clusters"] if c["state"] == "RUNNING"]
total_active_workers = sum(c["num_workers"] for c in running)

print(f"Active Running Clusters: {len(running)}")
print(f"Total Dedicated Workers: {total_active_workers}")
assert len(running) == 2, "Expected 2 active running clusters!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **API Versioning**: Use REST API 2.1 for Unity Catalog and modern workspace operations.
# MAGIC - **Databricks SDK**: Prefer `WorkspaceClient` from `databricks-sdk` over raw `requests` calls for built-in retries.
# MAGIC - **Rate Limiting**: Handle HTTP 429 Too Many Requests with exponential jitter backoff.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you handle API rate limits (HTTP 429) when polling Databricks job run statuses?
# MAGIC 1. What is the difference between `/api/2.0/jobs` and `/api/2.1/jobs`?
