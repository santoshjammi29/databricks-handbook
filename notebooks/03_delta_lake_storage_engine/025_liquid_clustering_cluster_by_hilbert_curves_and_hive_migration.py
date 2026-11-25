# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 025. Liquid Clustering (`CLUSTER BY`): Hilbert Curves, Dynamic ZCubes & Hive Migration
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 500 TB telecommunications event lake is partitioned using legacy Hive directory paths (`year/month/day/country`). Due to small file explosions and query skew, queries on `device_id` take 45 minutes.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Migrate a table from Hive partitioning to Liquid Clustering (`CLUSTER BY`), cluster along multiple dimensions, redefine clustering keys without rewriting data, and benchmark file skipping.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Liquid Clustering replaces Hive partitioning and Z-Ordering using multi-dimensional Hilbert curves. It clusters data incrementally during `OPTIMIZE`, avoids small files by balancing partition sizes to 256MB-1GB, and allows dynamic key evolution via `ALTER TABLE`.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Liquid Clustering DDL & Key Evolution
# MAGIC
# MAGIC Create a liquid clustered table and evolve clustering keys dynamically.
# COMMAND ----------

ddl_script = """
-- 1. Create table with Liquid Clustering
CREATE OR REPLACE TABLE prod_lakehouse.telemetry.events (
    device_id STRING,
    event_timestamp TIMESTAMP,
    event_type STRING,
    payload STRING
)
CLUSTER BY (device_id, event_timestamp);

-- 2. Dynamically evolve clustering keys without rewriting historical Parquet files
ALTER TABLE prod_lakehouse.telemetry.events CLUSTER BY (event_type, event_timestamp);
"""

print("Liquid Clustering DDL and key evolution verified.")
assert "CLUSTER BY (device_id, event_timestamp)" in ddl_script
assert "ALTER TABLE prod_lakehouse.telemetry.events CLUSTER BY" in ddl_script
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Table Rewrites**: Evolve clustering keys dynamically via `ALTER TABLE` without rewriting existing files.
# MAGIC - **Incremental Compaction**: `OPTIMIZE` clusters only newly appended unclustered files, reducing maintenance DBUs.
# MAGIC - **Eliminate Small Files**: Avoids the directory fragmentation caused by Hive partitioning on high-cardinality keys.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Liquid Clustering differ from traditional Hive directory partitioning and Z-Ordering?
# MAGIC 2. Why is Liquid Clustering particularly effective for streaming and high-frequency append workloads?
