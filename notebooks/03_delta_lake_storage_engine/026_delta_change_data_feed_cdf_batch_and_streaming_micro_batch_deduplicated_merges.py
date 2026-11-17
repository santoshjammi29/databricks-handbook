# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 026. Delta Change Data Feed (CDF): Batch & Streaming Micro-Batch Deduplicated Merges
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A downstream data mart must consume only changes (inserts, updates, deletes) from the upstream customer master table. Re-scanning the 500M row table daily is cost-prohibitive.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Delta Change Data Feed (`delta.enableChangeDataFeed = true`), query change feeds in batch and streaming mode, handle `update_preimage` vs `update_postimage`, and execute deduplicated merges.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC When CDF is enabled, Delta Lake records row-level change events across all DML operations. Reading with `.option('readChangeFeed', 'true')` surfaces `_change_type` (`insert`, `update_preimage`, `update_postimage`, `delete`), `_commit_version`, and `_commit_timestamp`.
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
# MAGIC ### 1. Change Data Feed Event Stream Simulation
# MAGIC
# MAGIC Simulate CDF change records and execute deduplication before merging into the downstream Gold table.
# COMMAND ----------

cdf_raw_events = [
    {"customer_id": 101, "email": "a@old.com", "_change_type": "update_preimage", "_commit_version": 4},
    {"customer_id": 101, "email": "a@new.com", "_change_type": "update_postimage", "_commit_version": 4},
    {"customer_id": 102, "email": "b@corp.com", "_change_type": "insert", "_commit_version": 4},
    {"customer_id": 103, "email": "c@trash.com", "_change_type": "delete", "_commit_version": 4}
]

# Downstream consumption: Filter out update_preimage to retain target state
net_changes = [e for e in cdf_raw_events if e["_change_type"] != "update_preimage"]
print(f"Total Raw CDF Events: {len(cdf_raw_events)}")
print(f"Net Changes for Downstream Merge: {len(net_changes)}")
for row in net_changes:
    print(f"  ID {row['customer_id']}: Action = {row['_change_type'].upper()}")

assert len(net_changes) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Row-Level Changes**: Exposes exact inserts, updates, and deletes without full table diffing.
# MAGIC - **Deduplication Rule**: Always deduplicate micro-batches by `_commit_version DESC` before merging to prevent ambiguous match errors.
# MAGIC - **Audit Trail**: CDF provides a continuous, auditable event stream for downstream CDC subscribers.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What extra columns are returned when reading a Delta table with `readChangeFeed = true`?
# MAGIC 1. Why must you filter out `update_preimage` before executing an upsert into a downstream table?
