# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 017. Lakehouse Federation: Querying Snowflake and Google BigQuery via Unity Catalog
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Following an enterprise acquisition, the analytics team must query financial ledgers in Snowflake and web telemetry in Google BigQuery alongside the core Databricks Lakehouse.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy foreign catalogs for Snowflake and BigQuery, analyze execution plans to ensure partition pruning, and optimize federated join performance.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Unity Catalog supports native connectors for cloud data warehouses (Snowflake, BigQuery, Redshift, Synapse). It leverages cloud IAM and OAuth for secure, credential-less cross-cloud federation.
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
# MAGIC ### 1. Cross-Cloud Federation Configuration Specification
# MAGIC
# MAGIC Define foreign connection parameters for Snowflake and BigQuery.
# COMMAND ----------

federated_connections = {
    "snowflake_prod": {
        "type": "SNOWFLAKE",
        "options": {"host": "xy12345.snowflakecomputing.com", "warehouse": "ANALYTICS_WH"},
        "auth": "OAuth / Key-Pair"
    },
    "bigquery_analytics": {
        "type": "BIGQUERY",
        "options": {"projectId": "enterprise-data-warehouse-prod"},
        "auth": "Google Service Account via Unity Catalog Storage Credential"
    }
}

for conn_name, cfg in federated_connections.items():
    print(f"Connection: {conn_name} | Type: {cfg['type']} | Auth: {cfg['auth']}")
assert len(federated_connections) == 2
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Multi-Warehouse Unification**: Query Snowflake, BigQuery, and Databricks in a single unified SQL statement.
# MAGIC - **Egress Cost Awareness**: Be cautious of cross-cloud data transfer egress fees when joining massive tables.
# MAGIC - **Governance Centralization**: Control who can access Snowflake tables via Databricks Unity Catalog permissions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What are the network latency and egress cost trade-offs when executing cross-cloud queries via Lakehouse Federation?
# MAGIC 1. How does Unity Catalog handle schema changes in remote Snowflake or BigQuery tables?
