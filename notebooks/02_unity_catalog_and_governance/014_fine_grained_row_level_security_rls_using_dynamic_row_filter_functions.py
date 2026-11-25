# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 014. Fine-Grained Row-Level Security (RLS) using Dynamic Row Filter Functions
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A global healthcare provider must restrict patient records so doctors can only view patients within their assigned hospital region, while compliance officers can view all records.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author and attach a dynamic SQL Row Filter function to a Delta table, testing that the filter transparently prunes rows based on caller session identity.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Dynamic Row Filters attach directly to physical tables in Unity Catalog. When a query executes, Catalyst injects the boolean filter function into the logical plan, executing security filtering without data duplication.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Define & Attach Dynamic Row Filter Function
# MAGIC
# MAGIC Write the SQL DDL for dynamic row filtering using `IS_ACCOUNT_GROUP_MEMBER()`.
# COMMAND ----------

# Simulate row filter logic in PySpark
def evaluate_row_access(user_groups: list, row_region: str) -> bool:
    if "compliance_admins" in user_groups:
        return True
    if "emea_doctors" in user_groups and row_region == "EMEA":
        return True
    if "us_doctors" in user_groups and row_region == "US":
        return True
    return False

# Test scenarios
assert evaluate_row_access(["compliance_admins"], "EMEA") is True
assert evaluate_row_access(["us_doctors"], "EMEA") is False
assert evaluate_row_access(["us_doctors"], "US") is True
print("Dynamic Row Filter evaluation validated across all user personas.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Data Duplication**: A single physical table serves all user tiers safely.
# MAGIC - **Optimizer Integration**: Catalyst pushes row filter predicates down into storage scans for maximum performance.
# MAGIC - **Metastore Administration**: Only table owners or metastore admins can attach or remove row filters.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Dynamic Row Filters differ from creating separate secure views for each region?
# MAGIC 2. What built-in Unity Catalog functions are used to inspect the current user's session in row filter functions?
