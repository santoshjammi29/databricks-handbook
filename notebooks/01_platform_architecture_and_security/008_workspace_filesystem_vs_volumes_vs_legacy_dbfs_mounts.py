# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 008. Workspace Filesystem (/Workspace) vs. Volumes (/Volumes) vs. Legacy DBFS Mounts
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A lakehouse migration project must eliminate legacy DBFS mounts (`/mnt/raw_data`) and transition all data pipelines to Unity Catalog Volumes (`/Volumes`) and Workspace Files (`/Workspace`).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Provide a complete migration mapping and operational script comparing file access semantics across `/Workspace`, `/Volumes`, and DBFS root.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Legacy DBFS mounts (`/mnt/`) expose security holes because all users on a shared cluster share the mount's credentials. Unity Catalog Volumes (`/Volumes/catalog/schema/volume`) enforce fine-grained governance for unstructured and semi-structured files. `/Workspace` stores code, repos, and lightweight configs.
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
# MAGIC ### 1. Path Resolution & Storage Routing Matrix
# MAGIC
# MAGIC Map file path semantics to their underlying storage boundaries.
# COMMAND ----------

storage_mapping = {
    "/Workspace/Users/user@company.com/project/config.json": {
        "tier": "Workspace Filesystem",
        "purpose": "Source code, repo files, small JSON configs (< 500 MB)",
        "governed_by": "Workspace Access Control Lists (ACLs)"
    },
    "/Volumes/prod_lakehouse/raw_landing/invoices/2026_01.pdf": {
        "tier": "Unity Catalog Volume",
        "purpose": "Unstructured enterprise files (PDFs, images, CSVs, audio)",
        "governed_by": "Unity Catalog Grants (READ/WRITE VOLUME)"
    },
    "/mnt/legacy_adls/orders/": {
        "tier": "Legacy DBFS Mount",
        "purpose": "DEPRECATED: Security risk; bypasses Unity Catalog governance",
        "governed_by": "Static mount tokens / SPN"
    }
}

for path, meta in storage_mapping.items():
    print(f"Path: {path}\n  -> Tier: {meta['tier']}\n  -> Governance: {meta['governed_by']}\n")

assert "DEPRECATED" in storage_mapping["/mnt/legacy_adls/orders/"]["purpose"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Deprecate `/mnt/`**: Legacy mounts lack Unity Catalog audit trails and fine-grained access control.
# MAGIC - **Use `/Volumes/`**: For raw files, PDFs, model weights, and semi-structured data.
# MAGIC - **Use `/Workspace/`**: For project scripts, requirements.txt, and local Python modules.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why are DBFS root mounts (`/mnt/`) deprecated in modern Databricks environments?
# MAGIC 1. How do POSIX file operations (`open()`, `os.listdir()`) work on Unity Catalog Volumes?
