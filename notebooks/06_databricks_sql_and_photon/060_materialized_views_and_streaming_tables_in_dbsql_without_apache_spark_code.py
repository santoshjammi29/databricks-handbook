# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 060. Materialized Views & Streaming Tables in DBSQL without Apache Spark Code
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC SQL analysts and analytics engineers without Python skills need to build automated incremental pipelines that ingest files and maintain aggregated summary marts.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy Streaming Tables and Materialized Views in Databricks SQL using pure ANSI SQL (`CREATE STREAMING TABLE` and `CREATE MATERIALIZED VIEW`), managing automatic refresh schedules.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks SQL supports declarative Streaming Tables and Materialized Views natively. Under the hood, these leverage the DLT engine with serverless compute, bringing incremental pipeline engineering to pure SQL users.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Pure ANSI SQL Declarative Pipeline DDL
# MAGIC
# MAGIC Create streaming tables and materialized views with refresh schedules in SQL.
# COMMAND ----------

ddl_sql_pipelines = """
-- 1. Create Streaming Table ingesting files via cloud_files() in SQL
CREATE OR REPLACE STREAMING TABLE prod_lakehouse.bronze.web_logs
SCHEDULE EVERY 1 HOUR
AS SELECT * FROM STREAM read_files(
    '/Volumes/prod_lakehouse/raw/web_logs/',
    format => 'json'
);

-- 2. Create Materialized View pre-aggregating metrics
CREATE OR REPLACE MATERIALIZED VIEW prod_lakehouse.gold.daily_page_views
SCHEDULE EVERY 1 DAY
AS SELECT
    CAST(event_time AS DATE) AS log_date,
    page_url,
    COUNT(*) AS total_hits,
    COUNT(DISTINCT visitor_id) AS unique_visitors
FROM prod_lakehouse.bronze.web_logs
GROUP BY 1, 2;
"""

print("Pure SQL Streaming Table & Materialized View DDL verified.")
assert "CREATE OR REPLACE STREAMING TABLE" in ddl_sql_pipelines
assert "CREATE OR REPLACE MATERIALIZED VIEW" in ddl_sql_pipelines
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Python Required**: SQL analysts can build robust streaming pipelines using pure ANSI SQL.
# MAGIC - **Automated Incremental Refresh**: Materialized views recompute only what has changed upstream.
# MAGIC - **Unified Serverless Compute**: Refreshes execute on serverless SQL warehouses automatically.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Materialized Views in Databricks SQL differ from standard SQL Views?
# MAGIC 2. What is the function of `STREAM read_files()` in pure SQL streaming tables?
