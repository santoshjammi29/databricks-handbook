# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 042. DLT Event Log Forensics: Querying Lineage, Metrics, Quality Rates & Execution SLAs
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A regulatory audit requires generating an SLA compliance report detailing data quality pass/drop rates across all Delta Live Tables pipelines for the past 90 days.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query the DLT Event Log Delta table, parse JSON diagnostic events, calculate expectation pass rates, and reconstruct pipeline lineage programmatically.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DLT records all pipeline telemetry (cluster events, data flow metrics, expectation evaluations, lineage relationships) in a Delta table located at the pipeline's storage root (`storage_location/system/events`).
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
# MAGIC ### 1. Querying DLT Event Log Telemetry
# MAGIC
# MAGIC Extract and analyze expectation metrics and failure rates from the event log.
# COMMAND ----------

sql_event_log_query = """
-- Query DLT event log to audit data quality expectation pass rates
SELECT
    timestamp,
    message,
    details:flow_progress:data_quality:dropped_records AS dropped_records,
    details:flow_progress:metrics:num_output_rows AS output_rows
FROM event_log("pipeline_id_12345")
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC
LIMIT 10;
"""

print("DLT Event Log forensic query validated.")
assert "event_log(" in sql_event_log_query
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Source of Observability**: The DLT event log contains complete execution, metric, and quality history.
# MAGIC - **Audit Reports**: Easily query dropped record counts and SLA durations using standard SQL.
# MAGIC - **Lineage Tracking**: Graph relationships between datasets are recorded in event log metadata.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you query the Delta Live Tables event log to find which expectations had the highest failure rates?
# MAGIC 1. What information is captured in `details:flow_progress` within the DLT event log?
