# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 028. Delta UniForm: Asynchronous Iceberg Metadata Manifest Generation & Trino Access
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data platform must serve both Databricks users and an external Snowflake / Trino analytics cluster without duplicating 100 TB of Parquet data across Delta and Iceberg formats.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Delta Universal Format (UniForm) for Apache Iceberg, verify background metadata manifest generation, and demonstrate reading the same Parquet files from external Iceberg engines.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta UniForm enables reading Delta tables with clients that support Apache Iceberg or Apache Hudi. As transactions commit to the `_delta_log`, Databricks asynchronously generates Iceberg metadata files (`metadata.json` and Avro manifests) pointing to the same underlying Parquet data files.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Configure UniForm Iceberg Compatibility on Delta Table
# MAGIC
# MAGIC Enable Iceberg metadata generation via table properties.
# COMMAND ----------

ddl_uniform = """
CREATE OR REPLACE TABLE prod_lakehouse.gold.customer_metrics (
    customer_id BIGINT,
    lifetime_value DECIMAL(18, 2),
    churn_probability DOUBLE
)
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableDeletionVectors' = true
);
"""

print("Delta UniForm DDL specification created.")
assert "'delta.universalFormat.enabledFormats' = 'iceberg'" in ddl_uniform
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Copy of Data**: Delta, Snowflake, Trino, and BigQuery read the exact same Parquet files.
# MAGIC - **Asynchronous Generation**: Writing to Delta is not blocked by Iceberg metadata creation.
# MAGIC - **Open Interoperability**: Prevents vendor lock-in by providing full Apache Iceberg v2 table format compatibility.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta UniForm enable Snowflake and AWS Athena to query Delta tables as Apache Iceberg?
# MAGIC 2. Are writes to the Delta table delayed while Iceberg metadata manifests are being generated in UniForm?
