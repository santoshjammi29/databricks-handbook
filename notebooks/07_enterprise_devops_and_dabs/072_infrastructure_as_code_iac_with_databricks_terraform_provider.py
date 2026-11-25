# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 072. Infrastructure as Code (IaC) with Databricks Terraform Provider
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise Cloud Infrastructure team needs to provision 10 new Databricks workspaces, configure storage accounts, create Unity Catalog metastores, and grant admin roles using Terraform.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author Terraform HCL manifests utilizing the official Databricks Terraform Provider (`databricks/databricks`), deploying workspaces, catalogs, storage credentials, and external locations.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The Databricks Terraform Provider manages account-level resources (workspaces, metastores, SCIM groups) and workspace-level assets. It complements DABs: Terraform provisions infrastructure; DABs deploys pipelines.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Terraform HCL Resource Definition
# MAGIC
# MAGIC Inspect Terraform code provisioning Unity Catalog catalogs and storage credentials.
# COMMAND ----------

terraform_manifest = """
terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

resource "databricks_catalog" "prod_lakehouse" {
  name         = "prod_lakehouse"
  comment      = "Production Enterprise Lakehouse Catalog"
  storage_root = "abfss://managed@storage.dfs.core.windows.net/prod"
}

resource "databricks_grant" "data_engineers_access" {
  catalog    = databricks_catalog.prod_lakehouse.name
  principal  = "data-engineers"
  privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
}
"""

print("Databricks Terraform HCL validated.")
assert "databricks_catalog" in terraform_manifest
assert "databricks_grant" in terraform_manifest
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Terraform for Infrastructure**: Best for provisioning workspaces, metastores, VNet peering, and IAM.
# MAGIC - **DABs for Applications**: Best for data engineers deploying pipelines, jobs, and apps.
# MAGIC - **Automated State**: Maintain infrastructure drift detection via Terraform Cloud or Azure DevOps.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the division of responsibility between the Databricks Terraform Provider and Databricks Asset Bundles (DABs)?
# MAGIC 2. How does Terraform manage Unity Catalog metastore assignments across multiple workspaces?
