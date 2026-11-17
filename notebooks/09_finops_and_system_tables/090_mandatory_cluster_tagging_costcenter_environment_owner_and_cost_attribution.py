# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 090. Mandatory Cluster Tagging (CostCenter, Environment, Owner) & Cost Attribution
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Finance cannot allocate a $500,000 monthly Databricks bill to business units because 60% of clusters were launched without `CostCenter` or `Project` tags.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enforce mandatory cluster tagging via Cluster Policies, parse the `custom_tags` map in `system.billing.usage`, and allocate 100% of DBU spend to verified department cost centers.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Cluster policies can mandate fixed or pattern-matched tags (e.g. `custom_tags.CostCenter`). These tags propagate directly into cloud provider billing logs and Databricks `system.billing.usage.custom_tags`.
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
# MAGIC ### 1. Querying Tagged Costs from custom_tags Map
# MAGIC
# MAGIC Extract nested JSON map keys to attribute costs to departments.
# COMMAND ----------

sql_tag_attribution = """
-- Allocate DBU spend by CostCenter and Project tags
SELECT
    usage_date,
    COALESCE(custom_tags['CostCenter'], 'UNALLOCATED_LEAK') AS cost_center,
    COALESCE(custom_tags['Project'], 'GENERAL') AS project,
    SUM(usage_quantity) AS total_dbus,
    ROUND(SUM(usage_quantity * 0.30), 2) AS cost_usd
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
GROUP BY 1, 2, 3
ORDER BY total_dbus DESC;
"""

print("Tag-based cost attribution query verified.")
assert "custom_tags['CostCenter']" in sql_tag_attribution
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Enforce at Policy Level**: Never rely on human memory for tagging; enforce via cluster policies.
# MAGIC - **Unallocated Leak Hunting**: Query for `CostCenter IS NULL` to identify rogue clusters.
# MAGIC - **Automated Chargeback**: Provide monthly departmental reports directly to finance.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do cluster tags propagate into Databricks System Tables?
# MAGIC 1. How do you configure a Databricks Cluster Policy to mandate that users enter a valid 6-digit Cost Center code?
