# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 009. Service Principals, SCIM Provisioning & Enterprise Identity Federation
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise identity architect must automate user provisioning from Microsoft Entra ID (Azure AD) and Okta into Databricks using SCIM (System for Cross-domain Identity Management).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define the identity architecture, group mapping model, and Service Principal assignment rules for automated enterprise identity lifecycle management.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Account-level SCIM synchronizes enterprise users and groups from the Identity Provider (IdP) to the Databricks Account Console. Groups are then assigned to specific workspaces, preventing manual user administration in individual workspaces.
# COMMAND ----------

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# Initialize or obtain active SparkSession with Delta Lake & Unity Catalog support
spark = SparkSession.builder \
    .appName("DatabricksHandbook") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. SCIM Group-to-Workspace Synchronization Model
# MAGIC
# MAGIC Simulate identity mapping from Okta/Entra ID to Databricks Account and Workspaces.
# COMMAND ----------

# Identity mapping schema
idp_groups = [
    {"group_name": "data_engineers", "members": 45, "workspaces": ["dev", "staging", "prod"]},
    {"group_name": "bi_analysts", "members": 120, "workspaces": ["staging", "prod"]},
    {"group_name": "data_scientists", "members": 30, "workspaces": ["dev", "staging"]}
]

# Service Principal specification for CI/CD
cicd_sp = {
    "display_name": "sp-github-actions-prod",
    "application_id": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4",
    "roles": ["account_admin", "workspace_admin"],
    "token_type": "OAuth M2M"
}

print(f"Service Principal: {cicd_sp['display_name']} ({cicd_sp['application_id']})")
assert cicd_sp["token_type"] == "OAuth M2M"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Account-Level SCIM**: Provision users and groups centrally at the account level, not per workspace.
# MAGIC - **Service Principals for Automation**: Never run production CI/CD or jobs under human user accounts.
# MAGIC - **Group-Based Access**: Always grant catalog permissions to SCIM groups, never individual users.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does SCIM integration streamline user onboarding and offboarding in Databricks?
# MAGIC 1. What happens to a scheduled production job if its owner leaves the company and their Entra ID account is disabled?
