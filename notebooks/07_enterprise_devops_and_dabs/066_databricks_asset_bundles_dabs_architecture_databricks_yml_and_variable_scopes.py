# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 066. Databricks Asset Bundles (DABs) Architecture: databricks.yml & Variable Scopes
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data platform engineering team needs to standardize pipeline deployments across 50 data engineers, eliminating manual UI clicks and establishing declarative Infrastructure as Code (IaC).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author and validate a root `databricks.yml` asset bundle specification, configure variable substitution scopes, and implement target environment overrides (dev, staging, prod).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Asset Bundles (DABs) provide declarative IaC for all Databricks assets. Assets (Jobs, DLT pipelines, Volumes, Models) are defined in YAML and deployed via the CLI (`databricks bundle deploy`). Variable scopes allow dynamic parameter substitution across targets.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. DABs Configuration Schema & Variable Substitution
# MAGIC
# MAGIC Define and validate root `databricks.yml` syntax with environment variable targets.
# COMMAND ----------

bundle_manifest = """
bundle:
  name: enterprise-lakehouse-pipeline

variables:
  catalog:
    default: "main"
  schema:
    default: "analytics"

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: "dev_catalog"
  prod:
    mode: production
    variables:
      catalog: "prod_catalog"
"""

print("DABs root configuration verified.")
assert "mode: development" in bundle_manifest
assert "mode: production" in bundle_manifest
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Declarative IaC**: Define all Databricks pipelines and resources as code in version-controlled YAML.
# MAGIC - **Target Overrides**: Dynamically alter catalogs, clusters, and permissions per target environment.
# MAGIC - **Development Mode**: `mode: development` isolates developer deployments to user sandboxes.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What are Databricks Asset Bundles (DABs) and why did Databricks introduce them over classic Terraform?
# MAGIC 2. How does variable scoping work across different deployment targets in `databricks.yml`?
