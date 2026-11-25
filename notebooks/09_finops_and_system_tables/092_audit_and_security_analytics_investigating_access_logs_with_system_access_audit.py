# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 092. Audit & Security Analytics: Investigating Access Logs with system.access.audit
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Following an employee departure, the security team needs a forensic audit of every table queried, exported, or modified by that employee during their final two weeks.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Run forensic Spark SQL queries over Unity Catalog audit telemetry modeled after `system.access.audit`, identifying bulk table exports, permission denials, and untrusted source IP addresses.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `system.access.audit` captures immutable workspace authentication, SQL table reads, permission grants, and export events. Locally we query a structured audit log temp view capturing the identical nested JSON fields.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Forensic User Activity & Exfiltration Investigation Query
# MAGIC
# MAGIC Query nested audit telemetry for offboarding forensics, flagging external IP table exports and failed authorization probes.
# COMMAND ----------

audit_events = [
    ("2026-11-18T14:00:00Z", "ws-01", "former_employee@company.com", "getTable", "unityCatalog", "10.20.1.5", "prod.pii.customers", 200),
    ("2026-11-18T14:05:00Z", "ws-01", "former_employee@company.com", "exportResults", "databrickssql", "198.51.100.99", "prod.pii.customers", 200),
    ("2026-11-18T14:07:00Z", "ws-01", "former_employee@company.com", "getSecret", "secrets", "198.51.100.99", "prod_kv_scope/api_key", 403),
    ("2026-11-18T15:00:00Z", "ws-01", "etl_sp@company.com", "commitTransaction", "unityCatalog", "10.20.0.10", "prod.silver.orders", 200),
]
spark.createDataFrame(
    audit_events,
    ["event_time", "workspace_id", "user_email", "action_name", "service_name", "source_ip", "target_asset", "status_code"],
).createOrReplaceTempView("access_audit_events")

suspect_df = spark.sql("""
    SELECT event_time, user_email, action_name, source_ip, target_asset, status_code
    FROM access_audit_events
    WHERE user_email = 'former_employee@company.com'
      AND (NOT source_ip LIKE '10.%' OR status_code >= 400)
    ORDER BY event_time
""")

suspect_rows = suspect_df.collect()
print(f"Flagged high-risk offboarding events: {len(suspect_rows)}")
assert len(suspect_rows) == 2
assert {r["action_name"] for r in suspect_rows} == {"exportResults", "getSecret"}
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Immutable Audit Trail**: Account-level audit tables cannot be modified by workspace users or admins.
# MAGIC - **IP Anomaly Detection**: Correlate `source_ip_address` outside corporate CIDR blocks with export actions.
# MAGIC - **SOC 2 Compliance**: Automate post-offboarding access reviews cleanly in SQL.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What specific user actions are tracked in `system.access.audit`?
# MAGIC 2. How can you detect anomalous large data downloads or notebook exports using audit telemetry?
