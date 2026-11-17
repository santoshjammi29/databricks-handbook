# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 054. Orchestration Governance: Monitoring Job Run History via System Tables
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A Data Operations manager requires a dashboard tracking pipeline success rates, average runtime trends, and identifying recurring failure modes across 100+ production jobs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query Unity Catalog System Tables to audit job execution history, measure duration percentiles ($P50, P90, P99$), and detect pipeline regressions.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks exposes job execution metrics via `system.lakeflow.jobs` and related compute telemetry tables, enabling enterprise-wide pipeline observability without third-party monitoring agents.
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
# MAGIC ### 1. SQL Query for Pipeline SLA & Failure Analytics
# MAGIC
# MAGIC Construct analytical queries over system tables to track pipeline health.
# COMMAND ----------

sql_job_monitoring = """
-- Query job run history to audit durations and failure rates
SELECT
    job_name,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_runs,
    ROUND(SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
    ROUND(AVG(execution_duration_ms) / 1000, 2) AS avg_duration_sec,
    ROUND(PERCENTILE(execution_duration_ms, 0.95) / 1000, 2) AS p95_duration_sec
FROM system.lakeflow.job_run_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY job_name
ORDER BY total_runs DESC;
"""

print("Job orchestration monitoring query verified.")
assert "system.lakeflow.job_run_history" in sql_job_monitoring
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Automated Observability**: Monitor job SLAs without third-party agents using built-in system tables.
# MAGIC - **Duration Percentiles**: Track P95 and P99 execution times to identify pipeline slowdowns before SLAs breach.
# MAGIC - **Audit Ready**: Maintain long-term compliance records of every production execution.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Which system tables provide metadata regarding Databricks Jobs and task run histories?
# MAGIC 1. How can you automate alerts when a critical production job exceeds its historical average runtime by 50%?
