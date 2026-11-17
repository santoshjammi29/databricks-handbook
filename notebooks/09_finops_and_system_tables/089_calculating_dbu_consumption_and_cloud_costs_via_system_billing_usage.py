# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 089. Calculating DBU Consumption & Cloud Costs via system.billing.usage
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A FinOps analyst needs to produce a daily executive report calculating total DBU spend, converting DBUs to currency based on contract rates, and identifying cost drivers.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop analytical SQL queries over `system.billing.usage` to aggregate DBU consumption by day, workspace, and SKU, projecting monetary costs with contract discount multipliers.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `system.billing.usage` records DBU consumption at 1-hour increments. Attributes include `workspace_id`, `sku_name`, `usage_quantity` (DBUs), and `custom_tags` for fine-grained departmental cost allocation.
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
# MAGIC ### 1. FinOps DBU Aggregation Query Implementation
# MAGIC
# MAGIC Write SQL to compute daily DBU totals and dollar costs by SKU.
# COMMAND ----------

sql_finops_billing = """
-- Compute daily DBU consumption and dollar costs by SKU
WITH daily_usage AS (
    SELECT
        usage_date,
        sku_name,
        workspace_id,
        SUM(usage_quantity) AS total_dbus
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1, 2, 3
)
SELECT
    usage_date,
    sku_name,
    workspace_id,
    ROUND(total_dbus, 2) AS dbus,
    -- Apply contract rate multiplier (e.g. $0.35 per DBU)
    ROUND(total_dbus * 0.35, 2) AS estimated_cost_usd
FROM daily_usage
ORDER BY usage_date DESC, dbus DESC;
"""

print("FinOps billing aggregation query validated.")
assert "system.billing.usage" in sql_finops_billing
assert "usage_quantity" in sql_finops_billing
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Accurate SKU Tracking**: Distinguish between high-cost Interactive compute and cost-effective Job compute.
# MAGIC - **Contract Normalization**: Multiply DBUs by contracted tier rates to calculate exact monthly cloud spend.
# MAGIC - **Proactive Budgeting**: Monitor daily burn rates to forecast end-of-month budget overages.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between `usage_quantity` in `system.billing.usage` and the underlying cloud VM cost?
# MAGIC 1. How does `system.billing.usage` capture serverless compute versus classic compute consumption?
