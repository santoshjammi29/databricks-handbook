# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 083. Enterprise RAG Architecture: Semantic Chunking, Dense Vector + Sparse BM25 Search
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Architect`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A legal firm builds an AI research assistant over 500,000 regulatory documents. Semantic vector search alone fails to match exact legal clause codes, requiring hybrid search with BM25 keyword matching.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Architect an enterprise Retrieval-Augmented Generation (RAG) pipeline incorporating semantic text chunking, hybrid search (dense embeddings + sparse BM25), and cross-encoder re-ranking.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Hybrid search combines dense vector embeddings (which capture conceptual meaning) with sparse lexical keywords like BM25 (which capture exact terms, acronyms, and product IDs). A re-ranker model then scores the combined candidates.
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
# MAGIC ### 1. Hybrid Retrieval Scoring Model
# MAGIC
# MAGIC Simulate combining dense semantic scores with sparse lexical scores.
# COMMAND ----------

def hybrid_score(dense_sim: float, sparse_bm25_norm: float, alpha: float = 0.7) -> float:
    # Alpha balances dense semantic weight vs sparse lexical weight
    return (alpha * dense_sim) + ((1.0 - alpha) * sparse_bm25_norm)

# Document 1: Good conceptual match, but lacks exact clause ID
doc1_dense = 0.92
doc1_sparse = 0.20
score_doc1 = hybrid_score(doc1_dense, doc1_sparse, alpha=0.6)

# Document 2: Moderate semantic match, but has EXACT legal clause ID
doc2_dense = 0.78
doc2_sparse = 0.95
score_doc2 = hybrid_score(doc2_dense, doc2_sparse, alpha=0.6)

print(f"Hybrid Score Doc 1: {score_doc1:.4f}")
print(f"Hybrid Score Doc 2 (Exact Keyword): {score_doc2:.4f}")
assert score_doc2 > score_doc1, "Hybrid search correctly elevated exact legal clause match!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Hybrid Search Standard**: Combine dense vector search with sparse keyword search for robust enterprise RAG.
# MAGIC - **Semantic Chunking**: Chunk documents on structural boundaries (headers, paragraphs) rather than raw token counts.
# MAGIC - **Re-ranking Stage**: Run top 50 hybrid candidates through a cross-encoder to select the final top 5 context chunks.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why does pure vector embedding search often fail on domain-specific acronyms and part numbers?
# MAGIC 1. How does Reciprocal Rank Fusion (RRF) combine dense and sparse search rankings?
