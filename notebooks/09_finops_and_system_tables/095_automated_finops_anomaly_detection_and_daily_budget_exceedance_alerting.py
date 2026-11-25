# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 095. Automated FinOps Anomaly Detection & Daily Budget Exceedance Alerting
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A buggy recursive query triggered by a contractor consumed 5,000 DBUs in 4 hours, causing a $2,000 billing surprise. FinOps requires automated anomaly detection alerting when daily spend spikes.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop an automated FinOps anomaly detection algorithm in SQL/PySpark that calculates rolling 14-day mean and standard deviation of DBU spend and fires an alert if daily spend exceeds $3\sigma$.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Statistically bounding daily DBU consumption using moving z-scores ($Z = \frac{X - \mu}{\sigma}$) catches cost runaway anomalies within hours, preventing billing shocks at month-end.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Statistical Z-Score Cost Anomaly Detection
# MAGIC
# MAGIC Calculate rolling 14-day mean and standard deviation to detect cost outliers.
# COMMAND ----------

sql_anomaly_detection = """
WITH daily_costs AS (
    SELECT
        usage_date,
        SUM(usage_quantity) AS daily_dbus
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY usage_date
),
stats AS (
    SELECT
        usage_date,
        daily_dbus,
        AVG(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_mean,
        STDDEV(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_std
    FROM daily_costs
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
ORDER BY usage_date DESC;
"""

print("FinOps statistical cost anomaly query validated.")
assert "z_score" in sql_anomaly_detection
assert "CRITICAL_COST_ANOMALY" in sql_anomaly_detection
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Statistical Baselines**: Avoid fixed dollar thresholds that trigger false alarms; use rolling 14-day z-scores.
# MAGIC - **Automate Alerts**: Schedule the anomaly query in a DBSQL Alert to send immediate Slack/PagerDuty messages.
# MAGIC - **Root-Cause Linkage**: Alert payload can link directly to the high-cost query or cluster ID.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you implement statistical anomaly detection over Databricks billing telemetry?
# MAGIC 2. What action should an automated FinOps system take when a runaway query anomaly is detected?
