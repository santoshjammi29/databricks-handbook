# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 038. Advanced DLT Data Quality: Dead Letter Queue (DLQ) Quarantine Tables Pattern
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC In regulatory banking, dropping invalid records with `expect_or_drop` violates compliance; every invalid row must be diverted into a Dead Letter Queue (DLQ) quarantine table for human remediation.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a single-read Structured Streaming DLQ split pipeline (`foreachBatch`), atomically persisting passing financial transactions to Delta Clean and constraint-violating records with diagnostic metadata to Delta Quarantine.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The DLQ pattern reads incoming transactions once and splits valid records (`account_id IS NOT NULL AND transaction_amount > 0`) from failing rows routed to quarantine with `_quarantine_reason` and `_quarantined_at` columns for downstream remediation and SOX/HIPAA auditability.
# COMMAND ----------

import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Single-Read `foreachBatch` DLQ Split into Clean & Quarantine Delta Tables
# MAGIC
# MAGIC Stream raw banking JSON events with `trigger(availableNow=True)` and branch good vs. bad records cleanly in a single pass.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_038_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "tx_landing"
landing.mkdir(parents=True)
clean_delta = str(lab_dir / "transactions_clean")
dlq_delta = str(lab_dir / "transactions_quarantine")
ckpt = str(lab_dir / "ckpt_dlq")

tx_lines = [
    '{"tx_id": "TX-1", "account_id": "ACC-100", "transaction_amount": 420.50}',
    '{"tx_id": "TX-2", "account_id": null, "transaction_amount": 95.00}',
    '{"tx_id": "TX-3", "account_id": "ACC-200", "transaction_amount": -15.00}',
    '{"tx_id": "TX-4", "account_id": "ACC-300", "transaction_amount": 1250.00}',
]
(landing / "batch_01.json").write_text("\n".join(tx_lines) + "\n", encoding="utf-8")

tx_schema = StructType(
    [
        StructField("tx_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("transaction_amount", DoubleType(), True),
    ]
)

def split_dlq_batch(micro_df, _batch_id: int) -> None:
    cached = micro_df.cache()
    valid_expr = (F.col("account_id").isNotNull()) & (F.col("transaction_amount") > 0)
    cached.filter(valid_expr).write.format("delta").mode("append").save(clean_delta)
    (
        cached.filter(~valid_expr)
        .withColumn(
            "_quarantine_reason",
            F.when(F.col("account_id").isNull(), "NULL_ACCOUNT_ID").otherwise("NON_POSITIVE_AMOUNT"),
        )
        .withColumn("_quarantined_at", F.current_timestamp())
        .write.format("delta")
        .mode("append")
        .save(dlq_delta)
    )
    cached.unpersist()

q = (
    spark.readStream.format("json")
    .schema(tx_schema)
    .load(str(landing))
    .writeStream.foreachBatch(split_dlq_batch)
    .option("checkpointLocation", ckpt)
    .trigger(availableNow=True)
    .start()
)
q.awaitTermination()

clean_cnt = spark.read.format("delta").load(clean_delta).count()
dlq_rows = spark.read.format("delta").load(dlq_delta).select("tx_id", "_quarantine_reason").collect()
reasons = {r["tx_id"]: r["_quarantine_reason"] for r in dlq_rows}
print(f"DLQ Split -> Clean: {clean_cnt}, Quarantined: {reasons}")
assert clean_cnt == 2
assert reasons == {"TX-2": "NULL_ACCOUNT_ID", "TX-3": "NON_POSITIVE_AMOUNT"}
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Silent Drops**: Every invalid record is preserved in the quarantine table with diagnostic metadata.
# MAGIC - **Single-Pass IO**: Splitting inside `foreachBatch` (or `@dlt.table` branching from one stream) avoids reading landing files twice.
# MAGIC - **Compliance Invariant**: Essential for healthcare (HIPAA) and financial (SOX) regulatory pipelines.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you implement a Dead Letter Queue in Delta Live Tables without reading upstream files twice?
# MAGIC 2. What metadata columns should always be attached to quarantined records?
