# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 103. Production Incident 05: Auto Loader Schema Drift & Poison Pill Quarantine Forensics
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An upstream vendor pushed corrupted JSON records with unescaped control characters and string data in numeric fields, halting the production ingestion stream.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy Auto Loader quarantine pattern with `rescuedDataColumn`, isolate poison pills to a Dead Letter Queue table, and resume streaming ingestion with zero data loss.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Poison pill files contain syntax or type violations that crash naive parsers. Auto Loader's `rescuedDataColumn` captures the raw unparseable JSON without failing the stream, allowing downstream quarantine routing.
# COMMAND ----------

from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Rescued Data Quarantine Extraction
# MAGIC
# MAGIC Filter and route poison records to an isolated quarantine table.
# COMMAND ----------

# Simulate separating clean records from poison pills
incoming_records = [
    {"id": 1, "val": 100.0, "_rescued_data": None},
    {"id": 2, "val": 250.0, "_rescued_data": None},
    {"id": 3, "val": None, "_rescued_data": '{"val": "CORRUPTED_HEX_TOKEN"}'}
]

df_incoming = spark.createDataFrame(incoming_records)
df_clean = df_incoming.filter(F.col("_rescued_data").isNull())
df_quarantine = df_incoming.filter(F.col("_rescued_data").isNotNull())

print(f"Clean Records Processed: {df_clean.count()}")
print(f"Poison Pills Quarantined: {df_quarantine.count()}")
assert df_quarantine.count() == 1
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Stream Halt**: Poison pills are isolated without interrupting ingestion for valid records.
# MAGIC - **Root-Cause Forensics**: Quarantined records preserve the exact raw payload and file source metadata.
# MAGIC - **Automated Alerting**: Fire PagerDuty alerts if quarantine table row count increases.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Auto Loader's `_rescued_data` column prevent poison pill pipeline outages?
# MAGIC 2. How do you safely replay quarantined records once upstream bugs are resolved?
