# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 064. DBSQL Alerts, Automated Refresh Schedules & SLA-Driven Slack Notifications
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Foundational`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A payments platform must be alerted within 5 minutes if failed credit card transactions exceed 2% of total volume over any rolling 15-minute window.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure automated Databricks SQL Alerts on scheduled queries, evaluate threshold triggers (`>` or `<`), and configure webhook destinations for Slack and PagerDuty.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DBSQL Alerts execute a query on a recurring schedule. When the returned result crosses a predefined threshold, Databricks automatically fires notifications to configured destinations (Slack, Teams, PagerDuty, Webhooks).
# COMMAND ----------

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# Initialize or obtain active SparkSession with Delta Lake & Unity Catalog support
spark = SparkSession.builder \
    .appName("DatabricksHandbook") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. SQL Alert Definition & Threshold Evaluation
# MAGIC
# MAGIC Define an alert query and trigger condition.
# COMMAND ----------

alert_definition = {
    "name": "High Payment Failure Rate Alert",
    "query": "SELECT failure_rate_pct FROM prod_lakehouse.gold.payment_kpis WHERE window_start >= NOW() - INTERVAL 15 MIN",
    "condition": {
        "column": "failure_rate_pct",
        "operator": ">",
        "threshold": 2.0
    },
    "schedule": "EVERY 5 MINUTES",
    "notification_destination": "slack-data-alerts-channel"
}

# Simulate threshold check
current_failure_rate = 3.4
triggered = current_failure_rate > alert_definition["condition"]["threshold"]

print(f"Alert: {alert_definition['name']}")
print(f"Current Value: {current_failure_rate}% | Threshold: {alert_definition['condition']['threshold']}%")
print(f"Alert Fired to Slack: {triggered}")
assert triggered is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Proactive Alerting**: Catch operational anomalies before business users notice.
# MAGIC - **Multi-Channel**: Send alerts to Slack channels, PagerDuty on-call services, or custom webhooks.
# MAGIC - **State Tracking**: Alerts can trigger 'Just Once' when passing threshold or 'Each Time' evaluated.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do DBSQL Alerts evaluate conditions across single-value versus multi-row query results?
# MAGIC 1. What is the difference between 'Trigger Once' and 'Trigger Each Time' in Databricks SQL Alerts?
