# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 055. Serverless SQL Warehouses: Instant Spin-up, Autoscaling Policies & Sizing T-Shirts
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Foundational`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A business intelligence team experiences unpredictable query concurrency: 5 analysts query dashboards at night, but 200 executives access them simultaneously on Monday mornings.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure a Serverless SQL Warehouse with optimal T-shirt sizing (2X-Small to 4X-Large), auto-stop policies (5-10 minutes), and autoscaling bounds (min/max clusters).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Serverless SQL Warehouses use pre-warmed compute pools managed by Databricks, starting in 2-4 seconds. They scale out clusters horizontally under concurrency pressure and terminate aggressively on idle to prevent wasted DBUs.
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
# MAGIC ### 1. Serverless SQL Warehouse T-Shirt Sizing Matrix
# MAGIC
# MAGIC Evaluate cluster sizing and concurrent query capacity.
# COMMAND ----------

warehouse_tiers = {
    "2X-Small": {"cores": 4, "ram_gb": 16, "target_queries": "Light ad-hoc analytics, exploratory queries"},
    "Small": {"cores": 16, "ram_gb": 64, "target_queries": "Standard department BI dashboards (Power BI / Tableau)"},
    "Large": {"cores": 64, "ram_gb": 256, "target_queries": "Heavy aggregations, multi-billion row joins"},
    "4X-Large": {"cores": 256, "ram_gb": 1024, "target_queries": "Enterprise-wide high-concurrency peak reporting"}
}

for size, specs in warehouse_tiers.items():
    print(f"[{size}] Cores: {specs['cores']} | RAM: {specs['ram_gb']}GB | {specs['target_queries']}")

assert warehouse_tiers["Small"]["cores"] == 16
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Instant Start**: Eliminates the 5-7 minute VM startup lag of classic warehouses.
# MAGIC - **Aggressive Auto-Stop**: Set auto-stop to 10 minutes; since startup is 2 seconds, no cold start penalty exists.
# MAGIC - **Cost Scaling**: Scale out max clusters during peak hours and allow scale-to-zero at night.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Serverless SQL Warehouses handle cluster autoscaling differently from Classic SQL Warehouses?
# MAGIC 1. What is the recommended auto-stop idle timeout for Serverless SQL Warehouses?
