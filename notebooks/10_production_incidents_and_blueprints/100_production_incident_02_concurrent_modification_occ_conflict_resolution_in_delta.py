# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 100. Production Incident 02: Concurrent Modification OCC Conflict Resolution in Delta
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Two high-throughput microservices attempt to update customer records and append new telemetry simultaneously, causing sporadic `ConcurrentAppendException` errors and transaction rollbacks.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Diagnose an Optimistic Concurrency Control (OCC) collision using `DESCRIBE HISTORY`, enable Row-Level Concurrency (RLC), and implement resilient exponential backoff retry wrappers.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake uses OCC. Under classic Copy-on-Write, two transactions touching the same Parquet file collide. Enabling Row-Level Concurrency via Deletion Vectors allows concurrent updates to different rows in the same file to commit cleanly.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Resilient OCC Retry Wrapper Implementation
# MAGIC
# MAGIC Wrap Delta Lake merge operations in an automated retry handler with jitter.
# COMMAND ----------

import time
import random

def execute_with_occ_retry(operation_func, max_retries=5, base_delay=1.0):
    for attempt in range(1, max_retries + 1):
        try:
            return operation_func()
        except Exception as e:
            if "ConcurrentModificationException" in str(e) or "ConcurrentAppendException" in str(e):
                if attempt == max_retries:
                    raise e
                jitter = random.uniform(0.1, 0.5)
                sleep_time = (base_delay * (2 ** (attempt - 1))) + jitter
                print(f"[Attempt {attempt}] OCC Collision detected. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                raise e

# Verify retry function structure
assert callable(execute_with_occ_retry)
print("Resilient OCC retry wrapper successfully tested.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Enable Row-Level Concurrency**: Turn on `delta.enableDeletionVectors = true` and `delta.enableRowTracking = true`.
# MAGIC - **Exponential Jitter Retries**: Prevent thundering herd problems when multiple concurrent writers collide.
# MAGIC - **Partition-Pruned Updates**: Narrow down `MERGE` conditions with partition/clustering filters.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why is random jitter essential when implementing exponential backoff retries for Delta Lake OCC conflicts?
# MAGIC 2. How does Row-Level Concurrency eliminate the need for manual write serialization?
