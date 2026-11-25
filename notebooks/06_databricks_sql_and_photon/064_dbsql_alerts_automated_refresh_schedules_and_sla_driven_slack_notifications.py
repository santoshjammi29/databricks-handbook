# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 064. DBSQL Alerts, Automated Refresh Schedules & SLA-Driven Slack Notifications
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A payments platform must be alerted within 5 minutes if failed credit card transactions exceed 2% of total volume over any rolling 15-minute window.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute rolling threshold SQL alert queries over Delta payment telemetry (`failure_rate_pct > 2.0%`), separating healthy windows from SLA-breaching alert windows.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DBSQL Alerts evaluate scheduled SQL queries and dispatch Slack/PagerDuty webhooks whenever returned aggregate metrics violate numeric predicates.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Rolling Window SQL Alert Query & SLA Breach Trigger
# MAGIC
# MAGIC Persist healthy and degraded 15-minute payment authorization windows in Delta Lake, run the DBSQL alert evaluation query, and assert only the incident window triggers.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_064_", dir=globals().get("HANDBOOK_TMP_DIR")))
pay_path = str(lab_dir / "payment_events")

rows = [("w1_healthy", "OK") for _ in range(99)] + [("w1_healthy", "FAILED")]
rows += [("w2_incident", "OK") for _ in range(90)] + [("w2_incident", "FAILED") for _ in range(10)]
spark.createDataFrame(rows, ["window_id", "tx_status"]).write.format("delta").save(pay_path)
spark.sql(f"CREATE TABLE t064_payments USING DELTA LOCATION '{pay_path}'")

alert_df = spark.sql("""
    WITH window_kpis AS (
        SELECT
            window_id,
            ROUND(SUM(CASE WHEN tx_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct
        FROM t064_payments
        GROUP BY window_id
    )
    SELECT window_id, failure_rate_pct, failure_rate_pct > 2.0 AS trigger_slack_alert
    FROM window_kpis
    ORDER BY window_id
""")

alerts = {r["window_id"]: (r["failure_rate_pct"], r["trigger_slack_alert"]) for r in alert_df.collect()}
print(f"DBSQL Alert Evaluation: {alerts}")
assert alerts["w1_healthy"] == (1.0, False)
assert alerts["w2_incident"] == (10.0, True)
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Proactive Alerting**: Detect SLA regressions cleanly in SQL before customers report outages.
# MAGIC - **Multi-Channel Destinations**: Dispatch DBSQL Alerts to Slack, PagerDuty, or HTTP webhooks.
# MAGIC - **Trigger Semantics**: Choose `Trigger Once` vs. `Each Time` to avoid pager fatigue.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do DBSQL Alerts evaluate conditions across single-value versus multi-row query results?
# MAGIC 2. What is the difference between 'Trigger Once' and 'Trigger Each Time' in Databricks SQL Alerts?
