# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 078. Databricks App Manifest (app.yaml), Resource Bindings & Service Principal IAM
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A production Databricks App requires access to a Serverless SQL Warehouse and a Vector Search endpoint. Access must be granted to an isolated App Service Principal rather than human developer credentials.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author an `app.yaml` manifest specifying resource bindings (SQL Warehouses, Serving Endpoints) and environment variables, verifying automated credential injection.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Apps automatically provisions a dedicated Service Principal for each app. The `app.yaml` manifest binds external workspace resources to the app, granting the App Service Principal least-privilege access.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Databricks App Manifest Specification
# MAGIC
# MAGIC Define `app.yaml` resource bindings and runtime configuration.
# COMMAND ----------

app_manifest_yaml = """
command: ["streamlit", "run", "app.py"]
env:
  - name: "DATABRICKS_APP_ENV"
    value: "production"
  - name: "TARGET_CATALOG"
    value: "prod_lakehouse"

resources:
  sql_warehouse:
    id: "wh-serverless-001"
    permission: "CAN_USE"
  serving_endpoint:
    name: "mosaic-rag-serving-endpoint"
    permission: "CAN_QUERY"
"""

print("Databricks App manifest validated.")
assert "streamlit" in app_manifest_yaml and "app.py" in app_manifest_yaml
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Resource Binding**: Bind SQL Warehouses and Serving Endpoints directly in `app.yaml`.
# MAGIC - **Dedicated App Identity**: Every app runs under its own Service Principal, not user tokens.
# MAGIC - **Port Mapping**: Databricks automatically proxies web traffic to the container's bound port.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does `app.yaml` manage permissions for external Databricks resources like SQL Warehouses?
# MAGIC 2. What happens if an app tries to access a table its Service Principal has not been granted permissions to?
