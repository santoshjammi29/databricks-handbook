# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 015. Dynamic Column Masking for PII Protection and Compliance
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A retail bank must protect customer Personally Identifiable Information (PII) such as Social Security Numbers (SSN) and credit card numbers. Non-privileged analysts should see only the last four digits.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define a dynamic column masking function in SQL, bind it to a table column, and verify that non-privileged queries receive redacted values while authorized payroll managers see plaintext.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Dynamic Column Masking functions evaluate at query runtime. Non-privileged users receive masked strings (e.g., `XXX-XX-1234` or cryptographic hashes), while privileged roles see the original raw values.
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
# MAGIC ### 1. Implement Dynamic Column Masking Function
# MAGIC
# MAGIC Create masking logic redacting sensitive strings based on caller privileges.
# COMMAND ----------

def mask_national_id(raw_id: str, is_privileged: bool) -> str:
    if is_privileged:
        return raw_id
    if not raw_id or len(raw_id) < 4:
        return "REDACTED"
    return f"XXX-XX-{raw_id[-4:]}"

# Test masking logic
raw_ssn = "123-45-6789"
assert mask_national_id(raw_ssn, is_privileged=True) == "123-45-6789"
assert mask_national_id(raw_ssn, is_privileged=False) == "XXX-XX-6789"
print(f"Privileged View: {mask_national_id(raw_ssn, True)}")
print(f"Masked Analyst View: {mask_national_id(raw_ssn, False)}")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **In-Place Protection**: Column masking protects data in-place without altering the underlying Parquet files.
# MAGIC - **Role Redaction**: Combine with `IS_ACCOUNT_GROUP_MEMBER()` for fine-grained role-based unmasking.
# MAGIC - **Compliance Ready**: Satisfies GDPR, HIPAA, and CCPA data privacy and pseudonymization standards.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Can a dynamic column mask be applied to non-string columns (e.g., decimal salaries or date of birth)?
# MAGIC 1. What happens if an unauthorized user attempts to filter on a masked column (`WHERE ssn = '123-45-6789'`)?
