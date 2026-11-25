# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 030. Schema Evolution (`mergeSchema`) vs. Enforcement & Table Constraints
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An API integration team frequently alters incoming JSON payloads, adding new tracking fields. The data pipeline must enforce data types on core columns while allowing safe addition of new fields without crashing.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the operational difference between Delta Schema Enforcement (rejecting schema mismatches) and Schema Evolution (`mergeSchema = true`), and enforce business invariants using `CHECK` constraints.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake enforces schema on write by default, rejecting writes with missing or extra columns. Enabling `mergeSchema` dynamically updates the table metadata. `CHECK` constraints enforce business rules (e.g., `amount > 0`) at the transactional storage layer.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Demonstrate Schema Enforcement vs. mergeSchema
# MAGIC
# MAGIC Simulate schema collision and resolution via `mergeSchema`.
# COMMAND ----------

# Simulate schema comparison
base_schema = ["order_id", "customer_id", "total_amount"]
new_payload_schema = ["order_id", "customer_id", "total_amount", "discount_code", "loyalty_tier"]

# Check if evolution is required
extra_columns = set(new_payload_schema) - set(base_schema)
print(f"Detected New Upstream Columns: {extra_columns}")

# If mergeSchema=True, target schema evolves to union
evolved_schema = sorted(list(set(base_schema).union(new_payload_schema)))
print(f"Evolved Target Schema: {evolved_schema}")
assert len(evolved_schema) == 5
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Schema Enforcement Default**: Protects downstream BI models from silent data corruption.
# MAGIC - **Controlled Evolution**: Use `.option('mergeSchema', 'true')` to safely append new optional attributes.
# MAGIC - **Storage-Level Constraints**: Add `ALTER TABLE t ADD CONSTRAINT valid_amount CHECK (amount >= 0)` to block bad data permanently.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between `mergeSchema` and `overwriteSchema` in Delta Lake?
# MAGIC 2. How do `CHECK` constraints in Delta Lake compare to traditional RDBMS constraints?
