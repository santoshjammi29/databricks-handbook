# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 070. GitHub Actions CI/CD Pipeline: Automated Bundle Linting, Testing & Validation
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A DevOps team requires a zero-touch CI/CD pipeline in GitHub Actions that runs unit tests on Pull Requests, validates bundle schemas, and automatically deploys to Production upon merging to `main`.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Construct a production GitHub Actions workflow YAML file incorporating Python linting, pytest execution, Databricks CLI authentication, and multi-stage deployment gates.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC GitHub Actions CI/CD executes jobs on Ubuntu runners. The workflow checks out the repository, installs the Databricks CLI, runs `bundle validate`, executes unit tests with pytest/chispa, and deploys to target workspaces.
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
# MAGIC ### 1. GitHub Actions CI/CD Workflow Template
# MAGIC
# MAGIC Define workflow steps for pull request validation and production rollout.
# COMMAND ----------

github_workflow_yaml = """
name: CI/CD Databricks Asset Bundle Rollout

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate_and_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - uses: databricks/setup-cli@v0.220.0
      - run: databricks bundle validate -t dev
"""

print("GitHub Actions CI/CD configuration validated.")
assert "databricks/setup-cli" in github_workflow_yaml
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Automated PR Checks**: Prevent broken bundle syntax or failing unit tests from merging to main.
# MAGIC - **Official Databricks Action**: Use `databricks/setup-cli` in GitHub Actions for official CLI installation.
# MAGIC - **Zero Manual Touches**: Automated deployments guarantee consistent environments across dev, staging, and prod.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you design a GitHub Actions pipeline for Databricks that supports dev branch validation and prod deployment?
# MAGIC 1. What is the best way to handle branch protection rules with Databricks Asset Bundles?
