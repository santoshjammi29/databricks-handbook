# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 104. Production Incident 06: Serverless SQL Warehouse Queue Saturation & Spill Tuning
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC During Monday morning executive review, 150 dashboard users connect simultaneously to a Serverless SQL Warehouse. Queries queue for 45 seconds and spill gigabytes to disk.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Diagnose query queue saturation and disk spills via Spark SQL over warehouse execution history telemetry, flag overloaded clusters for Economy->Pro upgrade, and verify AQE partition coalescing.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC When concurrent query demand exceeds slot limits or shuffle partitions spill memory to SSDs, DBSQL P99 latencies degrade sharply. Analyzing `waiting_for_compute_ms` + `spill_to_disk_bytes` alongside AQE partition coalescing restores sub-second response times.
# COMMAND ----------

from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Warehouse Queue Telemetry Diagnosis & Shuffle Partition Coalescing
# MAGIC
# MAGIC Correlate warehouse queue delays and disk spills in Spark SQL, classify congested warehouses for horizontal `Pro` autoscaling, and verify AQE coalesces tiny shuffle partitions.
# COMMAND ----------

# Modeled after Databricks `system.compute.query_history` warehouse metrics
q_logs = [
    ("wh-exec-bi", 42000, 18 * 1024**3, 1800),
    ("wh-exec-bi", 38000, 12 * 1024**3, 1650),
    ("wh-adhoc-dev", 300, 0, 150),
]
spark.createDataFrame(
    q_logs, ["warehouse_id", "waiting_for_compute_ms", "spill_to_disk_bytes", "execution_ms"]
).createOrReplaceTempView("wh_query_history")

triage_df = spark.sql("""
    SELECT
        warehouse_id,
        ROUND(AVG(waiting_for_compute_ms) / 1000.0, 2) AS avg_queue_sec,
        ROUND(SUM(spill_to_disk_bytes) / POW(1024, 3), 1) AS total_spill_gb,
        CASE WHEN AVG(waiting_for_compute_ms) > 10000 THEN 'UPGRADE_TO_PRO_AUTOSCALE' ELSE 'HEALTHY' END AS recommendation
    FROM wh_query_history
    GROUP BY warehouse_id
""")
recs = {r["warehouse_id"]: r["recommendation"] for r in triage_df.collect()}

# Verify Spark AQE coalesces over-partitioned small shuffles instead of spilling overhead
spark.conf.set("spark.sql.shuffle.partitions", "200")
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
agg_df = spark.range(0, 500).withColumn("grp", F.col("id") % 5).groupBy("grp").count()
actual_parts = agg_df.rdd.getNumPartitions()

print(f"Warehouse recommendations: {recs} | Coalesced partitions: {actual_parts}")
assert recs["wh-exec-bi"] == "UPGRADE_TO_PRO_AUTOSCALE" and recs["wh-adhoc-dev"] == "HEALTHY"
assert actual_parts < 200 and agg_df.count() == 5
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Pro Scaling Policy**: Aggressively launches horizontal SQL clusters as soon as query queues form.
# MAGIC - **Eliminate Spills with Liquid Clustering**: Clustered Delta reads minimize shuffle memory footprints.
# MAGIC - **Workload Isolation**: Separate SLA-critical BI warehouses from ad-hoc exploratory endpoints.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Economy and Pro scaling policies on Databricks SQL Warehouses?
# MAGIC 2. How do you eliminate disk spills in heavy distributed joins on SQL Warehouses?
