# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 060. Materialized Views & Streaming Tables in DBSQL without Apache Spark Code
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC SQL analysts and analytics engineers without Python skills need to build automated incremental pipelines that ingest files and maintain aggregated summary marts.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the Databricks SQL `CREATE STREAMING TABLE` and `CREATE MATERIALIZED VIEW` execution semantics locally by streaming JSON landing events incrementally into Delta Bronze and materializing Gold page-view rollups via SQL.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks SQL Streaming Tables and Materialized Views run on serverless DLT infrastructure using pure ANSI SQL (`STREAM read_files()`). Locally we mirror this exact incremental ingestion -> SQL rollup pattern cleanly in Spark + Delta.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Streaming Bronze Ingestion + SQL Materialized Gold Rollup
# MAGIC
# MAGIC Stream raw web JSON events with `trigger(availableNow=True)` into Delta `bronze_web_logs` and refresh an aggregated SQL summary table `gold_daily_page_views`.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_060_", dir=globals().get("HANDBOOK_TMP_DIR")))
raw_dir = lab_dir / "web_logs_json"
raw_dir.mkdir(parents=True)
bronze_path = str(lab_dir / "bronze_web_logs")
gold_path = str(lab_dir / "gold_daily_page_views")
ckpt = str(lab_dir / "ckpt_web_logs")

log_events = [
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v1"}',
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v2"}',
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v1"}',
    '{"log_date": "2026-11-20", "page_url": "/docs", "visitor_id": "v3"}',
]
(raw_dir / "events_01.json").write_text("\n".join(log_events) + "\n", encoding="utf-8")

schema = StructType(
    [
        StructField("log_date", StringType(), False),
        StructField("page_url", StringType(), False),
        StructField("visitor_id", StringType(), False),
    ]
)

q = (
    spark.readStream.format("json")
    .schema(schema)
    .load(str(raw_dir))
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt)
    .trigger(availableNow=True)
    .start(bronze_path)
)
q.awaitTermination()

spark.sql(f"CREATE TABLE t060_bronze USING DELTA LOCATION '{bronze_path}'")
gold_df = spark.sql("""
    SELECT log_date, page_url, COUNT(*) AS total_hits, COUNT(DISTINCT visitor_id) AS unique_visitors
    FROM t060_bronze
    GROUP BY log_date, page_url
""")
gold_df.write.format("delta").mode("overwrite").save(gold_path)

pricing = spark.read.format("delta").load(gold_path).filter("page_url = '/pricing'").first()
print(f"/pricing rollup -> hits={pricing['total_hits']}, unique_visitors={pricing['unique_visitors']}")
assert pricing["total_hits"] == 3 and pricing["unique_visitors"] == 2
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Python Required in DBSQL**: Analysts declare Streaming Tables & Materialized Views cleanly in ANSI SQL.
# MAGIC - **Incremental State Management**: Databricks tracks ingested files cleanly via checkpoints.
# MAGIC - **Consistent Aggregations**: Exact distinct & rollup metrics stay aligned with Bronze tables.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Materialized Views in Databricks SQL differ from standard SQL Views?
# MAGIC 2. What is the function of `STREAM read_files()` in pure SQL streaming tables?
