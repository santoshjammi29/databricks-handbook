# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 093. Compute Right-Sizing: Detecting Zombie Clusters & Low-CPU Utilization
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise cluster audit discovered 15 interactive clusters that were left running overnight with 0% CPU utilization, wasting $1,200 per day in idle compute.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Join cluster uptime metadata with query execution history in Spark SQL to detect zombie clusters (`uptime > 2h` with `0` queries executed) and calculate reclaimable DBU waste.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Correlating `system.compute.clusters` uptime windows against `system.compute.query_history` surfaces orphaned All-Purpose clusters that were left un-terminated or bypassed cluster auto-stop policies.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Zombie Cluster SQL Correlation & Waste Quantification
# MAGIC
# MAGIC Join cluster telemetry with query execution logs in Spark SQL to flag zero-query zombie compute and compute daily wasted DBUs.
# COMMAND ----------

clusters = [
    ("cl-001", "prod-etl-stream", 24.0, 16.0),
    ("cl-002", "analyst-sandbox-1", 14.0, 8.0),
    ("cl-003", "dev-scratch", 8.0, 4.0),
]
queries = [
    ("q-1", "cl-001", 1200),
    ("q-2", "cl-003", 180),
]
spark.createDataFrame(clusters, ["cluster_id", "cluster_name", "uptime_hours", "dbu_per_hour"]).createOrReplaceTempView("compute_clusters")
spark.createDataFrame(queries, ["query_id", "cluster_id", "exec_ms"]).createOrReplaceTempView("compute_queries")

zombies_df = spark.sql("""
    SELECT
        c.cluster_id,
        c.cluster_name,
        c.uptime_hours,
        COUNT(q.query_id) AS queries_executed,
        ROUND(c.uptime_hours * c.dbu_per_hour, 2) AS wasted_dbus
    FROM compute_clusters c
    LEFT JOIN compute_queries q ON c.cluster_id = q.cluster_id
    GROUP BY c.cluster_id, c.cluster_name, c.uptime_hours, c.dbu_per_hour
    HAVING queries_executed = 0 AND uptime_hours > 2.0
""")

zombies = zombies_df.collect()
print(f"Detected zombie clusters: {[(z['cluster_id'], z['wasted_dbus']) for z in zombies]}")
assert len(zombies) == 1
assert zombies[0]["cluster_id"] == "cl-002" and zombies[0]["wasted_dbus"] == 112.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Eliminate Zombie Spend**: Enforce 10–15 minute auto-termination on all interactive clusters via Cluster Policies.
# MAGIC - **Right-Sizing Audits**: Correlate cluster DBU burn with actual SQL/job query counts.
# MAGIC - **Automated Remediation**: Wire zombie-detection queries into Databricks Alerts + Cluster Termination API.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you correlate compute cluster runtime with actual query activity to identify idle resources?
# MAGIC 2. What cluster policy settings prevent developers from disabling auto-termination?
