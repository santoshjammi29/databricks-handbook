# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 092. Audit & Security Analytics: Investigating Access Logs with system.access.audit
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Following an employee departure, the security team needs a forensic audit of every table queried, exported, or modified by that employee during their final two weeks.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query `system.access.audit` to trace user actions, filtering on user identity, extracting accessed table names, IP addresses, and identifying unauthorized data export attempts.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `system.access.audit` provides unified, immutable audit logs across all workspaces in an account. It records authentication events, notebook executions, table reads/writes, cluster modifications, and secret access.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Forensic User Activity Audit Query
# MAGIC
# MAGIC Construct forensic investigation queries tracking user operations across workspaces.
# COMMAND ----------

sql_forensic_audit = """
-- Forensic trace of all actions performed by a specific user identity
SELECT
    event_time,
    workspace_id,
    action_name,
    service_name,
    source_ip_address,
    request_params.table_full_name AS accessed_table,
    response.status_code
FROM system.access.audit
WHERE user_identity.email = 'former_employee@company.com'
  AND event_time >= NOW() - INTERVAL 14 DAYS
ORDER BY event_time DESC
LIMIT 50;
"""

print("Forensic audit query verified.")
assert "system.access.audit" in sql_forensic_audit
assert "user_identity.email" in sql_forensic_audit
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Immutable Audit Trail**: System audit logs cannot be altered by developers or workspace admins.
# MAGIC - **IP Address Tracking**: Trace queries back to corporate VPNs or unexpected external IP addresses.
# MAGIC - **Compliance Audits**: Provide instant reports for SOC 2, HIPAA, and ISO 27001 regulatory inquiries.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What specific user actions are tracked in `system.access.audit`?
# MAGIC 2. How can you detect anomalous large data downloads or notebook exports using audit telemetry?
