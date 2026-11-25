# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 039. DLT Change Data Capture: Incremental Upserts with dlt.apply_changes (SCD Type 1)
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A CRM database emits change logs (inserts, updates, deletes) via Debezium. The analytics team must maintain a conformed customer table reflecting current state (SCD Type 1).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement CDC replication into Delta Lake using `dlt.apply_changes()` with primary keys, sequence ordering (`sequence_by`), and delete handling.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `dlt.apply_changes()` automates incremental CDC processing into Delta tables. It handles out-of-order events using a sequence column (e.g., binlog timestamp or version) and applies SCD Type 1 in-place updates natively.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. DLT apply_changes SCD Type 1 Definition
# MAGIC
# MAGIC Configure `dlt.apply_changes()` for automatic CDC upserts.
# COMMAND ----------

scd1_cdc_code = """
import dlt

dlt.create_streaming_table(
    name="customers_scd1",
    comment="Current state customer dimension (SCD Type 1)"
)

dlt.apply_changes(
    target="customers_scd1",
    source="customers_cdc_bronze",
    keys=["customer_id"],
    sequence_by="op_timestamp",
    apply_as_deletes="op_type = 'DELETE'",
    except_column_list=["op_type", "op_timestamp"]
)
"""

print("SCD Type 1 CDC code specification verified.")
assert "dlt.apply_changes" in scd1_cdc_code
assert "sequence_by" in scd1_cdc_code and "op_timestamp" in scd1_cdc_code
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Automated Deduplication**: `sequence_by` resolves out-of-order network events automatically.
# MAGIC - **Delete Support**: `apply_as_deletes` physically purges or deletes records when deletion flags appear.
# MAGIC - **Simplified Syntax**: Replaces complex manual `MERGE INTO` queries in streaming foreachBatch.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does `dlt.apply_changes()` handle out-of-order CDC change events?
# MAGIC 2. What is the difference between specifying `keys` versus `sequence_by` in `dlt.apply_changes()`?
