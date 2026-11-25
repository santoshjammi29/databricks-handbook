# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 077. Databricks Apps: Serverless Hosting for Streamlit, Dash, Gradio & FastAPI Applications
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Data scientists and engineers need to deploy interactive data applications (Streamlit for internal FinOps, FastAPI for microservices) directly inside the secure workspace perimeter without managing Kubernetes or cloud VMs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy and configure a serverless Python web application using Databricks Apps, handling port routing, single sign-on (SSO) authentication, and Unity Catalog data access.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Apps provides serverless container hosting for Python web frameworks (Streamlit, Dash, Gradio, Flask, FastAPI). Apps run securely within the workspace, inherit corporate SSO, and connect to Unity Catalog via auto-injected service credentials.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Databricks App Architecture & Component Model
# MAGIC
# MAGIC Inspect the components of a native Databricks App.
# COMMAND ----------

app_components = {
    "app_yaml": "Configuration manifest specifying command, port, and environment variables",
    "requirements_txt": "Python dependencies installed in the serverless container",
    "app_py": "Application source code (Streamlit / FastAPI)",
    "security": "Automatic corporate SSO authentication; users access via workspace URL"
}

for comp, desc in app_components.items():
    print(f"[{comp}]: {desc}")
assert len(app_components) == 4
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Serverless Hosting**: Zero Kubernetes or Docker management; Databricks manages the container fleet.
# MAGIC - **Built-In SSO**: Users authenticate using standard Databricks login; no manual OAuth boilerplate.
# MAGIC - **Zero Egress**: Data stays within the Databricks perimeter, governed by Unity Catalog.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is Databricks Apps and how does it simplify deploying internal data tools compared to standalone web servers?
# MAGIC 2. How does authentication and user identity work in a Databricks App?
