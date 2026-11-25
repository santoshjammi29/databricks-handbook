# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 075. Python Wheel Packaging, UC Volume Deployment & Dependency Pinning
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise maintains a proprietary Python library for encryption and financial accounting. The library must be packaged as a Python Wheel (`.whl`), stored securely in a Unity Catalog Volume, and installed on production jobs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Package Python code into a wheel distribution using `setuptools`/`build`, upload to a Unity Catalog Volume, and attach the wheel library to a Lakeflow Job cluster.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Unity Catalog Volumes provide secure, governed storage for compiled Python Wheels and JARs. Attaching libraries via `/Volumes` eliminates external internet pip downloads on compute nodes, enforcing secure air-gapped environments.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Python Wheel Bundle Specification
# MAGIC
# MAGIC Define how Python wheels are declared as libraries in Databricks Asset Bundles.
# COMMAND ----------

job_with_wheel_spec = {
    "task_key": "run_financial_model",
    "libraries": [
        {"whl": "/Volumes/prod_lakehouse/libraries/wheels/finance_core-1.2.0-py3-none-any.whl"}
    ],
    "python_wheel_task": {
        "package_name": "finance_core",
        "entry_point": "run_accounting_audit",
        "parameters": ["--fiscal-year", "2026"]
    }
}

print(f"Wheel Location: {job_with_wheel_spec['libraries'][0]['whl']}")
print(f"Package Entrypoint: {job_with_wheel_spec['python_wheel_task']['package_name']}.{job_with_wheel_spec['python_wheel_task']['entry_point']}")
assert job_with_wheel_spec["libraries"][0]["whl"].startswith("/Volumes/")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Air-Gapped Compliance**: Storing wheels in UC Volumes prevents cluster startup failures from PyPI downtime.
# MAGIC - **Version Immutability**: Pin exact wheel version numbers (`finance_core-1.2.0.whl`) to avoid drift.
# MAGIC - **Clean Separation**: Code logic lives in standard Python packages; jobs simply invoke entry points.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why should enterprise production pipelines prefer Python Wheels over raw notebooks in Databricks?
# MAGIC 2. How do Unity Catalog Volumes improve library security compared to legacy DBFS library installations?
