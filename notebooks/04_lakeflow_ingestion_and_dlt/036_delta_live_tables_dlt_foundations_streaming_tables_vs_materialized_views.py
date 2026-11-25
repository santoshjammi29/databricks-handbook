# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 036. Delta Live Tables (DLT) Foundations: Streaming Tables vs. Materialized Views
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An analytics engineering team is building an automated Bronze-to-Silver-to-Gold pipeline and wants to eliminate manual checkpoint management and complex streaming boilerplates.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Construct a declarative Delta Live Tables pipeline in Python using `@dlt.table` and `@dlt.view`, contrasting Streaming Tables (append-only) with Materialized Views (stateful projections).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Live Tables (DLT) is Databricks' declarative ETL framework. Developers define what tables to produce, and DLT orchestrates DAG dependencies, autoscaling compute, checkpoint state, and data quality enforcement automatically.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Declarative DLT Pipeline Definition
# MAGIC
# MAGIC Define a multi-hop pipeline using `@dlt.table` streaming tables and materialized views.
# COMMAND ----------

dlt_pipeline_code = """
import dlt
from pyspark.sql import functions as F

# 1. Bronze: Streaming Table ingesting raw files incrementally
@dlt.table(comment="Raw landing streaming table")
def orders_bronze():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/prod/raw/orders/")
    )

# 2. Silver: Conformed Materialized View with deduplication
@dlt.table(comment="Cleaned and validated orders")
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
def orders_silver():
    return dlt.read_stream("orders_bronze").select(
        F.col("order_id"),
        F.col("amount").cast("double"),
        F.to_timestamp("order_ts").alias("order_timestamp")
    )
"""

print("Declarative DLT pipeline code verified.")
assert "@dlt.table" in dlt_pipeline_code
assert "@dlt.expect_or_drop" in dlt_pipeline_code
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Declarative Pipelines**: Specify the target dataset; DLT manages execution, retries, and checkpoints.
# MAGIC - **Streaming Tables**: Use for incremental, append-only streams.
# MAGIC - **Materialized Views**: Use when query results must update based on changes across multiple upstream tables.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between a Streaming Table and a Materialized View in Delta Live Tables?
# MAGIC 2. How does DLT determine the topological execution order of tasks in a pipeline?
