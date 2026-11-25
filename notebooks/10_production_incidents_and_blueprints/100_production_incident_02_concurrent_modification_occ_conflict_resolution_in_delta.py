# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 100. Production Incident 02: Concurrent Modification OCC Conflict Resolution in Delta
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Two high-throughput microservices attempt to update customer records and append new telemetry simultaneously, causing sporadic `ConcurrentAppendException` errors and transaction rollbacks.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute our jittered exponential-backoff OCC retry wrapper against concurrent Delta writers (`ThreadPoolExecutor`), recover cleanly from snapshot conflicts, and verify Deletion Vectors + Row Tracking enablement.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake validates overlapping partition commits atomically. Adding jittered exponential retries (`execute_with_occ_retry`) absorbs transient OCC collisions while `delta.enableDeletionVectors` and `delta.enableRowTracking` isolate file-level concurrency conflicts.
# COMMAND ----------

import random
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Live OCC Conflict Storm Recovery with Jittered Exponential Retry Wrapper
# MAGIC
# MAGIC Launch concurrent `replaceWhere` commits on the same partition wrapped in `execute_with_occ_retry`, assert 100% commit success, and enable Row Tracking + Deletion Vectors on the target table.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_100_", dir=globals().get("HANDBOOK_TMP_DIR")))
occ_path = str(lab_dir / "cust_occ_delta")

spark.sql(f"""
    CREATE TABLE t100_cust (customer_id BIGINT, region STRING, state STRING) USING DELTA
    PARTITIONED BY (region)
    LOCATION '{occ_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true', 'delta.enableRowTracking' = 'true')
""")
spark.sql("INSERT INTO t100_cust VALUES (1, 'US', 'init')")

def execute_with_occ_retry(operation_func, max_retries: int = 8, base_delay: float = 0.03):
    for attempt in range(1, max_retries + 1):
        try:
            return operation_func()
        except Exception as exc:
            msg = f"{type(exc).__name__} {exc}"
            if "Concurrent" in msg or "DELTA_CONCURRENT" in msg:
                if attempt == max_retries:
                    raise
                time.sleep((base_delay * (2 ** min(attempt - 1, 4))) + random.uniform(0.01, 0.05))
            else:
                raise

barrier = threading.Barrier(4)

def resilient_worker(worker_id: int) -> str:
    barrier.wait()
    def _write():
        (
            spark.createDataFrame([(100 + worker_id, "US", f"worker_{worker_id}")], ["customer_id", "region", "state"])
            .write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", "region = 'US'")
            .save(occ_path)
        )
        return f"worker_{worker_id}"
    return execute_with_occ_retry(_write)

with ThreadPoolExecutor(max_workers=4) as pool:
    committed = [f.result() for f in [pool.submit(resilient_worker, i) for i in range(4)]]

props = dict(spark.sql("SHOW TBLPROPERTIES t100_cust").collect())
final_count = spark.table("t100_cust").count()
print(f"All {len(committed)} concurrent writers succeeded cleanly; rows={final_count}")
assert len(committed) == 4 and final_count == 1
assert props.get("delta.enableDeletionVectors") == "true" and props.get("delta.enableRowTracking") == "true"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Enable Row-Level Concurrency**: Turn on `delta.enableDeletionVectors = true` and `delta.enableRowTracking = true`.
# MAGIC - **Exponential Jitter Retries**: Random jitter prevents thundering-herd retries on colliding transactions.
# MAGIC - **Partition-Pruned Updates**: Narrow `MERGE` / `replaceWhere` scopes down to disjoint partitions whenever possible.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why is random jitter essential when implementing exponential backoff retries for Delta Lake OCC conflicts?
# MAGIC 2. How does Row-Level Concurrency eliminate the need for manual write serialization?
