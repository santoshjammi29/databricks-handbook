# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 059. DBSQL Query Profile Analysis: Diagnosing Scans, Shuffles, Spills & Pruning Efficiency
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An executive dashboard query takes 85 seconds to run. The business demands sub-5-second performance. The engineer must use Query Profile to identify whether the bottleneck is scanning, spilling, or shuffling.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Inspect and parse a Databricks SQL Query Profile, calculate data skipping efficiency (`Files Read` vs. `Files Pruned`), and eliminate disk spill bottlenecks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Query Profile visualizes the physical execution tree in DBSQL. Key metrics include: Scan Time, Files Pruned (partition/clustering efficiency), Shuffle Exchange Rows, and Memory Spill to Disk.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Query Profile Metric Extraction & Bottleneck Triage
# MAGIC
# MAGIC Analyze simulated query profile metrics to pinpoint performance regressions.
# COMMAND ----------

query_profile_metrics = {
    "query_id": "01ef-5544-aa33",
    "total_duration_ms": 85000,
    "stages": {
        "scan_orders": {
            "total_files": 12500,
            "files_read": 12500,
            "files_pruned": 0, # ZERO PRUNING!
            "bytes_read": "850 GB",
            "time_ms": 62000
        },
        "hash_join": {
            "spill_to_disk_bytes": "45 GB", # DISK SPILL!
            "time_ms": 18000
        }
    }
}

scan = query_profile_metrics["stages"]["scan_orders"]
prune_pct = (scan["files_pruned"] / scan["total_files"]) * 100
print(f"Total Scan Time: {scan['time_ms'] / 1000:.1f}s")
print(f"File Pruning Efficiency: {prune_pct:.1f}%")
print(f"Memory Spilled to Disk: {query_profile_metrics['stages']['hash_join']['spill_to_disk_bytes']}")

assert scan["files_pruned"] == 0, "Diagnostic Alert: Query performed full table scan!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Pruning Flag**: If `files_pruned == 0`, the query is doing a full table scan; apply Liquid Clustering.
# MAGIC - **Spill Detection**: High `spill_to_disk_bytes` indicates cluster RAM is undersized or join keys are skewed.
# MAGIC - **Scan Bottlenecks**: Scans taking > 70% of query time indicate missing partition/clustering filters.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you identify whether a slow query is bottlenecked on I/O scan vs. CPU shuffle in DBSQL Query Profile?
# MAGIC 2. What does 'Rows Spilled to Disk' indicate in a Query Profile?
