# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 085. AI Functions in SQL: ai_query, ai_summarize, ai_classify & ai_analyze_sentiment
# MAGIC **Module**: Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A customer support analytics team has 1 million unstructured call center transcripts in a Delta table. They must extract customer sentiment, classify issue categories, and summarize issues using SQL.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy and test Databricks SQL AI Functions: `ai_query()`, `ai_summarize()`, `ai_classify()`, and `ai_analyze_sentiment()`, running LLMs directly within SQL queries.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks SQL provides built-in AI functions that invoke foundation models directly from `SELECT` statements. These execute on serverless compute with automatic batching, rate-limiting, and error handling.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. SQL AI Functions Demonstration DDL
# MAGIC
# MAGIC Author SQL queries invoking foundation models directly over table rows.
# COMMAND ----------

sql_ai_functions = """
-- 1. Classify support ticket category
SELECT
    ticket_id,
    ai_classify(customer_notes, ARRAY('Billing', 'Technical Support', 'Cancellation', 'Product Inquery')) AS issue_category,
    ai_analyze_sentiment(customer_notes) AS sentiment_score,
    ai_summarize(customer_notes, 20) AS short_summary
FROM prod_lakehouse.bronze.support_tickets
LIMIT 100;

-- 2. General LLM prompt via ai_query
SELECT
    product_name,
    ai_query('databricks-meta-llama-3-70b-instruct', CONCAT('Write a 1-sentence marketing pitch for: ', product_name)) AS marketing_copy
FROM prod_lakehouse.gold.dim_products;
"""

print("SQL AI Functions queries verified.")
assert "ai_classify(" in sql_ai_functions
assert "ai_analyze_sentiment(" in sql_ai_functions
assert "ai_query(" in sql_ai_functions
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **SQL-Native AI**: Run LLM processing directly within standard SQL transformations.
# MAGIC - **Built-in Micro-Batching**: Automatically batches requests to maximize inference throughput.
# MAGIC - **Zero Infrastructure**: No GPU cluster management or PyTorch pipelines required for NLP tasks.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does `ai_query()` differ from specialized functions like `ai_classify()` in Databricks SQL?
# MAGIC 2. How does Databricks SQL optimize throughput and handle rate limits when executing `ai_query()` over millions of rows?
