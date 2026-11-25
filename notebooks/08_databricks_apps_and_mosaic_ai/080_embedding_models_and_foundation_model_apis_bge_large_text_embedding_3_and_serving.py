# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 080. Foundation Model APIs & Embeddings: bge-large, text-embedding-3 & Serving
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A natural language search system must convert text documents into high-dimensional numerical vectors (1024 dimensions) using state-of-the-art embedding models with predictable throughput and low cost.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Store document vector embeddings inside a Delta table (`ARRAY<DOUBLE>`) and compute scalable cosine similarity across catalog records directly in Spark SQL using built-in higher-order array functions (`arrays_zip`, `aggregate`).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC While Databricks Foundation Model APIs generate dense embeddings serverlessly (`databricks-bge-large-en`), downstream similarity scoring and evaluation over Delta tables scale effortlessly via distributed Spark SQL higher-order functions without Python UDF serialization.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Distributed Cosine Similarity over Delta Embeddings via Spark SQL
# MAGIC
# MAGIC Persist vector arrays in a Delta table and rank document matches against a query embedding vector using pure vectorized Spark SQL expressions.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_080_", dir=globals().get("HANDBOOK_TMP_DIR")))
vec_path = str(lab_dir / "product_embeddings")

docs = [
    ("doc_match", "Enterprise Delta Lake ACID Storage", [0.84, 0.15, 0.44, 0.25]),
    ("doc_partial", "Databricks Workflows Job Retries", [0.55, 0.45, 0.30, 0.20]),
    ("doc_unrelated", "SAML Single Sign-On Identity Groups", [0.05, 0.92, 0.11, 0.38]),
]
spark.createDataFrame(docs, ["doc_id", "title", "embedding"]).write.format("delta").save(vec_path)
spark.sql(f"CREATE TABLE t080_vectors USING DELTA LOCATION '{vec_path}'")

ranked_df = spark.sql("""
    WITH q AS (
        SELECT array(0.85, 0.12, 0.45, 0.22) AS query_vec
    ),
    scored AS (
        SELECT
            v.doc_id,
            v.title,
            aggregate(arrays_zip(q.query_vec, v.embedding), 0.0D, (acc, x) -> acc + x.query_vec * x.embedding) AS dot_prod,
            sqrt(aggregate(q.query_vec, 0.0D, (acc, x) -> acc + x * x)) AS norm_q,
            sqrt(aggregate(v.embedding, 0.0D, (acc, x) -> acc + x * x)) AS norm_v
        FROM t080_vectors v
        CROSS JOIN q
    )
    SELECT doc_id, title, ROUND(dot_prod / (norm_q * norm_v), 4) AS cosine_similarity
    FROM scored
    ORDER BY cosine_similarity DESC
""")

scores = {r["doc_id"]: r["cosine_similarity"] for r in ranked_df.collect()}
top_id = ranked_df.first()["doc_id"]
print(f"Cosine Similarity Ranking: {scores} (top={top_id})")
assert top_id == "doc_match"
assert scores["doc_match"] > 0.99 and scores["doc_unrelated"] < 0.60
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Pay-per-Token Model**: Foundation Model APIs generate embeddings without dedicated GPU cluster costs.
# MAGIC - **Vectorized Spark Scoring**: Native `aggregate` / `arrays_zip` evaluates similarity cleanly inside Catalyst without slow Python UDFs.
# MAGIC - **Zero Data Egress**: Embeddings stored directly in Delta tables inherit full Unity Catalog governance.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between Pay-per-token Foundation Model APIs and Provisioned Throughput Model Serving?
# MAGIC 2. How do you configure the OpenAI Python SDK to query Databricks-hosted foundation models?
