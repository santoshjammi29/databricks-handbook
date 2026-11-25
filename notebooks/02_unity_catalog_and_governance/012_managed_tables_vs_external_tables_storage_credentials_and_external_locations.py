# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 012. Managed Tables vs. External Tables: Storage Credentials & External Locations
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data architecture team must decide which enterprise datasets should be Managed Tables in Unity Catalog vs. External Tables pointing to existing cloud data lake locations.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement and compare Managed and External table creation, verify underlying cloud storage paths, and demonstrate table drop lifecycle differences.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Managed tables have their file lifecycle controlled by Unity Catalog; dropping a managed table deletes both metadata and Parquet data. External tables use an External Location and Storage Credential; dropping an external table removes only catalog metadata, leaving underlying cloud files intact.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Compare Managed vs. External Lifecycle & DDL
# MAGIC
# MAGIC Inspect the DDL and lifecycle behavior of Managed and External assets.
# COMMAND ----------

table_specs = {
    "managed_table": {
        "ddl": "CREATE TABLE prod.silver.orders (id BIGINT, amount DOUBLE);",
        "storage": "Managed by UC in schema root path",
        "drop_behavior": "DELETES metadata AND underlying Parquet files from cloud storage",
        "predictive_optimization": "Fully automated serverless OPTIMIZE & VACUUM"
    },
    "external_table": {
        "ddl": "CREATE TABLE prod.silver.legacy_orders (id BIGINT, amount DOUBLE) LOCATION 'abfss://data@datalake.dfs.core.windows.net/orders';",
        "storage": "Customer-managed external cloud storage path",
        "drop_behavior": "DELETES metadata ONLY; Parquet files remain preserved in cloud storage",
        "predictive_optimization": "Manual or requires explicit storage credential enablement"
    }
}

for name, spec in table_specs.items():
    print(f"[{name.upper()}]\n  DDL: {spec['ddl']}\n  Drop Semantics: {spec['drop_behavior']}\n")

assert "DELETES metadata AND underlying Parquet" in table_specs["managed_table"]["drop_behavior"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Managed Table Default**: Use Managed Tables for new lakehouse assets to leverage automated Predictive Optimization.
# MAGIC - **External Table Use Case**: Use External Tables when existing third-party applications write directly to cloud storage.
# MAGIC - **Storage Credentials**: Both use cloud IAM (Managed Identity / IAM Role) without static access keys.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What happens to the physical data on cloud object storage when a user drops an External Table versus a Managed Table?
# MAGIC 2. How does Unity Catalog authenticate to cloud storage for External Tables?
