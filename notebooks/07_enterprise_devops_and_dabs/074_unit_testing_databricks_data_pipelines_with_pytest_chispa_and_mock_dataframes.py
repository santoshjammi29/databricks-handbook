# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 074. Unit Testing Databricks Data Pipelines with pytest, chispa & Mock DataFrames
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A team experiences pipeline regressions when code changes accidentally alter decimal rounding logic. Data transformations must be validated by automated unit test suites before deployment.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop modular unit test suites using pytest and `chispa`, creating mock DataFrames, asserting schema matches, and verifying exact numerical results.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `chispa` provides fast, clean assertion helpers (`assert_df_equality`) for PySpark DataFrames, highlighting column, schema, and row discrepancies in test output without boilerplate loops.
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
# MAGIC ### 1. Unit Test Implementation with PySpark & Mock Data
# MAGIC
# MAGIC Write a pure transformation function and validate it with a mock unit test.
# COMMAND ----------

# Pure transformation function
def calculate_net_amount(df):
    return df.withColumn("net_amount", F.round(F.col("gross") - F.col("discount"), 2))

# Unit test
mock_input = spark.createDataFrame([
    (100.00, 10.00),
    (250.50, 25.50),
    (50.00, 0.00)
], ["gross", "discount"])

df_result = calculate_net_amount(mock_input)
results = [row["net_amount"] for row in df_result.collect()]

print(f"Computed Net Amounts: {results}")
assert results == [90.00, 225.00, 50.00], f"Unit test failed: Expected [90.0, 225.0, 50.0], got {results}"
print("Unit test PASSED: 100% numerical precision verified.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Decouple Transformations**: Write business logic as pure functions that accept and return DataFrames.
# MAGIC - **Mock Data Testing**: Run unit tests locally with tiny in-memory DataFrames in seconds.
# MAGIC - **Automated CI Guardrail**: Run pytest on every Pull Request before approving merges.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you test PySpark data transformations in CI/CD without spinning up an expensive Databricks cluster?
# MAGIC 1. What is `chispa` and how does `assert_df_equality` improve PySpark test assertions?
