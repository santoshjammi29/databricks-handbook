# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 029. Shallow Clones vs. Deep Clones: Zero-Copy Sandboxes, Testing & Disaster Recovery
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data science team needs a sandbox copy of a 10 TB production dataset to test experimental machine learning models. Duplicating 10 TB of data would take hours and cost thousands in cloud storage.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement and compare Shallow Clones and Deep Clones in Delta Lake. Demonstrate that a Shallow Clone creates an instant, zero-copy pointer table, while a Deep Clone creates a fully independent replica for disaster recovery.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC A Shallow Clone copies only transaction log metadata, referencing the original Parquet files in place. It is created instantaneously regardless of table size. A Deep Clone copies both metadata and physical Parquet files, creating a fully decoupled duplicate.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Clone Mechanics & Cost Comparison
# MAGIC
# MAGIC Benchmark clone creation time, storage overhead, and mutation independence.
# COMMAND ----------

clone_comparison = {
    "Shallow_Clone": {
        "command": "CREATE TABLE dev.sandbox.orders SHALLOW CLONE prod.silver.orders;",
        "creation_time": "1 to 3 seconds (metadata only)",
        "storage_cost": "0 bytes additional storage initially (copy-on-write on mutation)",
        "use_case": "Dev/test sandboxes, ML feature experimentation, staging validation"
    },
    "Deep_Clone": {
        "command": "CREATE TABLE dr.backup.orders DEEP CLONE prod.silver.orders;",
        "creation_time": "Hours (copies 100% of underlying Parquet files)",
        "storage_cost": "Full duplicate storage cost (e.g. 10 TB = 10 TB)",
        "use_case": "Disaster recovery, cross-region migration, regulatory immutable archives"
    }
}

for clone_type, props in clone_comparison.items():
    print(f"[{clone_type}]\n  Command: {props['command']}\n  Time: {props['creation_time']}\n")

assert "SHALLOW CLONE" in clone_comparison["Shallow_Clone"]["command"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Instant Sandboxes**: Shallow clones instantiate in seconds, making them ideal for QA testing and ML modeling.
# MAGIC - **Isolation Guaranteed**: Changes made to a shallow clone never propagate back to the parent table.
# MAGIC - **Disaster Recovery**: Deep clones provide complete physical decoupling across cloud storage accounts and regions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What happens to a Shallow Clone if someone runs `VACUUM` on the source parent table?
# MAGIC 2. Can you clone a specific historical version of a Delta table using Time Travel syntax?
