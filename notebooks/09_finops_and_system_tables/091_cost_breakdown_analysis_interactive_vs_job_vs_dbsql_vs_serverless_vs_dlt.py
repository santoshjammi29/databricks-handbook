# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 091. Cost Breakdown Analysis: Interactive vs. Job vs. DBSQL vs. Serverless vs. DLT
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A VP of Data Engineering wants to know whether recent platform modernization efforts (migrating batch jobs to DLT and Serverless) successfully reduced interactive development waste.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author an analytical query categorizing spend into five workload pillars: Interactive Compute, Automated Jobs, SQL Warehouses, Serverless Workflows, and Delta Live Tables.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The `sku_name` attribute in `system.billing.usage` identifies the exact compute engine. Classifying SKUs enables architectural FinOps analysis to track migration from expensive interactive VMs to cost-optimized serverless engines.
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
# MAGIC ### 1. Workload Categorization Query Model
# MAGIC
# MAGIC Categorize SKUs into business workload buckets and compute percentage distribution.
# COMMAND ----------

sql_workload_breakdown = """
SELECT
    CASE
        WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Development'
        WHEN sku_name LIKE '%JOBS%' THEN 'Automated Batch Jobs'
        WHEN sku_name LIKE '%SQL%' THEN 'Databricks SQL / BI'
        WHEN sku_name LIKE '%DLT%' THEN 'Delta Live Tables'
        WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless Compute'
        ELSE 'Other Services'
    END AS workload_category,
    SUM(usage_quantity) AS total_dbus,
    ROUND(SUM(usage_quantity) * 100.0 / SUM(SUM(usage_quantity)) OVER (), 1) AS dbu_share_pct
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY 1
ORDER BY total_dbus DESC;
"""

print("Workload SKU breakdown query validated.")
assert "ALL_PURPOSE" in sql_workload_breakdown
assert "dbu_share_pct" in sql_workload_breakdown
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Healthy Ratio Benchmark**: Production enterprises should target < 20% Interactive and > 80% Automated/Serverless.
# MAGIC - **Migration ROI**: Track the reduction in `ALL_PURPOSE` spend as pipelines transition to DABs and Lakeflow.
# MAGIC - **Executive Summary**: Translate raw technical telemetry into clear business capability costs.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is considered a healthy ratio of Interactive vs. Automated Job DBU consumption in an enterprise?
# MAGIC 1. How can you identify scheduled batch workloads incorrectly running under an `ALL_PURPOSE` SKU?
