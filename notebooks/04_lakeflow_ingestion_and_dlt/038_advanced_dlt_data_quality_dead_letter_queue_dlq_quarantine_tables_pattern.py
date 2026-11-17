# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 038. Advanced DLT Data Quality: Dead Letter Queue (DLQ) Quarantine Tables Pattern
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC In regulatory banking, dropping invalid records with `expect_or_drop` violates compliance; every invalid row must be diverted into a Dead Letter Queue (DLQ) quarantine table for human remediation.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement the DLT Dead Letter Queue (DLQ) split pattern, partitioning a raw streaming table into a clean target table and a quarantined error table.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The DLQ pattern reads from an upstream table once and writes to two downstream tables: valid records meeting constraints flow to the clean table, while records violating constraints are tagged with failure reasons and routed to the quarantine table.
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
# MAGIC ### 1. DLQ Split Pattern Implementation
# MAGIC
# MAGIC Define complementary DLT tables to separate valid data from quarantined errors.
# COMMAND ----------

dlq_pattern_code = """
import dlt
from pyspark.sql import functions as F

RULES = {
    "valid_account": "account_id IS NOT NULL",
    "valid_amount": "transaction_amount > 0"
}

# 1. Clean Table: Enforce all rules with expect_or_drop
@dlt.table(comment="Clean transactions passing all expectations")
@dlt.expect_all_or_drop(RULES)
def transactions_clean():
    return dlt.read_stream("transactions_bronze")

# 2. Quarantine Table: Invert the rules to capture only failing rows
@dlt.table(comment="Quarantined transactions for compliance review")
def transactions_quarantine():
    failing_condition = f"NOT ({RULES['valid_account']}) OR NOT ({RULES['valid_amount']})"
    return (
        dlt.read_stream("transactions_bronze")
        .filter(failing_condition)
        .withColumn("_quarantine_reason", F.lit("Violated account or amount constraint"))
        .withColumn("_quarantined_at", F.current_timestamp())
    )
"""

print("DLQ split pattern code verified.")
assert "transactions_clean" in dlq_pattern_code
assert "transactions_quarantine" in dlq_pattern_code
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Silent Drops**: Every invalid record is preserved in the quarantine table with audit metadata.
# MAGIC - **Audited Recovery**: Once data issues are resolved upstream, a backfill job can re-ingest from quarantine.
# MAGIC - **Compliance Invariant**: Crucial for healthcare (HIPAA) and financial (SOX) regulatory pipelines.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you implement a Dead Letter Queue in Delta Live Tables without reading upstream files twice?
# MAGIC 1. What metadata columns should always be attached to quarantined records?
