# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 029. Shallow Clones vs. Deep Clones: Zero-Copy Sandboxes, Testing & Disaster Recovery
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data science team needs a sandbox copy of a 10 TB production dataset to test experimental machine learning models. Duplicating 10 TB of data would take hours and cost thousands in cloud storage.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute real `SHALLOW CLONE` in Delta SQL, verify zero copied Parquet files inside the clone directory, prove mutation isolation against the source table, and contrast with physically decoupled replicas (`DEEP CLONE` in Databricks).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC A `SHALLOW CLONE` copies only `_delta_log` metadata, referencing existing parent Parquet files in place—making creation instant at zero initial storage cost. (`DEEP CLONE` copies both metadata and physical Parquet files in Databricks Runtime; locally in OSS Delta we model a decoupled physical snapshot alongside `SHALLOW CLONE`.)
# COMMAND ----------

import json
import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Execute Real `SHALLOW CLONE` & Verify Zero-Copy Disk Footprint
# MAGIC
# MAGIC Create a production Delta table with Parquet files on disk, run `CREATE OR REPLACE TABLE ... SHALLOW CLONE ...`, and confirm zero physical `.parquet` data files are duplicated in the sandbox folder.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_029_", dir=globals().get("HANDBOOK_TMP_DIR")))
prod_path = str(lab_dir / "prod_orders")
sandbox_path = str(lab_dir / "sandbox_orders")

spark.range(0, 1000).write.format("delta").save(prod_path)
spark.sql(f"CREATE TABLE t029_prod USING DELTA LOCATION '{prod_path}'")

spark.sql(f"CREATE OR REPLACE TABLE t029_sandbox SHALLOW CLONE t029_prod LOCATION '{sandbox_path}'")

prod_parquets = list(Path(prod_path).glob("*.parquet"))
sandbox_parquets = list(Path(sandbox_path).glob("*.parquet"))
sandbox_v0 = (Path(sandbox_path) / "_delta_log" / "00000000000000000000.json").read_text(encoding="utf-8")

print(f"Parent Parquet count : {len(prod_parquets)}")
print(f"Shallow Clone Parquets: {len(sandbox_parquets)} (0 physical copies!)")
assert len(prod_parquets) >= 1
assert len(sandbox_parquets) == 0
assert "prod_orders" in sandbox_v0
assert spark.table("t029_sandbox").count() == 1000
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Prove Mutation Isolation & Physical Decoupling for Disaster Recovery
# MAGIC
# MAGIC Mutate the shallow clone (delete 400 rows + append 50 rows), assert the production parent remains unchanged at 1,000 rows, and contrast with a physically decoupled replica.
# COMMAND ----------

spark.sql("DELETE FROM t029_sandbox WHERE id < 400")
spark.sql("INSERT INTO t029_sandbox SELECT id + 2000 AS id FROM range(50)")

prod_count = spark.table("t029_prod").count()
sandbox_count = spark.table("t029_sandbox").count()

# Model physically decoupled replica (equivalent to DBR `DEEP CLONE` independent Parquet copy)
dr_path = str(lab_dir / "dr_orders_replica")
spark.table("t029_prod").write.format("delta").save(dr_path)
dr_parquets = list(Path(dr_path).glob("*.parquet"))
dr_count = spark.read.format("delta").load(dr_path).count()

print(f"Production rows after sandbox mutations: {prod_count}")
print(f"Sandbox rows after mutations           : {sandbox_count}")
print(f"Decoupled DR Parquet files             : {len(dr_parquets)} ({dr_count} rows)")

assert prod_count == 1000
assert sandbox_count == 650
assert len(dr_parquets) >= 1 and dr_count == 1000
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Instant Sandboxes**: Shallow clones copy only metadata pointers, creating zero-byte-overhead clones in seconds.
# MAGIC - **Isolation Guaranteed**: Deletes and inserts inside a shallow clone never mutate the parent table.
# MAGIC - **Disaster Recovery**: Physically decoupled copies (`DEEP CLONE` on Databricks) replicate Parquet data so `VACUUM` on source cannot break DR.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What happens to a Shallow Clone if someone runs `VACUUM` on the source parent table?
# MAGIC 2. Can you clone a specific historical version of a Delta table using Time Travel syntax?
