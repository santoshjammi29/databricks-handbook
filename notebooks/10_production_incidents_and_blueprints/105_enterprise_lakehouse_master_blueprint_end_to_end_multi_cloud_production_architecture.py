# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 105. Enterprise Lakehouse Master Blueprint: End-to-End Multi-Cloud Production Architecture
# MAGIC **Module**: Module 10: Production Incidents, Triage & Architecture Blueprints
# MAGIC **Mastery Level**: `Architect` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A Fortune 50 enterprise requires a unified lakehouse blueprint spanning raw Auto Loader ingestion, DLT conformance, Unity Catalog governance, DABs CI/CD, DBSQL reporting, and Mosaic AI RAG.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a genuine end-to-end Bronze -> Quarantine & Silver -> Gold Delta Lakehouse pipeline locally: stream raw JSON landing files with corrupt rescue -> quarantine poison pills -> deduplicate & `MERGE INTO` Deletion-Vector Silver (`CHECK` enforced) -> aggregate `CLUSTER BY` Gold KPIs with full row reconciliation.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC The master blueprint links storage correctness (`Deletion Vectors`, `CHECK` constraints, `CDF`, `CLUSTER BY`), streaming exactly-once checkpointing, idempotent `MERGE INTO`, and additive Gold BI views into one reproducible verifiable pipeline.
# COMMAND ----------

import tempfile
from pathlib import Path
from delta.tables import DeltaTable
from pyspark.sql import Window, functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. End-to-End Bronze Stream -> Quarantine Split -> Silver Delta MERGE -> Gold KPIs
# MAGIC
# MAGIC Execute the full multi-hop medallion pipeline in local Spark + Delta 3.2 and reconcile counts and revenue across Bronze, Quarantine, Silver, and Gold.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_105_", dir=globals().get("HANDBOOK_TMP_DIR")))
landing = lab_dir / "raw_orders"
landing.mkdir(parents=True)
bronze_path = str(lab_dir / "bronze_orders")
dlq_path = str(lab_dir / "bronze_dlq")
silver_path = str(lab_dir / "silver_orders")
gold_path = str(lab_dir / "gold_region_kpis")

raw_json = [
    '{"order_id": "O-1", "region": "US", "amount": 100.0, "event_seq": 1}',
    '{"order_id": "O-1", "region": "US", "amount": 150.0, "event_seq": 2}',  # Update for O-1!
    '{"order_id": "O-2", "region": "EU", "amount": 250.0, "event_seq": 1}',
    '{"order_id": "O-BAD", "region": "EU", "amount": "CORRUPT"',             # Malformed JSON -> DLQ!
]
(landing / "batch_01.json").write_text("\n".join(raw_json) + "\n", encoding="utf-8")

raw_schema = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("region", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("event_seq", LongType(), True),
        StructField("_corrupt", StringType(), True),
    ]
)

# 1. Bronze streaming ingestion with corrupt payload isolation
q = (
    spark.readStream.format("json")
    .schema(raw_schema)
    .option("columnNameOfCorruptRecord", "_corrupt")
    .load(str(landing))
    .writeStream.format("delta")
    .option("checkpointLocation", str(lab_dir / "ckpt_bronze"))
    .trigger(availableNow=True)
    .start(bronze_path)
)
q.awaitTermination()

bronze_df = spark.read.format("delta").load(bronze_path)
bronze_df.filter(F.col("_corrupt").isNotNull()).write.format("delta").save(dlq_path)

# 2. Silver governed Delta table (Deletion Vectors + CDF + CHECK constraint)
spark.sql(f"""
    CREATE TABLE t105_silver (order_id STRING, region STRING, amount DOUBLE, event_seq BIGINT) USING DELTA
    LOCATION '{silver_path}'
    TBLPROPERTIES ('delta.enableDeletionVectors' = 'true', 'delta.enableChangeDataFeed' = 'true')
""")
spark.sql("ALTER TABLE t105_silver ADD CONSTRAINT positive_amt CHECK (amount > 0)")

valid_dedup = (
    bronze_df.filter(F.col("_corrupt").isNull())
    .withColumn("_rn", F.row_number().over(Window.partitionBy("order_id").orderBy(F.col("event_seq").desc())))
    .filter(F.col("_rn") == 1)
    .select("order_id", "region", "amount", "event_seq")
)
DeltaTable.forPath(spark, silver_path).alias("t").merge(
    valid_dedup.alias("s"), "t.order_id = s.order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# 3. Gold Liquid-Clustered BI KPI table
spark.sql(f"""
    CREATE TABLE t105_gold (region STRING, orders BIGINT, net_revenue DOUBLE) USING DELTA
    LOCATION '{gold_path}'
    CLUSTER BY (region)
""")
spark.sql("""
    INSERT OVERWRITE t105_gold
    SELECT region, COUNT(*) AS orders, SUM(amount) AS net_revenue
    FROM t105_silver
    GROUP BY region
""")

dlq_cnt = spark.read.format("delta").load(dlq_path).count()
silver_cnt = spark.table("t105_silver").count()
gold_rev = spark.sql("SELECT SUM(net_revenue) FROM t105_gold").first()[0]
silver_rev = spark.sql("SELECT SUM(amount) FROM t105_silver").first()[0]

print(f"Master Medallion Reconciliation -> DLQ={dlq_cnt}, Silver={silver_cnt}, GoldRev=${gold_rev}")
assert dlq_cnt == 1 and silver_cnt == 2
assert gold_rev == silver_rev == 400.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Complete Medallion Integrity**: End-to-end streaming Bronze, DLQ quarantine, governed Silver, and clustered Gold reconcile 100%.
# MAGIC - **Modern Delta Defaults**: Enable Deletion Vectors, Change Data Feed, Liquid Clustering, and storage `CHECK` constraints together.
# MAGIC - **Zero Silent Failures**: Corrupt vendor records divert cleanly into DLQ while valid updates upsert idempotently.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do all components of the Databricks Data Intelligence Platform fit together in a modern enterprise architecture?
# MAGIC 2. What are the top three architectural principles that differentiate a successful lakehouse implementation from a failed data swamp?
