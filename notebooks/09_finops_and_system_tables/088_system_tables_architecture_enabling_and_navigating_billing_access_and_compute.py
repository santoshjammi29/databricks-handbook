# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 088. System Tables Architecture: Enabling and Navigating billing, access, and compute
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Foundational`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise Cloud Center of Excellence (CCoE) needs automated visibility into compute usage, security audits, and storage optimization without managing custom logging pipelines.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Unity Catalog System Tables at the account level, explore system schemas (`system.billing`, `system.access`, `system.compute`, `system.storage`), and verify metadata query permissions.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC System Tables are a Databricks-hosted analytical store of operational telemetry. They reside in the `system` catalog, populated automatically and queryable via standard SQL with zero data egress or pipeline maintenance.
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
# MAGIC ### 1. System Tables Schema Hierarchy & Scope
# MAGIC
# MAGIC Map operational domains to their corresponding system tables.
# COMMAND ----------

system_table_schemas = {
    "system.billing.usage": "Historical DBU consumption records across all workspaces, SKUs, and cluster tags",
    "system.access.audit": "Audit logs capturing user logins, table access, DDL, and permission grants",
    "system.compute.clusters": "Cluster lifecycle events, node configurations, and creation metadata",
    "system.compute.query_history": "DBSQL query execution metrics, durations, rows produced, and memory spills",
    "system.storage.predictive_optimization_operations_history": "Telemetry on serverless OPTIMIZE and VACUUM jobs"
}

for tbl, desc in system_table_schemas.items():
    print(f"[{tbl}]\n  Purpose: {desc}\n")

assert "system.billing.usage" in system_table_schemas
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero-ETL Observability**: Operational metrics appear automatically in the `system` catalog.
# MAGIC - **Account-Level Visibility**: Queries aggregate data across all workspaces in the cloud account.
# MAGIC - **Granular Retention**: Retains long-term historical telemetry (typically 1 year) for compliance audits.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you enable Unity Catalog System Tables for an entire Databricks account?
# MAGIC 1. What system tables provide visibility into query execution bottlenecks and cluster utilization?
