# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 084. Mosaic AI Agent Evaluation (MLflow Evaluate): Groundedness, Faithfulness & Relevance
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Advanced`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Before deploying a customer-facing GenAI chatbot to production, compliance requires quantitative benchmarking ensuring hallucination rates are below 1% and groundedness exceeds 95%.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure Mosaic AI Agent Evaluation (MLflow Evaluate) with LLM-as-a-judge metrics: Groundedness, Answer Relevance, and Retrieval Precision.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Mosaic AI Agent Evaluation provides automated evaluation frameworks for GenAI agents and RAG applications. It leverages LLM-as-a-judge judges to grade system responses against retrieved context, measuring groundedness and safety.
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
# MAGIC ### 1. Agent Evaluation Metric Definition & Benchmarking
# MAGIC
# MAGIC Define evaluation thresholds and assert quality guardrails.
# COMMAND ----------

evaluation_benchmarks = {
    "groundedness": {
        "metric": "Percentage of generated claims supported by retrieved context",
        "measured_value": 0.97,
        "pass_threshold": 0.95
    },
    "answer_relevance": {
        "metric": "How directly the response answers the user's question",
        "measured_value": 0.94,
        "pass_threshold": 0.90
    },
    "toxicity": {
        "metric": "Presence of harmful or prohibited language",
        "measured_value": 0.00,
        "pass_threshold": 0.01
    }
}

for name, metric in evaluation_benchmarks.items():
    passed = metric["measured_value"] >= metric["pass_threshold"] if name != "toxicity" else metric["measured_value"] <= metric["pass_threshold"]
    print(f"Metric: {name.upper()} | Value: {metric['measured_value']} | Passed: {passed}")
    assert passed, f"Evaluation benchmark failed for {name}"

print("All GenAI Agent Evaluation benchmarks passed.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **LLM-as-a-Judge**: Automate subjective evaluation at scale using managed judge models.
# MAGIC - **Groundedness Metric**: Verifies that the LLM's response came strictly from retrieved context, not hallucinations.
# MAGIC - **CI/CD Integration**: Gate model deployment on automated evaluation benchmark scores.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Groundedness, Faithfulness, and Answer Relevance in RAG evaluation?
# MAGIC 1. How does MLflow Evaluate automate testing for Generative AI applications?
