# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 095. Automated FinOps Anomaly Detection & Daily Budget Exceedance Alerting
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A buggy recursive query triggered by a contractor consumed 5,000 DBUs in 4 hours, causing a $2,000 billing surprise. FinOps requires automated anomaly detection alerting when daily spend spikes.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement an automated rolling 14-day Z-score ($Z = (X - \mu)/\sigma$) anomaly detector in Spark SQL over multi-day daily spend history and assert runaway spikes exceeding $3\sigma$ trigger `CRITICAL_COST_ANOMALY`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Static dollar thresholds trigger false alarms during seasonal peaks. Moving 14-day baseline window functions (`AVG` and `STDDEV` with `ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING`) adapt automatically and isolate $3\sigma$ outliers cleanly.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Rolling 14-Day Z-Score Anomaly Detection in Spark SQL
# MAGIC
# MAGIC Generate a 16-day baseline with subtle daily variance followed by a runaway 4,500-DBU spike on Day 16, and execute Spark SQL rolling window statistics to classify alerts.
# COMMAND ----------

daily_spend = [(f"2026-11-{d:02d}", float(500 + (d % 4) * 15)) for d in range(1, 16)]
daily_spend.append(("2026-11-16", 4500.0))  # Runaway contractor job spike!

spark.createDataFrame(daily_spend, ["usage_date", "daily_dbus"]).createOrReplaceTempView("daily_dbu_usage")

alerts_df = spark.sql("""
    WITH stats AS (
        SELECT
            usage_date,
            daily_dbus,
            AVG(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_mean,
            STDDEV(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_std
        FROM daily_dbu_usage
    )
    SELECT
        usage_date,
        daily_dbus,
        ROUND(rolling_mean, 1) AS baseline_mean,
        ROUND((daily_dbus - rolling_mean) / NULLIF(rolling_std, 0), 2) AS z_score,
        CASE
            WHEN (daily_dbus - rolling_mean) / NULLIF(rolling_std, 0) > 3.0 THEN 'CRITICAL_COST_ANOMALY'
            WHEN (daily_dbus - rolling_mean) / NULLIF(rolling_std, 0) > 2.0 THEN 'WARNING_COST_SPIKE'
            ELSE 'NORMAL'
        END AS anomaly_status
    FROM stats
    ORDER BY usage_date DESC
""")

latest = alerts_df.first()
print(f"Day {latest['usage_date']}: {latest['daily_dbus']} DBUs (z={latest['z_score']}) -> {latest['anomaly_status']}")
assert latest["anomaly_status"] == "CRITICAL_COST_ANOMALY"
assert latest["z_score"] > 10.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Statistical Baselines**: Avoid brittle static thresholds; use rolling 14-day z-scores excluding the current day (`1 PRECEDING`).
# MAGIC - **Automate Alerts**: Schedule the anomaly query in a DBSQL Alert connected to Slack/PagerDuty.
# MAGIC - **Root-Cause Linkage**: Join anomalies with top-consuming `cluster_id` or `job_id` for immediate triage.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you implement statistical anomaly detection over Databricks billing telemetry?
# MAGIC 2. What action should an automated FinOps system take when a runaway query anomaly is detected?
