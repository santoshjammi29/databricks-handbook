# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 002. Databricks Workspace Topologies: Multi-Workspace Hub-and-Spoke & Private Link
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Architect`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A multinational enterprise operates four business units across Dev, Staging, and Prod. Architects must design a multi-workspace hub-and-spoke topology preventing cross-environment data leakage while sharing central Unity Catalog metadata.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define the programmatic catalog and workspace binding rules that enforce environment boundaries across dev and prod workspaces while isolating networking via Private Link.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC A single Unity Catalog Metastore per region binds to multiple workspaces. Workspace binding (`CATALOG BINDING`) allows administrators to restrict production catalogs strictly to production workspaces.
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
# MAGIC ### 1. Define Workspace Catalog Binding Hierarchy
# MAGIC
# MAGIC Simulate and validate workspace catalog bindings using Unity Catalog information schema and metadata commands.
# COMMAND ----------

# Establish catalog binding rules across workspaces
workspace_registry = [
    {"workspace_id": "1001", "name": "workspace-dev", "allowed_catalogs": ["dev_lakehouse", "sandbox"]},
    {"workspace_id": "1002", "name": "workspace-staging", "allowed_catalogs": ["staging_lakehouse", "dev_lakehouse"]},
    {"workspace_id": "1003", "name": "workspace-prod", "allowed_catalogs": ["prod_lakehouse"]}
]

def validate_workspace_access(workspace_id: str, target_catalog: str) -> bool:
    for ws in workspace_registry:
        if ws["workspace_id"] == workspace_id:
            return target_catalog in ws["allowed_catalogs"]
    return False

# Assert dev workspace cannot read production catalog
assert not validate_workspace_access("1001", "prod_lakehouse"), "Access Breach: Dev accessed Prod Catalog!"
assert validate_workspace_access("1003", "prod_lakehouse"), "Prod catalog must be accessible in Prod Workspace!"
print("Workspace binding validation passed successfully.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Regional Metastore Binding**: One Metastore per region connects to multiple workspaces.
# MAGIC - **Catalog Isolation**: Bind production catalogs exclusively to production workspaces to avoid dev accidental writes.
# MAGIC - **Dual Private Link**: Front-end Private Link for user access; Back-end Private Link for compute plane.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you design environment isolation (Dev/Test/Prod) in Unity Catalog?
# MAGIC 1. What is the difference between Front-end Private Link and Back-end Private Link in Databricks?
