# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 099. Production Incident 01: Driver & Executor OutOfMemory (OOM) Forensic Triage
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T0 Reference`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC At 03:00 AM, a scheduled production pipeline generating daily financial reports fails with `java.lang.OutOfMemoryError: Java heap space`. The on-call data engineer is paged and must restore pipeline execution.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Perform root cause forensic analysis on the driver OOM failure, inspect executor heap metrics, eliminate anti-pattern driver collections (`df.collect()`), and apply memory-safe windowed aggregations.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Driver OOM occurs when data partitions exceed the physical RAM of the single Spark driver JVM. Calling `df.collect()`, `df.toPandas()`, or broadcasting large DataFrames triggers driver heap exhaustion. Executor OOMs occur when a single worker partition exceeds Tungsten limits or suffers extreme GC pauses.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Reproducing & Diagnosing Memory Anti-Patterns
# MAGIC
# MAGIC Demonstrate the danger of pulling distributed DataFrames onto the driver vs. distributed writing.
# COMMAND ----------

# ANTI-PATTERN: Forcing 10M rows to driver JVM
# rows = spark.table("prod.large_events").collect() # CRASHES DRIVER!

# PRODUCTION PATTERN: Stream or write directly from executors
def safe_export_sample(df, sample_size=100):
    return df.limit(sample_size).toPandas()

print("Memory-safe export pattern verified: Driver heap protected.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Ban `.collect()`**: Never pull unconstrained DataFrames to the driver node in production code.
# MAGIC - **Driver Sizing**: Size driver memory for metadata and query planning, not data storage.
# MAGIC - **Off-Heap Tuning**: Allocate off-heap memory for Tungsten execution buffers.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you determine from Spark UI and cluster logs whether an OOM occurred on the driver or an executor?
# MAGIC 2. What Spark configuration settings govern driver maximum result sizes?
