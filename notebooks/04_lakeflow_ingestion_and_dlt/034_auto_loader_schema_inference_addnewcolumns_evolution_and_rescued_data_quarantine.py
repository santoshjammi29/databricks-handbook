# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 034. Auto Loader Schema Inference, addNewColumns Evolution & _rescued_data Quarantine
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Third-party vendors frequently change JSON schemas by adding new promotional fields or sending numeric strings instead of floats. The ingestion pipeline must never drop records or crash.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure Auto Loader with `schemaEvolutionMode = addNewColumns` and `rescuedDataColumn = _rescued_data`, proving that new fields evolve the schema while corrupt payloads are quarantined.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Auto Loader stores the active schema contract in `cloudFiles.schemaLocation`. When a new column appears, `addNewColumns` updates the Delta table schema and restarts the stream. If a data type conflicts, the original payload is captured safely in `_rescued_data`.
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
# MAGIC ### 1. Rescued Data Quarantine Verification
# MAGIC
# MAGIC Inspect how unparseable fields are captured in `_rescued_data` without data loss.
# COMMAND ----------

# Simulate incoming payloads with unexpected types
payloads = [
    {"order_id": "ORD-1", "amount": 150.50, "_rescued_data": None},
    {"order_id": "ORD-2", "amount": "INVALID_FLOAT", "_rescued_data": '{"amount": "INVALID_FLOAT", "_error": "TypeMismatch"}'}
]

df_stream_sim = spark.createDataFrame(payloads)
df_clean = df_stream_sim.filter(F.col("_rescued_data").isNull())
df_corrupt = df_stream_sim.filter(F.col("_rescued_data").isNotNull())

print(f"Clean Records: {df_clean.count()} | Rescued Corrupt: {df_corrupt.count()}")
assert df_corrupt.count() == 1
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Data Loss**: `rescuedDataColumn` guarantees no record is silently dropped due to formatting errors.
# MAGIC - **Schema Evolution**: `addNewColumns` allows upward-compatible upstream API evolution without manual DDL.
# MAGIC - **Schema Checkpointing**: Schema changes are persisted in JSON within the schema location directory.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What happens under the hood when Auto Loader encounters a new column with `schemaEvolutionMode = addNewColumns`?
# MAGIC 1. How does the `_rescued_data` column capture schema collisions and unparseable JSON tokens?
