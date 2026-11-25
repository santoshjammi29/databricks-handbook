# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 026. Delta Change Data Feed (CDF): Batch & Streaming Micro-Batch Deduplicated Merges
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A downstream data mart must consume only changes (inserts, updates, deletes) from the upstream customer master table. Re-scanning the 500M row table daily is cost-prohibitive.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Enable Delta Change Data Feed (`delta.enableChangeDataFeed = true`), execute multiple upstream mutations (`INSERT`, `UPDATE`, `DELETE`), filter out `update_preimage`, deduplicate multiple changes per key by `_commit_version DESC`, and merge into Gold.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC When CDF is enabled, Delta Lake records row-level change events across DML commits. Reading with `.option('readChangeFeed', 'true')` exposes `_change_type` (`insert`, `update_preimage`, `update_postimage`, `delete`), `_commit_version`, and `_commit_timestamp`.
# COMMAND ----------

import tempfile
from pathlib import Path
from delta.tables import DeltaTable
from pyspark.sql import Window, functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Enable CDF & Emit Multi-Version Inserts, Updates & Deletes
# MAGIC
# MAGIC Create a CDF-enabled Silver customer table, apply two consecutive updates to the same customer key plus an insert and a delete, and inspect the raw change feed stream.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_026_", dir=globals().get("HANDBOOK_TMP_DIR")))
silver_path = str(lab_dir / "silver_customers")
gold_path = str(lab_dir / "gold_customers")

spark.sql(f"""
    CREATE TABLE t026_silver (customer_id INT, email STRING, tier STRING) USING DELTA
    LOCATION '{silver_path}'
    TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")

# Initial baseline (v1) + mirror baseline to Gold
spark.sql("INSERT INTO t026_silver VALUES (101, 'a@v1.com', 'BASIC'), (102, 'b@v1.com', 'PRO'), (103, 'c@v1.com', 'BASIC')")
spark.read.format("delta").load(silver_path).write.format("delta").save(gold_path)

# Incremental Silver mutations after baseline:
# v2: update 101 twice across versions to test deduplication, delete 103, insert 104
spark.sql("UPDATE t026_silver SET email = 'a@v2.com' WHERE customer_id = 101")
spark.sql("UPDATE t026_silver SET email = 'a@final.com', tier = 'ENTERPRISE' WHERE customer_id = 101")
spark.sql("DELETE FROM t026_silver WHERE customer_id = 103")
spark.sql("INSERT INTO t026_silver VALUES (104, 'd@new.com', 'PRO')")

cdf_raw = (
    spark.read.format("delta")
    .option("readChangeFeed", "true")
    .option("startingVersion", 2)
    .load(silver_path)
)
change_types = {r["_change_type"] for r in cdf_raw.select("_change_type").distinct().collect()}
print(f"Captured CDF change types: {sorted(change_types)}")
assert {"insert", "update_preimage", "update_postimage", "delete"} <= change_types
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Filter `update_preimage`, Deduplicate by Version & Execute Delta MERGE
# MAGIC
# MAGIC Prevent non-deterministic merge conflicts by discarding `update_preimage` rows, ranking per `customer_id` by `_commit_version DESC`, merging into Gold, and verifying exact table parity.
# COMMAND ----------

latest_window = Window.partitionBy("customer_id").orderBy(F.col("_commit_version").desc())
net_changes = (
    cdf_raw.filter(F.col("_change_type") != "update_preimage")
    .withColumn("_rn", F.row_number().over(latest_window))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

DeltaTable.forPath(spark, gold_path).alias("t").merge(
    net_changes.alias("s"), "t.customer_id = s.customer_id"
).whenMatchedDelete(condition="s._change_type = 'delete'").whenMatchedUpdate(
    condition="s._change_type != 'delete'",
    set={"email": "s.email", "tier": "s.tier"},
).whenNotMatchedInsert(
    condition="s._change_type != 'delete'",
    values={"customer_id": "s.customer_id", "email": "s.email", "tier": "s.tier"},
).execute()

gold_rows = [tuple(r) for r in spark.read.format("delta").load(gold_path).orderBy("customer_id").collect()]
silver_rows = [tuple(r) for r in spark.read.format("delta").load(silver_path).orderBy("customer_id").collect()]

print(f"Gold table rows synced via CDF: {gold_rows}")
assert gold_rows == silver_rows
assert len(gold_rows) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Row-Level CDC**: Exposes exact inserts, updates, and deletes without full-table diffs.
# MAGIC - **Deduplication Rule**: Filter out `update_preimage` and take `_commit_version DESC` row_number == 1 before merging to avoid `UnsupportedOperationException` on duplicate keys.
# MAGIC - **Exact Parity**: Incremental CDF MERGE keeps Gold synchronized with Silver across updates and hard deletes.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What extra metadata columns are returned when reading a Delta table with `readChangeFeed = true`?
# MAGIC 2. Why must you filter out `update_preimage` and deduplicate multiple versions per key before executing `MERGE INTO`?
