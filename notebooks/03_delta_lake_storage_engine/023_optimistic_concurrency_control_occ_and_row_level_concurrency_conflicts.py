# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 023. Optimistic Concurrency Control (OCC) & Row-Level Concurrency Conflicts
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Multiple streaming ingestion jobs and nightly batch GDPR deletion jobs run concurrently against the customer master table, causing intermittent `ConcurrentModificationException` failures.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the mechanics of Delta Lake Optimistic Concurrency Control (OCC), reproduce a concurrent conflicting commit, resolve it via partition isolation and bounded retries, and inspect Row Tracking metadata.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake uses OCC: transactions read a snapshot, prepare changes, and attempt to commit. If another writer modified conflicting partitions or files during that window without Row-Level Concurrency (Deletion Vectors + Row Tracking), Delta raises `ConcurrentAppendException` / `ConcurrentModificationException`.
# COMMAND ----------

import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bad vs. Good: Reproduce Real OCC Conflicts vs. Disjoint Partition Isolation
# MAGIC
# MAGIC Trigger genuine concurrent `replaceWhere` commits against the same `region='US'` partition using a thread barrier (exposing `ConcurrentAppendException`), then contrast with disjoint `US` vs. `EU` partition writes.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_023_", dir=globals().get("HANDBOOK_TMP_DIR")))
occ_path = str(lab_dir / "occ_customers")

spark.createDataFrame(
    [(1, "US", "v0"), (2, "EU", "v0")], ["id", "region", "tag"]
).write.format("delta").partitionBy("region").save(occ_path)

# GOOD PATTERN: Concurrent appends/overwrites isolated to DISJOINT partitions ('US' vs 'EU')
def write_partition(region: str, rec_id: int, label: str) -> str:
    (
        spark.createDataFrame([(rec_id, region, label)], ["id", "region", "tag"])
        .write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"region = '{region}'")
        .save(occ_path)
    )
    return region

with ThreadPoolExecutor(max_workers=2) as pool:
    results = [
        f.result()
        for f in [
            pool.submit(write_partition, "US", 10, "isolated"),
            pool.submit(write_partition, "EU", 20, "isolated"),
        ]
    ]

print(f"Disjoint partition writes committed cleanly: {results}")
assert spark.read.format("delta").load(occ_path).count() == 2

# BAD PATTERN: Multiple unsynchronized writers overwrite the SAME partition concurrently
conflicts_seen = 0
for wave in range(3):
    barrier = threading.Barrier(4)

    def colliding_write(idx: int) -> None:
        barrier.wait()
        (
            spark.createDataFrame([(100 + idx, "US", f"wave_{wave}_{idx}")], ["id", "region", "tag"])
            .write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", "region = 'US'")
            .save(occ_path)
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        for fut in [pool.submit(colliding_write, i) for i in range(4)]:
            try:
                fut.result()
            except Exception as exc:
                if "Concurrent" in type(exc).__name__ or "DELTA_CONCURRENT" in str(exc):
                    conflicts_seen += 1
    if conflicts_seen > 0:
        break

print(f"Real OCC conflict exceptions observed on shared partition: {conflicts_seen}")
assert conflicts_seen >= 1, "Expected at least one real Delta ConcurrentAppendException!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Production Resolution: OCC Retry Wrapper & Row Tracking Preparation
# MAGIC
# MAGIC Wrap conflicting updates with bounded jittered retries so parallel writers converge cleanly, and enable `delta.enableRowTracking` + `delta.enableDeletionVectors` to inspect stable `_metadata.row_id` tracking.
# COMMAND ----------

# Bounded retry pattern for transient OCC conflicts
def write_partition_with_retry(rec_id: int, max_attempts: int = 6) -> int:
    for attempt in range(1, max_attempts + 1):
        try:
            (
                spark.createDataFrame([(rec_id, "APAC", f"ok_{attempt}")], ["id", "region", "tag"])
                .write.format("delta")
                .mode("append")
                .save(occ_path)
            )
            return attempt
        except Exception as exc:
            if "Concurrent" not in type(exc).__name__ and "DELTA_CONCURRENT" not in str(exc):
                raise
            if attempt == max_attempts:
                raise
            time.sleep(0.05 * attempt)
    return max_attempts

with ThreadPoolExecutor(max_workers=3) as pool:
    attempts = [f.result() for f in [pool.submit(write_partition_with_retry, 300 + i) for i in range(3)]]

apac_count = spark.read.format("delta").load(occ_path).filter("region = 'APAC'").count()
print(f"APAC concurrent writes committed via retry loop; attempts={attempts}, apac_rows={apac_count}")
assert apac_count == 3

# Enable Row Tracking + Deletion Vectors for Delta 3.x fine-grained row lineage
rt_path = str(lab_dir / "rlc_orders")
spark.sql(f"""
    CREATE TABLE t023_rlc (order_id INT, status STRING) USING DELTA
    LOCATION '{rt_path}'
    TBLPROPERTIES (
        'delta.enableDeletionVectors' = 'true',
        'delta.enableRowTracking' = 'true'
    )
""")
spark.sql("INSERT INTO t023_rlc VALUES (1, 'PENDING'), (2, 'PAID')")
tracked_df = spark.sql(
    "SELECT order_id, _metadata.row_id AS row_id, _metadata.row_commit_version AS commit_ver FROM t023_rlc ORDER BY order_id"
)
row_ids = [r["row_id"] for r in tracked_df.collect()]
print(f"Assigned stable Delta Row IDs: {row_ids}")
assert len(set(row_ids)) == 2
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **OCC Semantics**: Writers assume no conflicts; validation happens atomically at commit time.
# MAGIC - **Row-Level Concurrency**: Enable `delta.enableRowTracking = true` and `delta.enableDeletionVectors = true` to avoid file-level conflicts on row updates.
# MAGIC - **Partition Isolation & Retries**: Isolating writes by partition eliminates conflicts structurally, while bounded OCC retries absorb transient overlaps.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Under what exact conditions will two concurrent transactions trigger a `ConcurrentModificationException` in Delta Lake?
# MAGIC 2. How does Row-Level Concurrency (RLC) resolve conflicts that previously failed under Copy-on-Write?
