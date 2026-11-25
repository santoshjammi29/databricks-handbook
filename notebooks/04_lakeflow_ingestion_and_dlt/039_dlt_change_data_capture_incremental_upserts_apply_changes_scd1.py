# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 039. DLT Change Data Capture: Incremental Upserts with dlt.apply_changes (SCD Type 1)
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A CRM database emits change logs (inserts, updates, deletes) via Debezium. The analytics team must maintain a conformed customer table reflecting current state (SCD Type 1).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute out-of-order CDC deduplication (`sequence_by` descending window) + Delta `MERGE INTO` (`UPDATE`, `INSERT`, `DELETE`) locally to mirror `dlt.apply_changes()` SCD Type 1 semantics.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC In Databricks DLT, `dlt.apply_changes()` (and SQL `AUTO CDC INTO`) compiles down to sequenced deduplication + Delta `MERGE INTO`. Ranking incoming batch events per primary key by sequence timestamp ensures older delayed retries never clobber newer state.
# COMMAND ----------

import tempfile
from pathlib import Path
from delta.tables import DeltaTable
from pyspark.sql import Window, functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Out-of-Order CDC Deduplication & SCD Type 1 Delta MERGE
# MAGIC
# MAGIC Seed `customers_scd1`, ingest an unordered CDC micro-batch containing a stale retry (`t=10` arriving alongside newer `t=30`), a new insert, and a hard `DELETE`, then verify final target state.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_039_", dir=globals().get("HANDBOOK_TMP_DIR")))
scd1_path = str(lab_dir / "customers_scd1")

spark.createDataFrame(
    [(1, "alice@v1.com", "2026-11-20T09:00:00"), (2, "bob@v1.com", "2026-11-20T09:00:00")],
    ["customer_id", "email", "last_seq_ts"],
).write.format("delta").save(scd1_path)

cdc_events = spark.createDataFrame(
    [
        # Out-of-order pair for customer_id=1: newer event (12:00) + delayed stale retry (08:00)
        (1, "alice@v3_final.com", "UPDATE", "2026-11-20T12:00:00"),
        (1, "alice@stale_retry.com", "UPDATE", "2026-11-20T08:00:00"),
        (2, "bob@v1.com", "DELETE", "2026-11-20T11:30:00"),
        (3, "carol@new.com", "INSERT", "2026-11-20T11:45:00"),
    ],
    ["customer_id", "email", "op_type", "op_timestamp"],
)

latest_cdc = (
    cdc_events.withColumn(
        "_rn",
        F.row_number().over(Window.partitionBy("customer_id").orderBy(F.col("op_timestamp").desc())),
    )
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

(
    DeltaTable.forPath(spark, scd1_path)
    .alias("t")
    .merge(latest_cdc.alias("s"), "t.customer_id = s.customer_id")
    .whenMatchedDelete(condition="s.op_type = 'DELETE'")
    .whenMatchedUpdate(
        condition="s.op_type != 'DELETE' AND s.op_timestamp > t.last_seq_ts",
        set={"email": "s.email", "last_seq_ts": "s.op_timestamp"},
    )
    .whenNotMatchedInsert(
        condition="s.op_type != 'DELETE'",
        values={"customer_id": "s.customer_id", "email": "s.email", "last_seq_ts": "s.op_timestamp"},
    )
    .execute()
)

final_map = {
    r["customer_id"]: r["email"] for r in spark.read.format("delta").load(scd1_path).collect()
}
print(f"SCD Type 1 Customer State: {final_map}")
assert final_map == {1: "alice@v3_final.com", 3: "carol@new.com"}
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Automated Deduplication**: Sequence keys resolve out-of-order CDC retries safely.
# MAGIC - **Guard Stale Replays**: Checking `s.op_timestamp > t.last_seq_ts` protects already-committed newer rows.
# MAGIC - **Declarative Upgrade**: On Databricks, `dlt.apply_changes()` / `AUTO CDC INTO` handles this logic declaratively.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does `dlt.apply_changes()` handle out-of-order CDC change events?
# MAGIC 2. What is the difference between specifying `keys` versus `sequence_by` in `dlt.apply_changes()`?
