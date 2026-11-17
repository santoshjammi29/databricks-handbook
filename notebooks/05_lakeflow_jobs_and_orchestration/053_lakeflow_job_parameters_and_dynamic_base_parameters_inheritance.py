# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 053. Lakeflow Job Parameters & Dynamic Base Parameters Inheritance
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Foundational`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A reusable enterprise workflow template is executed across multiple business units and dates. The job must accept runtime parameters (`env`, `target_date`, `batch_id`) and propagate them to child tasks.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure top-level Job Parameters in Lakeflow Jobs, pass them into task `base_parameters`, and consume them via `dbutils.widgets.get()` inside notebooks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakeflow Jobs provides dynamic parameter substitution. Top-level job parameters can be referenced in task configurations using `{{job.parameters.param_name}}` and dynamic values like `{{job.start_time.iso_date}}`.
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
# MAGIC ### 1. Parameter Inheritance & Widget Binding
# MAGIC
# MAGIC Verify parameter substitution syntax and consumption in Python tasks.
# COMMAND ----------

# Simulate notebook widget extraction
mock_widgets = {
    "target_date": "2026-11-17",
    "environment": "production",
    "batch_size": "50000"
}

def get_job_param(key: str, default: str = "") -> str:
    return mock_widgets.get(key, default)

target_date = get_job_param("target_date")
env = get_job_param("environment")

print(f"Execution Target Date: {target_date} | Environment: {env}")
assert target_date == "2026-11-17"
assert env == "production"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Dynamic Variables**: Use built-in variables like `{{job.start_time.iso_date}}` for automated date slicing.
# MAGIC - **Widget Decoupling**: Notebooks can be tested interactively with default widget values or run via Jobs.
# MAGIC - **Parameter Scoping**: Override top-level parameters for specific tasks where needed.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What built-in dynamic parameter variables are available in Databricks Workflows?
# MAGIC 1. How do you pass dynamic parameters to a Databricks Job when triggering it via the REST API?
