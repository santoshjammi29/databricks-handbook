# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 083. Enterprise RAG Architecture: Semantic Chunking, Dense Vector + Sparse BM25 Search
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Architect` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A legal firm builds an AI research assistant over 500,000 regulatory documents. Semantic vector search alone fails to match exact legal clause codes, requiring hybrid search with BM25 keyword matching.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute hybrid retrieval scoring (`alpha * dense_cosine + (1 - alpha) * sparse_keyword`) over a Delta chunk store in Spark SQL and prove exact legal identifiers (`Clause 409-B`) outrank generic semantic matches.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Pure dense vector search captures meaning but can dilute exact part numbers, SKUs, or legal clause identifiers. Blending dense cosine similarity with sparse keyword scoring ensures exact identifiers rank #1 before cross-encoder reranking.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Hybrid Retrieval Scoring (Dense Cosine + Sparse Lexical Term) in Spark SQL
# MAGIC
# MAGIC Store document chunks + normalized embeddings in Delta, score a user query (`Clause 409-B termination penalty`) via Spark SQL hybrid fusion, and assert exact clause match wins.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_083_", dir=globals().get("HANDBOOK_TMP_DIR")))
rag_path = str(lab_dir / "legal_rag_chunks")

chunks = [
    ("chunk_1_conceptual", "General overview of enterprise contract termination penalties.", [0.92, 0.39]),
    ("chunk_2_exact", "Mandatory SLA breach liability under Clause 409-B governing early exit.", [0.78, 0.62]),
]
spark.createDataFrame(chunks, ["chunk_id", "content", "dense_vec"]).write.format("delta").save(rag_path)
spark.sql(f"CREATE TABLE t083_chunks USING DELTA LOCATION '{rag_path}'")

ranked_df = spark.sql("""
    WITH scored AS (
        SELECT
            chunk_id,
            ROUND((0.99 * element_at(dense_vec, 1) + 0.14 * element_at(dense_vec, 2)), 4) AS dense_score,
            CASE WHEN content LIKE '%Clause 409-B%' THEN 0.95 ELSE 0.20 END AS sparse_score
        FROM t083_chunks
    )
    SELECT
        chunk_id,
        dense_score,
        sparse_score,
        ROUND(0.6 * dense_score + 0.4 * sparse_score, 4) AS hybrid_score
    FROM scored
    ORDER BY hybrid_score DESC
""")

results = {r["chunk_id"]: r["hybrid_score"] for r in ranked_df.collect()}
winner = ranked_df.first()["chunk_id"]
print(f"Hybrid RAG Ranking: {results} (top={winner})")
assert winner == "chunk_2_exact"
assert results["chunk_2_exact"] > results["chunk_1_conceptual"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Hybrid Search Standard**: Blend dense embeddings with sparse lexical scores to preserve exact identifiers.
# MAGIC - **Semantic Chunking**: Preserve header and clause boundaries instead of fixed character slices.
# MAGIC - **Reranking Pipeline**: Filter top hybrid candidates cleanly before invoking cross-encoders or LLMs.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why does pure vector embedding search often fail on domain-specific acronyms and part numbers?
# MAGIC 2. How does Reciprocal Rank Fusion (RRF) combine dense and sparse search rankings?
