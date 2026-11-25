# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 081. MLflow 2.15+ in Unity Catalog: Tracking Runs, Signatures & 3-Level Model Registry
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A machine learning team must govern models across multiple workspaces, tracking training data lineage, model evaluation metrics, and registering models under the 3-level namespace (`catalog.schema.model`).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Train a model, log metrics and artifacts with MLflow 2.15+, enforce strict model input/output signatures, and register the model into Unity Catalog.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC MLflow in Unity Catalog replaces the legacy workspace-scoped Model Registry. Models are governed as first-class Unity Catalog assets with 3-level naming, fine-grained access grants, and end-to-end data lineage from training Delta tables.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. MLflow Tracking & Unity Catalog Model Registration
# MAGIC
# MAGIC Log an MLflow run with model signature and register to Unity Catalog.
# COMMAND ----------

mlflow_uc_spec = {
    "experiment_name": "/Users/ml_engineer/churn_prediction",
    "registered_model_name": "prod_lakehouse.gold.customer_churn_model",
    "model_signature": {
        "inputs": "[{'name': 'account_age_days', 'type': 'integer'}, {'name': 'avg_monthly_spend', 'type': 'double'}]",
        "outputs": "[{'type': 'double'}]"
    },
    "metrics_logged": {"rmse": 0.042, "r2": 0.89, "auc": 0.94}
}

print(f"Registered Model: {mlflow_uc_spec['registered_model_name']}")
print(f"Target Accuracy (AUC): {mlflow_uc_spec['metrics_logged']['auc']}")
parts = mlflow_uc_spec["registered_model_name"].split(".")
assert len(parts) == 3, "Model name must follow catalog.schema.model in Unity Catalog!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **3-Level Model Naming**: Register models in Unity Catalog (`catalog.schema.model_name`).
# MAGIC - **Model Signatures**: Enforce input/output column types to prevent runtime prediction errors.
# MAGIC - **Lineage Tracking**: Unity Catalog automatically links the model to the exact Delta table versions used during training.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does the Unity Catalog Model Registry differ from the legacy workspace-scoped MLflow Model Registry?
# MAGIC 2. What is a Model Signature in MLflow and why is it critical for production model serving?
