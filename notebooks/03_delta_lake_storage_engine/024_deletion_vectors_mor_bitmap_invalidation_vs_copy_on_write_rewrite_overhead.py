# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 024. Deletion Vectors (MoR): Bitmap Invalidation vs. Copy-on-Write Rewrite Overhead
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A high-churn customer loyalty table processes 50,000 updates per hour. Under traditional Copy-on-Write, each update rewrote 200 MB files, resulting in 10 TB of disk writes per day and severe write amplification.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Deletion Vectors on a Delta table, execute point updates and deletes, measure write amplification reduction, and physically purge invalid rows using `REORG TABLE ... APPLY (PURGE)`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Deletion Vectors (DVs) convert Delta Lake DML from Copy-on-Write (CoW) to Merge-on-Read (MoR). In MoR, deleted rows are recorded in a lightweight roaring bitmap (`.dv` file) without touching the original Parquet data file. The physical data is rewritten only during scheduled compaction.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Write Amplification Benchmarking: CoW vs. MoR
# MAGIC
# MAGIC Compare physical storage write volume between Copy-on-Write and Deletion Vectors.
# COMMAND ----------

def calculate_write_amplification(target_file_size_mb: int, modified_rows_bytes: int, mode: str) -> dict:
    if mode == "CoW":
        bytes_written = target_file_size_mb * 1024 * 1024 # Rewrites entire file
        amplification_factor = bytes_written / modified_rows_bytes
    else: # MoR with Deletion Vectors
        bytes_written = modified_rows_bytes + 4096 # Only modified rows + 4KB roaring bitmap
        amplification_factor = bytes_written / modified_rows_bytes
    return {"bytes_written": bytes_written, "amplification": amplification_factor}

cow_result = calculate_write_amplification(256, 1024, "CoW")
mor_result = calculate_write_amplification(256, 1024, "MoR")

print(f"Copy-on-Write Written: {cow_result['bytes_written'] / (1024*1024):.1f} MB (Amplification: {cow_result['amplification']:.0f}x)")
print(f"Merge-on-Read Written: {mor_result['bytes_written'] / 1024:.1f} KB (Amplification: {mor_result['amplification']:.2f}x)")

assert cow_result["bytes_written"] > mor_result["bytes_written"] * 1000
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Massive Write Acceleration**: DML write latency drops from minutes to sub-seconds.
# MAGIC - **Zero File Rewriting**: Unchanged rows remain untouched until scheduled `OPTIMIZE`.
# MAGIC - **GDPR Compliance**: Run `REORG TABLE my_table APPLY (PURGE)` to permanently purge tombstoned rows.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Deletion Vectors work at the read engine level in Photon and Apache Spark?
# MAGIC 2. When should you run `REORG TABLE ... APPLY (PURGE)` on a table with Deletion Vectors enabled?
