# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 067. Defining Multi-Resource Bundles: Jobs, DLT Pipelines, Volumes & Model Serving
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A machine learning engineering platform deploys an end-to-end AI product consisting of a DLT data preparation pipeline, a Lakeflow model training job, a Unity Catalog model, and a real-time Model Serving endpoint.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Parse modular multi-resource bundle specs (`resources/*.yml`) declaring Jobs, Pipelines, and Model Serving endpoints, and verify cross-resource DAG references with Spark SQL.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DABs compose complex platforms using modular `include: - resources/*.yml` files. Validating cross-resource interpolations (e.g., `${resources.pipelines.etl.id}`) guarantees no broken task references enter production.
# COMMAND ----------

import yaml
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Resource YAML Parsing & Spark DAG Referential Integrity Check
# MAGIC
# MAGIC Parse YAML resource maps for jobs, pipelines, and serving endpoints, load them into Spark SQL views, and prove every cross-resource task link resolves cleanly.
# COMMAND ----------

jobs_yml = """
resources:
  jobs:
    ml_release_job:
      tasks:
        - task_key: run_etl_pipeline
          pipeline_task:
            pipeline_id: "etl_silver_pipeline"
        - task_key: train_churn_model
          depends_on:
            - task_key: run_etl_pipeline
        - task_key: refresh_serving_endpoint
          depends_on:
            - task_key: train_churn_model
          serving_target: "churn_realtime_endpoint"
"""
other_resources_yml = """
resources:
  pipelines:
    etl_silver_pipeline:
      target: "gold"
  model_serving_endpoints:
    churn_realtime_endpoint:
      entity: "prod_lakehouse.gold.churn_model"
"""

job_tree = yaml.safe_load(jobs_yml)["resources"]["jobs"]["ml_release_job"]["tasks"]
res_tree = yaml.safe_load(other_resources_yml)["resources"]

known_assets = set(res_tree["pipelines"].keys()) | set(res_tree["model_serving_endpoints"].keys()) | {
    t["task_key"] for t in job_tree
}

edge_rows = []
for task in job_tree:
    tk = task["task_key"]
    for dep in task.get("depends_on", []):
        edge_rows.append((tk, "task_dep", dep["task_key"]))
    if "pipeline_task" in task:
        edge_rows.append((tk, "pipeline_ref", task["pipeline_task"]["pipeline_id"]))
    if "serving_target" in task:
        edge_rows.append((tk, "serving_ref", task["serving_target"]))

edges_df = spark.createDataFrame(edge_rows, ["source_task", "link_type", "target_ref"])
edges_df.createOrReplaceTempView("bundle_edges")
known_df = spark.createDataFrame([(k,) for k in sorted(known_assets)], ["asset_id"])
known_df.createOrReplaceTempView("bundle_assets")

dangling_count = spark.sql("""
    SELECT e.*
    FROM bundle_edges e
    LEFT ANTI JOIN bundle_assets a ON e.target_ref = a.asset_id
""").count()

total_links = edges_df.count()
print(f"Validated {total_links} bundle resource links; dangling references: {dangling_count}")
assert total_links == 4 and dangling_count == 0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Unified Lifecycle**: Deploy data ingestion, model training, and model serving together in a single atomic bundle.
# MAGIC - **Modular Directory Layout**: Keep resource definitions in separate YAML files under `resources/`.
# MAGIC - **Topological Validation**: Cross-check task dependencies and pipeline/serving references in CI before deployment.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you organize multi-resource bundles for complex projects spanning data engineering and ML?
# MAGIC 2. Can a Databricks Job in DABs trigger a DLT Pipeline declared in the same bundle?
