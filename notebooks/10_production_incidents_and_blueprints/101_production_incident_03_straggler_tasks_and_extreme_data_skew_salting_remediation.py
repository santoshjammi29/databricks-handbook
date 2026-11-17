# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 101. Production Incident 03: Straggler Tasks & Extreme Data Skew Salting Remediation
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 100-node cluster executes a join between transactions and merchant dimensions. 99 out of 100 tasks finish in 5 seconds, but Task 100 hangs for 55 minutes due to extreme key skew on 'Amazon' merchant ID.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Diagnose the 99% straggler task using the Spark UI, inspect shuffle distribution percentiles, and implement two-phase deterministic key salting to redistribute skewed keys uniformly.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC When one key has millions of records while other keys have hundreds, standard hash partitioning routes all millions of records to a single worker core. Key salting appends a pseudo-random suffix to the skewed key, distributing it across $N$ worker buckets.
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
# MAGIC ### 1. Two-Phase Deterministic Key Salting Implementation
# MAGIC
# MAGIC Salt the large skewed DataFrame and replicate the lookup table across salt buckets.
# COMMAND ----------

# Two-phase key salting pattern
SALT_FACTOR = 16

# 1. Salt large skewed table
df_large_salted = spark.createDataFrame([("AMAZON", 100.0), ("AMAZON", 250.0), ("EBAY", 45.0)], ["merchant", "amount"]) \
    .withColumn("_salt", F.concat(F.col("merchant"), F.lit("_"), F.floor(F.rand() * SALT_FACTOR)))

# 2. Replicate dimension table across all salt factors
df_dim = spark.createDataFrame([("AMAZON", "Retail"), ("EBAY", "Auction")], ["merchant", "category"])
df_dim_replicated = df_dim \
    .withColumn("_salts", F.array([F.lit(i) for i in range(SALT_FACTOR)])) \
    .withColumn("_sub_salt", F.explode("_salts")) \
    .withColumn("_salt", F.concat(F.col("merchant"), F.lit("_"), F.col("_sub_salt"))) \
    .drop("_salts", "_sub_salt")

# 3. Uniform join on salted key
df_joined = df_large_salted.join(df_dim_replicated, on="_salt").drop("_salt")
df_joined.show()
assert df_joined.count() == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Straggler Diagnostic**: Check Spark UI Task Duration percentiles: if Max >> Median, you have severe skew.
# MAGIC - **AQE Skew Join**: Verify `spark.sql.adaptive.skewJoin.enabled = true` is active.
# MAGIC - **Two-Phase Salting**: Use deterministic salting when AQE cannot split non-equi joins or custom transformations.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Adaptive Query Execution (AQE) detect and resolve join skew at runtime?
# MAGIC 1. What is the mathematical principle behind key salting in distributed hash joins?
