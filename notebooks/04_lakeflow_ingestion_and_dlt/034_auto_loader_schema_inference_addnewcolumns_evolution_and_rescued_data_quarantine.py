# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 034. Auto Loader Schema Inference, addNewColumns Evolution & _rescued_data Quarantine
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Third-party vendors frequently change JSON schemas by adding new promotional fields or sending numeric strings instead of floats. The ingestion pipeline must never drop records or crash.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Simulate Auto Loader's `_rescued_data` quarantine and `addNewColumns` schema evolution locally using Spark Structured Streaming over real JSON files (`columnNameOfCorruptRecord` + `mergeSchema`).
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC In Databricks, Auto Loader (`cloudFiles`) tracks schemas in `cloudFiles.schemaLocation`, captures malformed/type-conflicting tokens in `_rescued_data`, and evolves new columns when `schemaEvolutionMode = addNewColumns`. Locally we run genuine Spark Structured Streaming (`format('json')`, `trigger(availableNow=True)`) to verify corrupt record routing and Delta schema evolution.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Corrupt Payload Capture into Quarantine vs. Clean Bronze Stream
# MAGIC
# MAGIC Write raw JSON landing files (including a type-corrupt / malformed record), ingest using Structured Streaming `columnNameOfCorruptRecord = '_rescued_data'`, and route corrupt rows to quarantine without halting the pipeline.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_034_", dir=globals().get("HANDBOOK_TMP_DIR")))
raw_dir = lab_dir / "landing_json"
raw_dir.mkdir(parents=True)
ckpt_clean = str(lab_dir / "ckpt_clean")
ckpt_q = str(lab_dir / "ckpt_quarantine")
bronze_path = str(lab_dir / "bronze_orders")
quarantine_path = str(lab_dir / "quarantine_orders")

batch1_records = [
    '{"order_id": "ORD-1", "amount": 150.50}',
    '{"order_id": "ORD-2", "amount": 85.00}',
    '{"order_id": "ORD-BAD", "amount": "INVALID_FLOAT"',  # Malformed JSON triggers _rescued_data!
]
(raw_dir / "batch_01.json").write_text("\n".join(batch1_records) + "\n", encoding="utf-8")

expected_schema = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("_rescued_data", StringType(), True),
    ]
)

stream_df = (
    spark.readStream.format("json")
    .schema(expected_schema)
    .option("columnNameOfCorruptRecord", "_rescued_data")
    .load(str(raw_dir))
)

clean_q = (
    stream_df.filter(F.col("_rescued_data").isNull())
    .drop("_rescued_data")
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt_clean)
    .trigger(availableNow=True)
    .start(bronze_path)
)
bad_q = (
    stream_df.filter(F.col("_rescued_data").isNotNull())
    .select("order_id", "_rescued_data")
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt_q)
    .trigger(availableNow=True)
    .start(quarantine_path)
)
clean_q.awaitTermination()
bad_q.awaitTermination()

clean_cnt = spark.read.format("delta").load(bronze_path).count()
quarantine_cnt = spark.read.format("delta").load(quarantine_path).count()
print(f"Clean Bronze rows: {clean_cnt} | Quarantined _rescued_data rows: {quarantine_cnt}")
assert clean_cnt == 2 and quarantine_cnt == 1
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Safe Additive Schema Evolution (`mergeSchema` / `addNewColumns`)
# MAGIC
# MAGIC Simulate an upstream vendor adding a new `promo_code` attribute and evolve the Delta Bronze target cleanly while historical rows retain `NULL` for the new column.
# COMMAND ----------

evolved_df = spark.createDataFrame(
    [("ORD-3", 210.0, "WINTER20")], ["order_id", "amount", "promo_code"]
)
evolved_df.write.format("delta").mode("append").option("mergeSchema", "true").save(bronze_path)

final_bronze = spark.read.format("delta").load(bronze_path)
null_promos = final_bronze.filter("promo_code IS NULL").count()
print(f"Evolved schema columns: {final_bronze.columns}, legacy null promos: {null_promos}")
assert "promo_code" in final_bronze.columns
assert final_bronze.count() == 3 and null_promos == 2
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Data Loss**: `rescuedDataColumn` / `columnNameOfCorruptRecord` routes unparseable payloads safely to quarantine.
# MAGIC - **Schema Evolution**: `addNewColumns` (`mergeSchema`) accepts backward-compatible fields cleanly.
# MAGIC - **Schema Checkpointing**: Persisting schema state ensures stream restarts never regress schema versions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What happens under the hood when Auto Loader encounters a new column with `schemaEvolutionMode = addNewColumns`?
# MAGIC 2. How does the `_rescued_data` column capture schema collisions and unparseable JSON tokens?
