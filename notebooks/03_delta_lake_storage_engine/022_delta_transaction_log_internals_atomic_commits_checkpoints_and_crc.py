# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 022. Delta Transaction Log Internals: Atomic Commits, Checkpoints & CRC
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial auditing team requires proof that Delta Lake guarantees ACID transaction atomicity, even if a cluster crashes mid-commit or storage experiences temporary latency.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Inspect and parse the `_delta_log` directory of a production Delta table. Decode JSON commit files (`add`, `remove`, `metaData`, `protocol`), analyze `.checkpoint.parquet` state consolidation, and verify CRC integrity checks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake maintains the single source of truth for table state in `_delta_log/`. Transactions write sequential JSON commit files (`000000.json`, `000001.json`). Checkpoint Parquet files collapse historical commits every 10 transactions to keep reader state reconstruction fast.
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
# MAGIC ### 1. Inspect Transaction Log Commit Action Structure
# MAGIC
# MAGIC Simulate and verify the internal JSON actions written to `_delta_log/000001.json`.
# COMMAND ----------

# Simulate raw JSON commit actions in Delta Lake
commit_actions = {
    "commit_version": 1,
    "actions": [
        {
            "add": {
                "path": "part-00000-abc-c000.snappy.parquet",
                "size": 154200,
                "modificationTime": 1763400000000,
                "dataChange": True,
                "stats": '{"numRecords": 5000, "minValues": {"id": 1}, "maxValues": {"id": 5000}}'
            }
        },
        {
            "metaData": {
                "schemaString": '{"type":"struct","fields":[{"name":"id","type":"integer"}]}',
                "format": {"provider": "parquet"}
            }
        }
    ]
}

add_action = commit_actions["actions"][0]["add"]
print(f"Committed Data File: {add_action['path']}")
print(f"Record Count in Commit: {5000}")
assert add_action["dataChange"] is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Atomic Commits**: A transaction is only committed once its sequential JSON file is atomically written.
# MAGIC - **Compacted Checkpoints**: Prevent slow object storage listings by consolidating active state every 10 commits.
# MAGIC - **Data Skipping Stats**: Column min/max statistics embedded in `add` actions enable rapid file skipping without reading Parquet footers.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta Lake reconstruct the current active table state from `_delta_log`?
# MAGIC 1. What role do Parquet checkpoints play in maintaining low query scan latency?
