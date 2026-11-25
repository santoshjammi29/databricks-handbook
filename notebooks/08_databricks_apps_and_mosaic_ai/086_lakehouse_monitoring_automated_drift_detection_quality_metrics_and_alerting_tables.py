# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 086. Lakehouse Monitoring: Automated Drift Detection, Quality Metrics & Alerting Tables
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A production credit card fraud model is experiencing degraded accuracy because customer spending behavior changed during holiday shopping. Engineers need automated alerts on statistical feature drift.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy a Databricks Lakehouse Monitor on a Delta table, analyzing automated profile and drift metric tables (`_profile_metrics`, `_drift_metrics`), tracking Kolmogorov-Smirnov and Jensen-Shannon divergence.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakehouse Monitoring automatically profiles Delta tables and model inference logs. It tracks data quality, schema drift, statistical distribution drift (KS test, Wasserstein distance), and writes metrics directly to Unity Catalog metric tables.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Lakehouse Monitor Metric Table Schema Inspection
# MAGIC
# MAGIC Simulate and verify statistical drift metrics tracked by Lakehouse Monitoring.
# COMMAND ----------

drift_metrics_sample = {
    "column_name": "transaction_amount",
    "time_window": "2026-11-17",
    "baseline_mean": 142.50,
    "current_mean": 218.40,
    "ks_test_p_value": 0.002, # Highly significant distribution shift!
    "drift_detected": True
}

print(f"Monitored Feature: {drift_metrics_sample['column_name']}")
print(f"Mean Shift: ${drift_metrics_sample['baseline_mean']} -> ${drift_metrics_sample['current_mean']}")
print(f"Statistical Significance (KS p-value): {drift_metrics_sample['ks_test_p_value']}")
assert drift_metrics_sample["drift_detected"] is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Pipeline Overhead**: Monitors run asynchronously without impacting production write jobs.
# MAGIC - **Statistical Tests Built-in**: Automatically computes Kolmogorov-Smirnov and Chi-square drift statistics.
# MAGIC - **Dashboard Out-of-the-Box**: Automatically generates an AI/BI dashboard visualizing table trends.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Profile Metrics and Drift Metrics in Databricks Lakehouse Monitoring?
# MAGIC 2. How does Lakehouse Monitoring detect concept drift in deployed machine learning models?
