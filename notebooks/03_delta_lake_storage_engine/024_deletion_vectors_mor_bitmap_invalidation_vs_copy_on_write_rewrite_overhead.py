# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 024. Deletion Vectors (MoR): Bitmap Invalidation vs. Copy-on-Write Rewrite Overhead
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A high-churn customer loyalty table processes 50,000 updates per hour. Under traditional Copy-on-Write, each update rewrote 200 MB files, resulting in 10 TB of disk writes per day and severe write amplification.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Deletion Vectors on a Delta table, execute point deletes, measure Copy-on-Write vs. Merge-on-Read Parquet write amplification from `_delta_log`, and physically purge invalid rows using `REORG TABLE ... APPLY (PURGE)`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Deletion Vectors (DVs) convert Delta Lake DML from Copy-on-Write (CoW) to Merge-on-Read (MoR). In MoR, deleted rows are recorded in a lightweight roaring bitmap (`.bin` Deletion Vector file) without rewriting the Parquet data file until `OPTIMIZE` or `REORG TABLE ... APPLY (PURGE)`.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Bad (Copy-on-Write) vs. Good (Merge-on-Read Deletion Vectors)
# MAGIC
# MAGIC Create two identical 10,000-row Delta tables (2 Parquet files each)—one with Deletion Vectors disabled and one enabled—then execute an identical 1% DELETE and inspect `_delta_log/000001.json`.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_024_", dir=globals().get("HANDBOOK_TMP_DIR")))
cow_path = str(lab_dir / "cow_loyalty")
dv_path = str(lab_dir / "dv_loyalty")

spark.sql(f"""
    CREATE TABLE t024_cow (id LONG, bucket INT, payload STRING) USING DELTA
    LOCATION '{cow_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'false')
""")
spark.sql(f"""
    CREATE TABLE t024_dv (id LONG, bucket INT, payload STRING) USING DELTA
    LOCATION '{dv_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true')
""")

base_df = (
    spark.range(0, 10000)
    .withColumn("bucket", (F.col("id") % 2).cast("int"))
    .withColumn("payload", F.concat(F.lit("loyalty_member_profile_"), F.col("id").cast("string")))
    .coalesce(2)
)
base_df.write.format("delta").mode("append").save(cow_path)
base_df.write.format("delta").mode("append").save(dv_path)

# Delete only 100 rows (1% of dataset) from both tables
spark.sql("DELETE FROM t024_cow WHERE id % 100 = 0")
spark.sql("DELETE FROM t024_dv WHERE id % 100 = 0")

def inspect_delete_commit(table_root: Path) -> tuple[int, int, int]:
    v2_actions = [
        json.loads(line)
        for line in (table_root / "_delta_log" / "00000000000000000002.json").read_text().splitlines()
    ]
    rewritten_bytes = 0
    new_parquet_files = 0
    dv_bitmaps = 0
    for act in v2_actions:
        if "add" in act:
            add_act = act["add"]
            if add_act.get("deletionVector"):
                dv_bitmaps += 1
            else:
                new_parquet_files += 1
                rewritten_bytes += int(add_act["size"])
    return new_parquet_files, dv_bitmaps, rewritten_bytes

cow_new_pq, cow_dvs, cow_bytes = inspect_delete_commit(Path(cow_path))
dv_new_pq, dv_dvs, dv_bytes = inspect_delete_commit(Path(dv_path))

print(f"Copy-on-Write : rewrote {cow_new_pq} Parquet files ({cow_bytes:,} bytes), DVs={cow_dvs}")
print(f"Merge-on-Read : rewrote {dv_new_pq} Parquet files ({dv_bytes:,} bytes), DVs={dv_dvs}")

assert cow_new_pq >= 1 and cow_bytes > 0 and cow_dvs == 0
assert dv_new_pq == 0 and dv_bytes == 0 and dv_dvs >= 1
assert spark.table("t024_dv").count() == spark.table("t024_cow").count() == 9900
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Physical GDPR Row Purge with `REORG TABLE ... APPLY (PURGE)`
# MAGIC
# MAGIC Reclaim storage and physically remove masked-out rows from Parquet files using `REORG TABLE ... APPLY (PURGE)` while keeping logical row counts invariant.
# COMMAND ----------

dv_bin_before = list(Path(dv_path).glob("*.bin"))
spark.sql("REORG TABLE t024_dv APPLY (PURGE)")

remaining_dv_actions = 0
latest_log = sorted((Path(dv_path) / "_delta_log").glob("*.json"))[-1]
for line in latest_log.read_text(encoding="utf-8").splitlines():
    act = json.loads(line)
    if "add" in act and act["add"].get("deletionVector"):
        remaining_dv_actions += 1

final_dv_count = spark.table("t024_dv").count()
print(f"DV bitmap files created on DELETE : {len(dv_bin_before)}")
print(f"DV annotations after REORG PURGE  : {remaining_dv_actions}")
print(f"Final logical row count preserved : {final_dv_count}")

assert len(dv_bin_before) >= 1
assert remaining_dv_actions == 0
assert final_dv_count == 9900
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Parquet Rewrites on DML**: Deletion Vectors write lightweight `.bin` roaring bitmaps instead of rewriting multi-hundred-MB Parquet files.
# MAGIC - **Logical Consistency**: Spark SQL transparently filters masked row offsets on read with exact CoW equivalence.
# MAGIC - **GDPR Compliance**: Run `REORG TABLE my_table APPLY (PURGE)` to physically rewrite touched files and remove tombstoned data.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Deletion Vectors work at the read engine level in Photon and Apache Spark?
# MAGIC 2. When should you run `REORG TABLE ... APPLY (PURGE)` on a table with Deletion Vectors enabled?
