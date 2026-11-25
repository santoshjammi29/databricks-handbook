# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 086. Lakehouse Monitoring: Automated Drift Detection, Quality Metrics & Alerting Tables
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A production credit card fraud model is experiencing degraded accuracy because customer spending behavior changed during holiday shopping. Engineers need automated alerts on statistical feature drift.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Compute real Delta feature-profile shifts and two-sample Kolmogorov-Smirnov (KS) empirical CDF divergence across baseline vs. drifted transaction windows using Spark SQL.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakehouse Monitoring automatically computes `_profile_metrics` and `_drift_metrics` over Delta tables in Databricks. Computing empirical CDF buckets and mean-shift deltas in Spark SQL demonstrates the exact mathematics behind KS feature drift alerts.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Profile Mean Shift & Empirical Two-Sample KS Drift Statistic in Spark SQL
# MAGIC
# MAGIC Compare a baseline vs. shifted spending window stored in Delta Lake, compute profile means + max CDF separation (`ks_stat`), and raise `DRIFT_DETECTED`.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_086_", dir=globals().get("HANDBOOK_TMP_DIR")))
base_path = str(lab_dir / "tx_baseline")
curr_path = str(lab_dir / "tx_current")

spark.range(0, 200).select((50.0 + (F.col("id") % 50)).alias("tx_amount")).write.format("delta").save(base_path)
spark.range(0, 200).select((180.0 + (F.col("id") % 50)).alias("tx_amount")).write.format("delta").save(curr_path)

spark.sql(f"CREATE TABLE t086_baseline USING DELTA LOCATION '{base_path}'")
spark.sql(f"CREATE TABLE t086_current USING DELTA LOCATION '{curr_path}'")

profile_df = spark.sql("""
    SELECT 'baseline' AS window_name, ROUND(AVG(tx_amount), 2) AS mean_amt, ROUND(STDDEV(tx_amount), 2) AS std_amt FROM t086_baseline
    UNION ALL
    SELECT 'current'  AS window_name, ROUND(AVG(tx_amount), 2) AS mean_amt, ROUND(STDDEV(tx_amount), 2) AS std_amt FROM t086_current
""")
profiles = {r["window_name"]: r for r in profile_df.collect()}

# Empirical two-sample KS statistic = MAX |CDF_baseline(x) - CDF_current(x)| over threshold buckets
ks_df = spark.sql("""
    WITH buckets AS (
        SELECT explode(array(75.0, 100.0, 150.0, 200.0, 225.0)) AS cutoff
    ),
    cdf_b AS (
        SELECT b.cutoff, AVG(CASE WHEN t.tx_amount <= b.cutoff THEN 1.0 ELSE 0.0 END) AS fb
        FROM buckets b CROSS JOIN t086_baseline t GROUP BY b.cutoff
    ),
    cdf_c AS (
        SELECT b.cutoff, AVG(CASE WHEN t.tx_amount <= b.cutoff THEN 1.0 ELSE 0.0 END) AS fc
        FROM buckets b CROSS JOIN t086_current t GROUP BY b.cutoff
    )
    SELECT ROUND(MAX(ABS(cdf_b.fb - cdf_c.fc)), 3) AS ks_stat
    FROM cdf_b JOIN cdf_c ON cdf_b.cutoff = cdf_c.cutoff
""")

ks_stat = ks_df.first()["ks_stat"]
mean_delta = round(profiles["current"]["mean_amt"] - profiles["baseline"]["mean_amt"], 2)
print(f"Baseline mean=${profiles['baseline']['mean_amt']}, Current mean=${profiles['current']['mean_amt']} (delta=${mean_delta}, KS={ks_stat})")
assert mean_delta > 100.0 and ks_stat >= 0.9
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Pipeline Overhead**: Lakehouse Monitors run asynchronously over Delta `_delta_log` telemetry.
# MAGIC - **Distribution Drift Detection**: Track mean shifts alongside non-parametric Kolmogorov-Smirnov (KS) CDF divergence.
# MAGIC - **Unified Metrics Tables**: Write profile & drift history directly into Unity Catalog Delta tables.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Profile Metrics and Drift Metrics in Databricks Lakehouse Monitoring?
# MAGIC 2. How does Lakehouse Monitoring detect concept drift in deployed machine learning models?
