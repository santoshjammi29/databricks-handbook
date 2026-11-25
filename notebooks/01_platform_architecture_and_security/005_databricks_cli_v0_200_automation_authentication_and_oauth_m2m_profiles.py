# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 005. Databricks CLI v0.200+ Automation, Authentication & OAuth M2M Profiles
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise DevOps team is replacing deprecated legacy Python CLI tools with the modern Go-based Databricks CLI v0.200+ across all Jenkins and GitHub Actions runners using OAuth Machine-to-Machine (M2M) authentication.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the programmatic setup of Databricks CLI authentication profiles, token generation, and command execution using Service Principal client credentials.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks CLI v0.200+ is rewritten in Go for high performance. It standardizes on OAuth M2M tokens generated from Azure Service Principals or AWS OIDC roles, eliminating insecure static personal access tokens (PATs).
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Configure OAuth M2M Profile Specification
# MAGIC
# MAGIC Define the `.databrickscfg` configuration block for zero-trust service principal execution.
# COMMAND ----------

# Simulate databrickscfg profile structure
databrickscfg_template = """
[DEFAULT]
host = https://adb-1234567890123456.7.azuredatabricks.net
auth_type = oauth-m2m
client_id = 4f63c679-0db8-40a2-b91a-7b3b7e7136f4
client_secret = {{secrets/sp_tokens/client_secret}}

[PROD_ACCOUNT]
host = https://accounts.azuredatabricks.net
account_id = a1b2c3d4-e5f6-7890-abcd-ef1234567890
auth_type = oauth-m2m
client_id = 4f63c679-0db8-40a2-b91a-7b3b7e7136f4
client_secret = {{secrets/sp_tokens/client_secret}}
"""

print("OAuth M2M profile specification configured.")
assert "auth_type = oauth-m2m" in databrickscfg_template
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Modern CLI Baseline**: Use Go-based CLI v0.200+; legacy pip databricks-cli is deprecated.
# MAGIC - **OAuth M2M Standard**: Service Principals use short-lived OAuth tokens instead of static PATs.
# MAGIC - **Account vs. Workspace**: Separate CLI profiles for account-level operations (metastore, SCIM) and workspace operations.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why are Personal Access Tokens (PATs) prohibited in enterprise production CI/CD?
# MAGIC 2. How does OAuth M2M authentication work between GitHub Actions and Databricks?
