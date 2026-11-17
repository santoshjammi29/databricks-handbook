# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 048. Cluster Allocation Strategy: Ephemeral Job Clusters vs. Shared Compute Pools
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data engineering team wants to minimize cluster initialization time (4-6 minutes per task) without incurring the higher cost of running an all-day All-Purpose cluster.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Evaluate and configure cluster allocation strategies: (1) Ephemeral New Clusters per task, (2) Shared Job Clusters across multiple tasks, and (3) Pre-warmed Instance Pools.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC In a multi-task job, tasks can share a single **Job Cluster** (`job_cluster_key`), eliminating VM spinup time for downstream tasks while maintaining the lower Job DBU pricing tier. Pre-warmed Instance Pools reduce VM provisioning latency to under 45 seconds.
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
# MAGIC ### 1. Shared Job Cluster Configuration Analysis
# MAGIC
# MAGIC Compare cold-start provisioning delays and DBU consumption models.
# COMMAND ----------

cluster_strategies = {
    "New_Cluster_Per_Task": {
        "spinup_time": "4-7 minutes per task",
        "isolation": "Complete VM isolation between tasks",
        "cost_efficiency": "Moderate; repeated VM initialization overhead"
    },
    "Shared_Job_Cluster": {
        "spinup_time": "4-7 minutes once for Task 1; instant for Tasks 2-N",
        "isolation": "Shared driver/worker across DAG tasks; cluster terminates when job completes",
        "cost_efficiency": "High; eliminates repeated startup lag at Job DBU rate"
    },
    "Instance_Pool": {
        "spinup_time": "30-60 seconds (pre-warmed VMs)",
        "isolation": "Clean OS boot from pooled instances",
        "cost_efficiency": "High; incurs idle VM cloud cost only for minimum idle instances"
    }
}

for name, strat in cluster_strategies.items():
    print(f"[{name}]\n  Spinup: {strat['spinup_time']}\n  Efficiency: {strat['cost_efficiency']}\n")

assert "Shared driver/worker" in cluster_strategies["Shared_Job_Cluster"]["isolation"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Use `job_clusters`**: Define a single `job_cluster_key` in DABs so all DAG tasks share the cluster.
# MAGIC - **Ephemeral Teardown**: Shared job clusters terminate automatically when the final task finishes.
# MAGIC - **Instance Pools**: Use pools for latency-sensitive batch pipelines requiring rapid VM acquisition.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between sharing a Job Cluster across tasks in a workflow vs. using an All-Purpose cluster?
# MAGIC 1. How do Instance Pools reduce cluster startup latency?
