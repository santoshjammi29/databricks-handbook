# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 010. Workspace Audit Logging & Security Event Ingestion via Diagnostic Settings
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A cyber-security operations center (SOC) requires real-time alerting on unauthorized notebook exports, permissions escalation, and unexpected secret reads across all Databricks workspaces.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop a PySpark pipeline ingesting raw cloud diagnostic audit logs (Azure Monitor / AWS CloudWatch) into a Delta Lake security audit table with automated intrusion detection rules.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks generates comprehensive JSON audit logs for every workspace action (notebook commands, login attempts, secret reads, cluster changes). These stream to cloud storage and can be queried directly via `system.access.audit` or custom Bronze audit tables.
# COMMAND ----------

from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Ingest & Parse Diagnostic Security Audit Logs
# MAGIC
# MAGIC Parse raw audit JSON records and flag suspicious privilege escalations.
# COMMAND ----------

raw_audit_records = [
    {"timestamp": "2026-11-17T10:00:00Z", "action": "login", "user": "alice@company.com", "status": "SUCCESS", "ip": "10.0.1.5"},
    {"timestamp": "2026-11-17T10:05:00Z", "action": "secrets.getSecret", "user": "alice@company.com", "status": "SUCCESS", "ip": "10.0.1.5"},
    {"timestamp": "2026-11-17T10:12:00Z", "action": "grantPermissions", "user": "contractor@vendor.com", "status": "FAILURE", "ip": "198.51.100.44"},
    {"timestamp": "2026-11-17T10:13:00Z", "action": "notebook.export", "user": "contractor@vendor.com", "status": "SUCCESS", "ip": "198.51.100.44"}
]

df_audit = spark.createDataFrame(raw_audit_records)
df_suspicious = df_audit.filter((F.col("action") == "notebook.export") | (F.col("status") == "FAILURE"))
print("Security Alerts Flagged:")
df_suspicious.show(truncate=False)

assert df_suspicious.count() == 2, "Expected 2 flagged security events!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Diagnostic Settings**: Stream workspace logs to Azure Log Analytics, S3, or GCS.
# MAGIC - **System Audit Tables**: Query `system.access.audit` for unified, zero-ETL access to account-level security events.
# MAGIC - **Automated Intrusion Detection**: Set up hourly SQL alerts on critical actions like `grantPermissions` and `notebook.export`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What events are captured in Databricks audit logs?
# MAGIC 2. How can you detect data exfiltration attempts using Databricks audit telemetry?
