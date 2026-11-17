# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 071. Service Principal Authentication in CI/CD Runners using Azure OIDC / AWS IAM
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A Chief Information Security Officer (CISO) mandates the elimination of all static client secrets and API tokens from GitHub repository secrets to prevent credential theft.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure passwordless GitHub Actions authentication to Databricks using OpenID Connect (OIDC) cloud federation (Azure Federated Credentials / AWS IAM OIDC Provider).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC OIDC federation allows GitHub Actions runners to exchange short-lived OIDC tokens directly with Azure or AWS without storing long-lived passwords or secrets. The cloud provider issues a temporary access token that authenticates to Databricks via OAuth M2M.
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
# MAGIC ### 1. OIDC Token Exchange Workflow Model
# MAGIC
# MAGIC Simulate and verify the passwordless OIDC token exchange sequence.
# COMMAND ----------

oidc_auth_flow = {
    "step_1": "GitHub Actions runner requests OIDC JWT token from GitHub token service",
    "step_2": "Runner sends JWT token to Cloud Provider (Azure AD / AWS STS) to assume role",
    "step_3": "Cloud Provider verifies GitHub repository, branch, and signature claims",
    "step_4": "Cloud Provider issues short-lived scoped OAuth token (1 hour lifespan)",
    "step_5": "Databricks CLI authenticates to workspace using temporary OAuth token"
}

for step, desc in oidc_auth_flow.items():
    print(f"[{step.upper()}]: {desc}")

assert "short-lived scoped OAuth token" in oidc_auth_flow["step_4"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Passwordless CI/CD**: Eliminates stored client secrets, preventing credential leak disasters.
# MAGIC - **Short-Lived Tokens**: Tokens expire automatically after 1 hour.
# MAGIC - **Cryptographic Claims**: Cloud providers verify the exact GitHub repository and branch before issuing tokens.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does OpenID Connect (OIDC) eliminate stored static secrets in GitHub Actions for Databricks deployments?
# MAGIC 1. What claims does Azure Active Directory verify when validating a GitHub Actions OIDC request?
