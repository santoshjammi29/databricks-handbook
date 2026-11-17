# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 052. Repair and Rerun Workflows: Surgical Partial DAG Replay on Upstream Failures
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC In a 12-task pipeline that took 3 hours to process 10 tasks, Task 11 failed due to a schema bug in an external dimension table. Re-running the entire 3-hour job from scratch violates executive SLAs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the 'Repair and Rerun' operational workflow in Databricks Jobs, executing only the failed task and its downstream children while preserving upstream state.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Workflows records the state of each task in a job run. The Repair and Rerun capability allows operators to fix the underlying issue and replay only failed and downstream tasks, saving hours of compute time.
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
# MAGIC ### 1. Repair and Rerun DAG State Simulation
# MAGIC
# MAGIC Simulate partial DAG state and determine which tasks require re-execution.
# COMMAND ----------

job_run_state = {
    "run_id": 998822,
    "tasks": {
        "task_1_bronze": "SUCCESS",
        "task_2_silver": "SUCCESS",
        "task_3_feature_prep": "SUCCESS",
        "task_4_model_training": "FAILED", # FAILED TASK
        "task_5_model_evaluation": "UPSTREAM_FAILED" # SKIPPED CHILD
    }
}

# Repair algorithm: find failed tasks and all downstream dependencies
tasks_to_rerun = [k for k, v in job_run_state["tasks"].items() if v in ("FAILED", "UPSTREAM_FAILED")]
preserved_tasks = [k for k, v in job_run_state["tasks"].items() if v == "SUCCESS"]

print(f"Tasks Preserved (Zero re-computation): {preserved_tasks}")
print(f"Tasks Surgically Re-executed: {tasks_to_rerun}")
assert len(tasks_to_rerun) == 2
assert len(preserved_tasks) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **SLA Protection**: Saves hours of re-computation by skipping completed upstream tasks.
# MAGIC - **Cost Efficient**: Prevents paying twice for successful heavy ETL transformations.
# MAGIC - **Idempotent Sinks**: Ensure target tables support safe retries via `MERGE INTO` or atomic overwrites.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does the Repair and Rerun feature in Databricks Workflows preserve upstream task context?
# MAGIC 1. Can you alter task parameters before triggering a Repair and Rerun?
