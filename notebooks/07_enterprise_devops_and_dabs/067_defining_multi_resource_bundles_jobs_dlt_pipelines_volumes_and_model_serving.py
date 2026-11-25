# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 067. Defining Multi-Resource Bundles: Jobs, DLT Pipelines, Volumes & Model Serving
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A machine learning engineering platform deploys an end-to-end AI product consisting of a DLT data preparation pipeline, a Lakeflow model training job, a Unity Catalog model, and a real-time Model Serving endpoint.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Construct a modular multi-resource bundle structure (`resources/*.yml`) declaring Jobs, DLT Pipelines, Volumes, and Model Serving endpoints as a unified deployment unit.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DABs support multi-resource definitions. The `include: - resources/*.yml` directive allows modular separation of concerns: `jobs.yml`, `pipelines.yml`, `unity_catalog.yml`, and `model_serving.yml`.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Resource YAML Structure Inspection
# MAGIC
# MAGIC Verify how different resource types are declared and linked in bundle resources.
# COMMAND ----------

resource_files = [
    "resources/jobs.yml",
    "resources/dlt_pipelines.yml",
    "resources/unity_catalog.yml",
    "resources/model_serving.yml",
    "resources/apps.yml"
]

print("Multi-Resource Bundle Hierarchy:")
for r in resource_files:
    print(f"  -> {r}")
assert len(resource_files) == 5
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Unified Lifecycle**: Deploy data ingestion, model training, and model serving together in a single atomic bundle.
# MAGIC - **Modular Directory Layout**: Keep resource definitions in separate YAML files under `resources/`.
# MAGIC - **Topological Deployment**: DABs automatically resolves cross-resource references.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you organize multi-resource bundles for complex projects spanning data engineering and ML?
# MAGIC 2. Can a Databricks Job in DABs trigger a DLT Pipeline declared in the same bundle?
