# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 031. Delta Time Travel: Historical Point-in-Time Auditing, Rollbacks & Log Retention
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A developer accidentally executed an unconstrained `DELETE FROM prod_customers` in production. Operations must restore the table to the exact state prior to the disaster without data loss.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Audit historical versions with `DESCRIBE HISTORY`, reproduce an unconstrained `DELETE` disaster, query the intact prior snapshot using `VERSION AS OF`, and execute atomic disaster recovery using `RESTORE TABLE`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake preserves immutable historical Parquet snapshots across commits until `VACUUM` deletes expired files. `RESTORE TABLE` records a brand-new forward commit pointing back to the target version, keeping full audit lineage intact.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Commit Evolution, Disaster Reproduction & `DESCRIBE HISTORY`
# MAGIC
# MAGIC Build 3 committed versions (`v0` load, `v1` enrichment insert, `v2` accidental full-table `DELETE`) and inspect the commit audit trail.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_031_", dir=globals().get("HANDBOOK_TMP_DIR")))
cust_path = str(lab_dir / "silver_customers")

spark.sql(f"CREATE TABLE t031_customers (id LONG, segment STRING) USING DELTA LOCATION '{cust_path}'")
spark.range(0, 100).withColumn("segment", F.lit("CORE")).write.format("delta").mode("append").save(cust_path)
spark.range(100, 125).withColumn("segment", F.lit("VIP")).write.format("delta").mode("append").save(cust_path)

# Oops: unconstrained DELETE wipes the table at version 3!
spark.sql("DELETE FROM t031_customers")

post_disaster_count = spark.table("t031_customers").count()
history_df = spark.sql("DESCRIBE HISTORY t031_customers").select("version", "operation")
ops_by_ver = {r["version"]: r["operation"] for r in history_df.collect()}

print(f"Row count immediately after accidental DELETE: {post_disaster_count}")
print(f"Delta Audit Log versions: {ops_by_ver}")
assert post_disaster_count == 0
assert ops_by_ver[3] == "DELETE"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Point-in-Time Inspection (`VERSION AS OF`) & Atomic `RESTORE TABLE`
# MAGIC
# MAGIC Verify pre-disaster Version 2 holds all 125 customer records, restore atomically with `RESTORE TABLE t031_customers TO VERSION AS OF 2`, and verify Version 4 captures the `RESTORE` audit entry.
# COMMAND ----------

v2_count = spark.sql("SELECT * FROM t031_customers VERSION AS OF 2").count()
assert v2_count == 125

spark.sql("RESTORE TABLE t031_customers TO VERSION AS OF 2")

restored_count = spark.table("t031_customers").count()
latest_op = (
    spark.sql("DESCRIBE HISTORY t031_customers")
    .orderBy(F.col("version").desc())
    .select("version", "operation")
    .first()
)

print(f"Pre-disaster snapshot (v2) count: {v2_count}")
print(f"Restored live table count       : {restored_count}")
print(f"Latest audit entry              : version={latest_op['version']}, op={latest_op['operation']}")

assert restored_count == 125
assert latest_op["operation"] == "RESTORE"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Data Loss Rollback**: `RESTORE TABLE` instantaneously reverts bad writes via a metadata pointer update.
# MAGIC - **Forward-Only Auditability**: `RESTORE` appends a new version (`RESTORE`) rather than deleting history.
# MAGIC - **Retention Guardrails**: Configure `delta.deletedFileRetentionDuration` >= 7 days so Time Travel windows stay intact before `VACUUM`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta Lake execute a `TIMESTAMP AS OF` query under the hood?
# MAGIC 2. What happens if you run `RESTORE TABLE ... TO VERSION AS OF 2` after `VACUUM` has deleted the Parquet files from version 2?
