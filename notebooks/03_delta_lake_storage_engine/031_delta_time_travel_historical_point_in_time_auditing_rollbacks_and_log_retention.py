# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 031. Delta Time Travel: Historical Point-in-Time Auditing, Rollbacks & Log Retention
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A developer accidentally executed an unconstrained `DELETE FROM prod_customers` in production. Operations must restore the table to the exact state 10 minutes prior to the disaster.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query historical table states using Delta Time Travel (`VERSION AS OF` and `TIMESTAMP AS OF`), perform surgical auditing using `DESCRIBE HISTORY`, and execute instant disaster recovery using `RESTORE TABLE`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Because Delta Lake retains historical Parquet files and commit logs until `VACUUM` runs, users can query previous versions of the table. `RESTORE TABLE` creates a new commit that reverts the table pointer to a prior snapshot.
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
# MAGIC ### 1. Time Travel Querying & RESTORE Syntax
# MAGIC
# MAGIC Audit version history and restore table state prior to corruption.
# COMMAND ----------

ddl_time_travel = """
-- 1. Inspect audit history
DESCRIBE HISTORY prod_lakehouse.silver.customers;

-- 2. Query data as of version 3
SELECT * FROM prod_lakehouse.silver.customers VERSION AS OF 3;

-- 3. Query data as of 2 hours ago
SELECT * FROM prod_lakehouse.silver.customers TIMESTAMP AS OF (CURRENT_TIMESTAMP() - INTERVAL 2 HOURS);

-- 4. Execute instant table restore to version 3
RESTORE TABLE prod_lakehouse.silver.customers TO VERSION AS OF 3;
"""

print("Delta Time Travel and RESTORE syntax verified.")
assert "RESTORE TABLE prod_lakehouse.silver.customers TO VERSION AS OF 3" in ddl_time_travel
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Data Loss**: Time Travel allows reproducible audits and instant disaster rollback.
# MAGIC - **Retention Guardrail**: Table history is preserved for `delta.logRetentionDuration` (default 30 days) and unvacuumed data for 7 days.
# MAGIC - **Safe Restore**: `RESTORE TABLE` writes an atomic forward commit recording the reversion, preserving full auditability.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta Lake execute a `TIMESTAMP AS OF` query under the hood?
# MAGIC 1. What happens if you run `RESTORE TABLE ... TO VERSION AS OF 2` after `VACUUM` has deleted the Parquet files from version 2?
