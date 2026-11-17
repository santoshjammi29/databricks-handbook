# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 047. Production Job Execution: Run As Service Principal & Zero-Interactive Identity
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A critical production job failed because the data engineer who configured it transferred to another team and their user account was deactivated.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure production Lakeflow Jobs to execute under a dedicated Service Principal identity (`run_as`), eliminating personal user identity dependencies.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The `run_as` setting decouples job ownership from human users. Production jobs should run as a Service Principal identity authenticated via OAuth M2M tokens, ensuring unbroken pipeline operations.
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
# MAGIC ### 1. Configure Run As Service Principal Specification
# MAGIC
# MAGIC Define DABs and Job JSON properties enforcing Service Principal ownership.
# COMMAND ----------

job_security_spec = {
    "job_name": "prod_financial_reconciliation",
    "run_as": {
        "service_principal_name": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4"
    },
    "permissions": [
        {"service_principal_name": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4", "level": "IS_OWNER"},
        {"group_name": "data-platform-engineers", "level": "CAN_MANAGE_RUN"}
    ]
}

print(f"Job Owner Service Principal: {job_security_spec['run_as']['service_principal_name']}")
assert "service_principal_name" in job_security_spec["run_as"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Business Continuity**: Service Principals never leave the company or reset personal passwords.
# MAGIC - **Least Privilege**: Grant Service Principals exact permissions on Unity Catalog catalogs and schemas.
# MAGIC - **Audit Trail**: Security teams can distinctly track automated vs. interactive queries in `system.access.audit`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you assign a Service Principal as the owner of a Databricks Workflow?
# MAGIC 1. What privileges in Unity Catalog are required for a Service Principal to execute a multi-task job?
