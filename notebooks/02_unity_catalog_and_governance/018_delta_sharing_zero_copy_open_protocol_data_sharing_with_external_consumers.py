# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 018. Delta Sharing: Zero-Copy Open Protocol Data Sharing with External Consumers
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial data vendor sells daily market pricing feeds to external hedge funds and academic institutions that do not use Databricks. Data must be shared securely without copying or FTP exports.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure an open Delta Sharing Share, create recipient profiles, generate secure credential activation tokens, and read shared tables using Python and Pandas.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Sharing is the industry's first open source protocol for secure, real-time data exchange across platforms. External recipients query data directly using Python, Pandas, Power BI, Apache Spark, or DuckDB without running Databricks compute.
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
# MAGIC ### 1. Delta Sharing Protocol Flow & Token Activation
# MAGIC
# MAGIC Model the recipient credential activation and secure file URL generation flow.
# COMMAND ----------

# Simulate Delta Sharing protocol metadata
share_spec = {
    "share_name": "market_daily_pricing_share",
    "tables": ["prod_catalog.gold.eod_stock_prices"],
    "recipient_name": "hedge_fund_alpha",
    "token_expiration": "2027-01-01T00:00:00Z"
}

print(f"Share: {share_spec['share_name']}")
print(f"Recipient: {share_spec['recipient_name']}")
print(f"Shared Tables: {share_spec['tables']}")
assert len(share_spec["tables"]) == 1
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Open Protocol**: Recipients can use Python, DuckDB, Power BI, or Excel without a Databricks account.
# MAGIC - **Zero Data Copying**: Data remains in the provider's cloud storage; recipients receive pre-signed short-lived URLs.
# MAGIC - **Audited Access**: Every external query is logged with recipient ID and IP address.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta Sharing differ from cloud-specific data sharing solutions like Snowflake Data Sharing?
# MAGIC 1. How does the Delta Sharing protocol ensure security when returning cloud storage pre-signed URLs to recipients?
