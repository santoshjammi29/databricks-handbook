# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 019. Delta Sharing Databricks-to-Databricks: Managed Cross-Account Data Virtualization
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A global conglomerate operates independent Databricks accounts for subsidiaries in Europe and North America. They need to share supplier and inventory tables with zero credential management.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Establish a Databricks-to-Databricks managed sharing topology using metastore sharing identifiers, creating provider and recipient catalogs without bearer token files.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC When both provider and recipient use Databricks with Unity Catalog, Delta Sharing is fully managed. The provider shares data directly using the recipient's global metastore ID (`cloud:region:metastore-id`), completely eliminating manual credential files and token rotation.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Managed Databricks-to-Databricks Sharing Architecture
# MAGIC
# MAGIC Verify metastore sharing identifiers and cross-account catalog binding.
# COMMAND ----------

metastore_id = "azure:eastus2:99a8b7c6-1234-5678-abcd-ef0123456789"
recipient_spec = {
    "name": "emea_subsidiary",
    "sharing_type": "DATABRICKS_TO_DATABRICKS",
    "metastore_id": metastore_id,
    "automatic_lineage": True
}

print(f"Recipient Metastore ID: {recipient_spec['metastore_id']}")
assert recipient_spec["sharing_type"] == "DATABRICKS_TO_DATABRICKS"
assert recipient_spec["automatic_lineage"] is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Token-Less Security**: No manual credential JSON files to manage or rotate.
# MAGIC - **Unified Lineage**: Lineage tracks seamlessly across provider and recipient workspaces.
# MAGIC - **Multi-Cloud Sharing**: Shares data across Azure, AWS, and GCP transparently.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Open Delta Sharing and Databricks-to-Databricks Delta Sharing?
# MAGIC 2. How is data lineage maintained across two separate Databricks accounts in managed Delta Sharing?
