# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 079. Databricks Vector Search: Managed Vector Endpoints & Delta Sync Indexes
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise search application requires sub-100ms semantic similarity search over 5 million product catalog descriptions. When new products are added or edited in Delta Lake, the vector index must update automatically.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Provision a Databricks Vector Search endpoint, create a Delta Sync Index that automatically calculates and updates vector embeddings on source Delta table commits, and execute similarity queries.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Vector Search is an enterprise vector database built directly into Unity Catalog. A **Delta Sync Index** continuously tracks changes in a source Delta table via Change Data Feed (CDF), generating embeddings automatically and syncing the vector index in real time.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Delta Sync Index Architecture & Python Configuration
# MAGIC
# MAGIC Configure a continuous vector sync index from a Delta table using `databricks-sdk`.
# COMMAND ----------

vector_index_spec = {
    "endpoint_name": "enterprise_vector_search_endpoint",
    "index_name": "prod_lakehouse.gold.product_vector_index",
    "primary_key": "product_id",
    "index_type": "DELTA_SYNC",
    "source_table": "prod_lakehouse.gold.dim_products",
    "pipeline_type": "CONTINUOUS", # Continuous synchronization from Delta CDF
    "embedding_source_column": "product_description",
    "embedding_model_endpoint_name": "databricks-bge-large-en"
}

print(f"Vector Endpoint: {vector_index_spec['endpoint_name']}")
print(f"Delta Sync Source: {vector_index_spec['source_table']}")
print(f"Auto-Embedding Model: {vector_index_spec['embedding_model_endpoint_name']}")
assert vector_index_spec["index_type"] == "DELTA_SYNC"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Continuous Synchronization**: Delta Sync automatically updates the vector index when Delta tables commit.
# MAGIC - **Zero Embedding Pipelines**: Databricks computes and embeds vectors automatically from text columns.
# MAGIC - **Sub-100ms Latency**: High-performance HNSW index delivers millisecond vector similarity queries.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between a Delta Sync Index and a Direct Vector Access Index in Databricks Vector Search?
# MAGIC 2. How does Delta Sync Index leverage Change Data Feed (CDF) under the hood?
