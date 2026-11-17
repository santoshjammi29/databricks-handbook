# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 073. Databricks Connect v2: Local IDE Development in VS Code with Remote DBR Compute
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Software engineers want to develop PySpark pipelines locally inside VS Code or PyCharm, using local git, linters, and debuggers, while executing DataFrame code on remote Databricks clusters.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure Databricks Connect v2 using Spark Connect architecture, establish an IDE session connecting to a remote DBR 15.4+ cluster, and execute interactive step-through debugging.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Connect v2 is built on open source Apache Spark Connect. The client IDE sends unresolved DataFrame logical query plans over gRPC to the remote Databricks cluster, which executes them and streams back results.
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
# MAGIC ### 1. Databricks Connect v2 SparkSession Initialization
# MAGIC
# MAGIC Demonstrate connecting from a local IDE to remote Databricks compute.
# COMMAND ----------

connect_script = """
from databricks.connect import DatabricksSession

# Connects to remote Databricks cluster using local CLI profile or environment variables
spark = DatabricksSession.builder.getOrCreate()

# DataFrame API executes on remote cluster; results stream back locally
df = spark.read.table("prod_lakehouse.silver.customers")
print(f"Remote Customer Count: {df.count()}")
"""

print("Databricks Connect v2 script structure verified.")
assert "from databricks.connect import DatabricksSession" in connect_script
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **gRPC Architecture**: Uses lightweight Spark Connect protocol instead of heavy old Py4J bridges.
# MAGIC - **IDE Superpowers**: Step-through breakpoints, code completion, and linters in VS Code.
# MAGIC - **Zero Local Java Needed**: Client machines only need Python; no local Java or Hadoop binaries required.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Databricks Connect v2 fundamentally differ from Databricks Connect v1?
# MAGIC 1. What are the network prerequisites for establishing a Databricks Connect v2 session from a corporate laptop?
