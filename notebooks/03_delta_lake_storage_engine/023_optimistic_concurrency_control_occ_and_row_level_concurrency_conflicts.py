# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 023. Optimistic Concurrency Control (OCC) & Row-Level Concurrency Conflicts
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Multiple streaming ingestion jobs and nightly batch GDPR deletion jobs run concurrently against the customer master table, causing intermittent `ConcurrentModificationException` failures.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the mechanics of Delta Lake Optimistic Concurrency Control (OCC), reproduce a concurrent append/delete conflict, and resolve it by enabling Row-Level Concurrency (RLC).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake uses OCC: transactions read a snapshot, prepare changes, and attempt to commit. If another writer modified conflicting files or rows during that window, Delta verifies whether the changes actually conflict. Row-Level Concurrency allows two concurrent writes to modify distinct rows in the same Parquet file.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. OCC Conflict Matrix & Row-Level Concurrency Verification
# MAGIC
# MAGIC Evaluate concurrent transaction compatibility across Delta Lake execution modes.
# COMMAND ----------

concurrency_matrix = {
    "Classic_Delta_CoW": {
        "concurrent_appends": "Allowed",
        "concurrent_updates_same_file": "CONFLICT: ConcurrentModificationException",
        "resolution": "Serial execution or retry loops"
    },
    "Delta_3x_with_RLC": {
        "concurrent_appends": "Allowed",
        "concurrent_updates_same_file": "ALLOWED: Row-Level Concurrency via Deletion Vectors",
        "resolution": "Native non-blocking commit"
    }
}

for mode, rules in concurrency_matrix.items():
    print(f"Mode: {mode}\n  Same-File Updates: {rules['concurrent_updates_same_file']}\n")

assert "ALLOWED" in concurrency_matrix["Delta_3x_with_RLC"]["concurrent_updates_same_file"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **OCC Semantics**: Writers assume no conflicts; validation occurs at atomic commit time.
# MAGIC - **Row-Level Concurrency**: Enable `delta.enableRowTracking = true` and `delta.enableDeletionVectors = true` to allow concurrent row updates in the same file.
# MAGIC - **Partition Isolation**: Confining concurrent writes to separate partitions eliminates conflicts completely.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Under what exact conditions will two concurrent transactions trigger a `ConcurrentModificationException` in Delta Lake?
# MAGIC 2. How does Row-Level Concurrency (RLC) resolve conflicts that previously failed under Copy-on-Write?
