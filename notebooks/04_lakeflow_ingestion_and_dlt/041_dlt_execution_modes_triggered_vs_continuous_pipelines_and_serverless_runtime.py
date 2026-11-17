# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 041. DLT Execution Modes: Triggered vs. Continuous Pipelines & Serverless Runtime
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A lakehouse architect must optimize pipeline costs: high-priority fraud detection requires sub-minute continuous execution, while standard billing reconciliation runs hourly.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Compare Triggered (batch) vs. Continuous (streaming) pipeline execution modes in DLT, configure Serverless DLT compute, and analyze DBU consumption curves.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Triggered pipelines start compute, process all available data once, and terminate (ideal for hourly/daily batch ETL). Continuous pipelines run indefinitely with dedicated streaming micro-batches (sub-second latency). Serverless DLT removes cluster configuration and scales instantly.
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
# MAGIC ### 1. DLT Pipeline Execution Mode Decision Matrix
# MAGIC
# MAGIC Evaluate latency requirements vs compute cost across DLT execution models.
# COMMAND ----------

dlt_modes = {
    "Triggered_Serverless": {
        "latency": "Minutes to hours (scheduled)",
        "cost_efficiency": "High: Scales down to 0 DBUs immediately upon batch completion",
        "best_for": "Medallion batch pipelines, hourly reporting, cost-sensitive workloads"
    },
    "Continuous_Enhanced": {
        "latency": "Sub-second to seconds",
        "cost_efficiency": "Moderate: Clusters remain continuously warm and active",
        "best_for": "Real-time fraud alerting, live IoT telemetry, sub-minute SLAs"
    }
}

for mode, attrs in dlt_modes.items():
    print(f"[{mode}]\n  Latency: {attrs['latency']}\n  Cost: {attrs['cost_efficiency']}\n")

assert "Scales down to 0 DBUs" in dlt_modes["Triggered_Serverless"]["cost_efficiency"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Triggered Mode for Batch**: Always use Triggered mode unless the business explicitly demands sub-minute SLA.
# MAGIC - **Serverless DLT**: Eliminates cluster startup delay and automatically optimizes worker memory.
# MAGIC - **Enhanced Autoscaling**: DLT allocates compute based on streaming backlog queue depths.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. When should an enterprise use Continuous mode versus Triggered mode in Delta Live Tables?
# MAGIC 1. How does Serverless DLT handle worker autoscaling compared to Classic DLT?
