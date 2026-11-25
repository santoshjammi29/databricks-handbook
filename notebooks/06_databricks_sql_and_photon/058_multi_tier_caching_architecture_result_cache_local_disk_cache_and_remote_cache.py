# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 058. Multi-Tier Caching Architecture: Result Cache, Local Disk Cache & Remote Cache
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A dashboard with 50 visual tiles is refreshed by 500 business users throughout the day. Executing 25,000 queries directly against cloud object storage costs thousands in repeated scanning.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Verify live Delta commit cache coherency vs. manual Spark `CACHE TABLE` refresh behavior locally, demonstrating why Delta transaction log awareness prevents stale BI reads.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks SQL Result Cache and NVMe Disk Cache track underlying Delta `_delta_log` commits automatically—invalidating cached blocks the millisecond a DML commit alters referenced files. In open-source Spark, caching a DataFrame/View via `CACHE TABLE` pins executors' memory until `REFRESH TABLE` / `UNCACHE TABLE`.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Cache Coherency Test: Manual Spark Cache vs. Delta Live Snapshot Commits
# MAGIC
# MAGIC Materialize a Delta table, cache a read view with `CACHE TABLE`, append a new Delta commit, and confirm Spark catalog state + refreshed live read totals.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_058_", dir=globals().get("HANDBOOK_TMP_DIR")))
tbl_path = str(lab_dir / "cached_sales")

spark.createDataFrame([(1, 100.0), (2, 200.0)], ["order_id", "amount"]).write.format("delta").save(tbl_path)
spark.sql(f"CREATE TABLE t058_sales USING DELTA LOCATION '{tbl_path}'")
spark.sql("CACHE TABLE t058_sales")
assert spark.catalog.isCached("t058_sales") is True

initial_total = spark.sql("SELECT SUM(amount) FROM t058_sales").first()[0]

# New Delta commit adds +500.0; refresh/uncache aligns cached executors with latest _delta_log
spark.createDataFrame([(3, 500.0)], ["order_id", "amount"]).write.format("delta").mode("append").save(tbl_path)
spark.sql("REFRESH TABLE t058_sales")
refreshed_total = spark.sql("SELECT SUM(amount) FROM t058_sales").first()[0]

spark.sql("UNCACHE TABLE t058_sales")
assert spark.catalog.isCached("t058_sales") is False

print(f"Cached initial={initial_total}, post-commit refreshed={refreshed_total}")
assert initial_total == 300.0 and refreshed_total == 800.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Deterministic Invalidation**: DBSQL Result Cache & Disk Cache automatically invalidate when Delta `_delta_log` commits a new version.
# MAGIC - **Explicit Spark Cache Lifecycle**: In open Spark clusters, remember `REFRESH TABLE` / `UNCACHE TABLE` to keep executor memory aligned.
# MAGIC - **NVMe Delta Cache Advantage**: Persists hot Parquet columns natively on local SSDs without consuming JVM executor heap.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Databricks ensure that Query Result Cache never serves stale data after an update?
# MAGIC 2. What is the difference between the Spark `CACHE TABLE` command and the Databricks Disk Cache (Delta Cache)?
