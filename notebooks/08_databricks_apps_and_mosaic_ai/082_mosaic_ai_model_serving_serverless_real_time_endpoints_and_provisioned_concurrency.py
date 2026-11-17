# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 082. Mosaic AI Model Serving: Serverless Real-Time Endpoints & Provisioned Concurrency
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A mobile banking application requires real-time fraud scoring API endpoints responding in under 30 milliseconds with scale-to-zero capabilities to eliminate nighttime idle costs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy an MLflow model to a Mosaic AI Model Serving endpoint, configure scale-to-zero autoscaling, and test REST inference invocations with payload validation.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Mosaic AI Model Serving deploys machine learning models, custom Python code, and LLMs as highly available, serverless microservice REST APIs. It supports automatic scale-to-zero and provisioned concurrency for guaranteed latency.
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
# MAGIC ### 1. Model Serving Endpoint Configuration
# MAGIC
# MAGIC Define serverless model serving endpoint parameters and scaling policies.
# COMMAND ----------

endpoint_config = {
    "name": "fraud-detection-realtime",
    "config": {
        "served_entities": [
            {
                "entity_name": "prod_lakehouse.gold.fraud_detector",
                "entity_version": "2",
                "workload_size": "Small",
                "scale_to_zero_enabled": True
            }
        ],
        "traffic_config": {
            "routes": [{"served_model_name": "fraud_detector-2", "traffic_percentage": 100}]
        }
    }
}

entity = endpoint_config["config"]["served_entities"][0]
print(f"Endpoint: {endpoint_config['name']}")
print(f"Served Entity: {entity['entity_name']} (v{entity['entity_version']})")
print(f"Scale-To-Zero Enabled: {entity['scale_to_zero_enabled']}")
assert entity["scale_to_zero_enabled"] is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Scale-to-Zero**: Endpoints scale down to 0 instances when idle, incurring zero compute cost.
# MAGIC - **Sub-30ms Latency**: Optimized C++ runtime provides real-time scoring for production applications.
# MAGIC - **Canary Deployments**: Split traffic (e.g., 90% v1 / 10% v2) using `traffic_config`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Mosaic AI Model Serving achieve scale-to-zero while minimizing cold start latency?
# MAGIC 1. How do you implement a blue/green or canary rollout on a Model Serving endpoint?
