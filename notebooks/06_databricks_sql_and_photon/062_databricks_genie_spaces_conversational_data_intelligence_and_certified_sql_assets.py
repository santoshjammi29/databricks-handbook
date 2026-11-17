# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 062. Databricks Genie Spaces: Conversational Data Intelligence & Certified SQL Assets
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Executive leaders want to ask business questions in natural language ('What was our top selling product in EMEA last month?') and receive accurate SQL-backed answers with zero hallucination.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure a Databricks Genie Space, define certified SQL assets, author semantic descriptions, and curate trusted benchmarks to guide LLM query generation.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Genie provides a conversational AI interface over Lakehouse data. It combines foundation models with enterprise semantic metadata, Unity Catalog schemas, and certified SQL queries to generate verifiable SQL answers.
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
# MAGIC ### 1. Genie Space Semantic Configuration
# MAGIC
# MAGIC Define trusted tables, column descriptions, and certified SQL benchmark queries for Genie.
# COMMAND ----------

genie_space_config = {
    "space_name": "Executive Sales Intelligence",
    "tables": ["prod_lakehouse.gold.fact_sales", "prod_lakehouse.gold.dim_products"],
    "curated_sql_assets": [
        {
            "question": "What is our definition of monthly recurring revenue (MRR)?",
            "sql": "SELECT SUM(plan_price) FROM subscriptions WHERE status = 'ACTIVE' AND billing_cycle = 'MONTHLY'"
        }
    ],
    "semantic_guidelines": [
        "Always exclude test accounts where email ends with @example.com",
        "Total revenue must always use the 'net_revenue' column, not 'gross_revenue'"
    ]
}

print(f"Genie Space: {genie_space_config['space_name']}")
print(f"Curated Benchmarks: {len(genie_space_config['curated_sql_assets'])}")
print(f"Semantic Guardrails: {len(genie_space_config['semantic_guidelines'])}")
assert len(genie_space_config["semantic_guidelines"]) == 2
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Grounded in SQL**: Genie always presents the exact SQL query executed, allowing human verification.
# MAGIC - **Certified Assets**: Curate approved SQL templates to train Genie on complex proprietary calculations.
# MAGIC - **Zero Hallucination Guardrails**: Semantic instructions instruct the LLM on business logic rules.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Databricks Genie ensure that natural language queries generate mathematically accurate SQL?
# MAGIC 1. What role do certified benchmark queries play in tuning a Genie Space?
