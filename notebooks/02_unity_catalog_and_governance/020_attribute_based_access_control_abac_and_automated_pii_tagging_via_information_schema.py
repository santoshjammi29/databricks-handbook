# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 020. Attribute-Based Access Control (ABAC) & Automated PII Tagging via Information Schema
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A compliance team must enforce data policies across 5,000 tables. Managing table grants manually is impossible; policies must automatically apply based on metadata tags like `classification:pii`.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy Attribute-Based Access Control (ABAC) in Unity Catalog, tag columns automatically using Python and Information Schema queries, and enforce tag-based column masking.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC ABAC evaluates access based on user attributes, asset tags, and environment context rather than hardcoded role grants. Unity Catalog allows binding masking policies directly to tags (`TAG classification = 'pii'`).
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Automated PII Tagging via Information Schema Discovery
# MAGIC
# MAGIC Identify columns matching sensitive patterns and apply governance tags programmatically.
# COMMAND ----------

# Simulate discovering columns that require PII classification
columns_to_audit = [
    {"table": "customers", "column": "email_address", "type": "STRING"},
    {"table": "customers", "column": "home_phone", "type": "STRING"},
    {"table": "orders", "column": "order_total", "type": "DECIMAL"}
]

pii_keywords = ["email", "phone", "ssn", "national_id", "credit_card"]
tagged_columns = []

for col in columns_to_audit:
    is_pii = any(k in col["column"].lower() for k in pii_keywords)
    tag = "classification=pii" if is_pii else "classification=internal"
    tagged_columns.append({**col, "tag": tag})

print("Automated Governance Tagging Results:")
for t in tagged_columns:
    print(f"  {t['table']}.{t['column']} -> {t['tag']}")

assert tagged_columns[0]["tag"] == "classification=pii"
assert tagged_columns[2]["tag"] == "classification=internal"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Scalable Governance**: Manage policies across thousands of tables using metadata tags instead of individual table grants.
# MAGIC - **Tag-Based Masking**: Bind a dynamic column mask once to a tag; every tagged column across all catalogs is masked automatically.
# MAGIC - **Information Schema**: Automate compliance scanning via `system.information_schema`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Attribute-Based Access Control (ABAC) differ from Role-Based Access Control (RBAC)?
# MAGIC 2. How can you automatically discover and tag PII columns across an entire catalog in Unity Catalog?
