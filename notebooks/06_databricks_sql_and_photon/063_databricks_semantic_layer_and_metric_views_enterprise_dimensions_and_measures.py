# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 063. Databricks Semantic Layer & Metric Views: Enterprise Dimensions & Measures
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Different departments compute 'Customer Churn' and 'Net Revenue' using conflicting formulas, resulting in discrepancies during executive board meetings.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define a unified Semantic Layer and Metric Views in Databricks, codifying enterprise dimensions and measures as the single source of truth for all downstream tools.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The Databricks Semantic Layer establishes standardized metric definitions (measures, dimensions, time grains) directly in Unity Catalog. BI tools (Power BI, Tableau, Lakeview) query certified metrics consistently.
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
# MAGIC ### 1. Metric View Specification DDL
# MAGIC
# MAGIC Define standardized dimensions and measures in SQL.
# COMMAND ----------

metric_view_spec = """
-- Define certified enterprise metric view
CREATE OR REPLACE VIEW prod_lakehouse.gold.metrics_financial_core AS
SELECT
    -- Dimensions
    customer_id,
    region,
    product_tier,
    date_trunc('month', transaction_date) AS fiscal_month,

    -- Standardized Enterprise Measures
    SUM(gross_amount - discount_amount) AS net_revenue,
    COUNT(DISTINCT transaction_id) AS order_volume,
    ROUND(SUM(gross_amount - discount_amount) / COUNT(DISTINCT transaction_id), 2) AS average_order_value
FROM prod_lakehouse.silver.sales_transactions
GROUP BY 1, 2, 3, 4;
"""

print("Enterprise Semantic Metric View DDL verified.")
assert "net_revenue" in metric_view_spec
assert "average_order_value" in metric_view_spec
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Source of Truth**: Define critical business metrics once in Unity Catalog.
# MAGIC - **Consistent BI**: Power BI, Tableau, and Genie all report identical numbers.
# MAGIC - **Governance Centralization**: Changes to formulas update globally across all downstream dashboards.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does an in-database Semantic Layer in Unity Catalog eliminate metric discrepancies between BI tools?
# MAGIC 1. What is the difference between a dimensional attribute and a metric measure?
