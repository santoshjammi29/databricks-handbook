# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 080. Foundation Model APIs & Embeddings: bge-large, text-embedding-3 & Serving
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Intermediate`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A natural language search system must convert text documents into high-dimensional numerical vectors (1024 dimensions) using state-of-the-art embedding models with predictable throughput and low cost.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Query Databricks Foundation Model APIs (e.g. `databricks-bge-large-en`), generate dense vector embeddings from text batches, and measure similarity using cosine distance.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Foundation Model APIs provide pay-per-token access to top-tier open models (`bge-large`, `dbrx-instruct`, `llama-3`) hosted securely on serverless Databricks infrastructure. Data never leaves the workspace perimeter.
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
# MAGIC ### 1. Vector Embedding Generation & Cosine Similarity Verification
# MAGIC
# MAGIC Generate vector arrays and compute mathematical cosine similarity.
# COMMAND ----------

import math

# Vector cosine similarity function
def cosine_similarity(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2)

# Simulated 4-dimensional normalized embeddings
query_vec = [0.85, 0.12, 0.45, 0.22]
doc_match_vec = [0.84, 0.15, 0.44, 0.25] # Highly similar document
doc_unrelated_vec = [0.05, 0.92, 0.11, 0.38] # Unrelated document

sim_match = cosine_similarity(query_vec, doc_match_vec)
sim_unrelated = cosine_similarity(query_vec, doc_unrelated_vec)

print(f"Similarity (Target Document): {sim_match:.4f}")
print(f"Similarity (Unrelated Document): {sim_unrelated:.4f}")
assert sim_match > 0.95
assert sim_unrelated < 0.60
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Pay-per-Token Model**: Foundation Model APIs eliminate the cost of keeping dedicated GPU clusters running.
# MAGIC - **Zero Data Egress**: Prompts and embeddings are not logged by external vendors or used for model training.
# MAGIC - **Standard API**: Fully compatible with OpenAI client format (`openai.OpenAI(base_url=...)`).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Pay-per-token Foundation Model APIs and Provisioned Throughput Model Serving?
# MAGIC 1. How do you configure the OpenAI Python SDK to query Databricks-hosted foundation models?
