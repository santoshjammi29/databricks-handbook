# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 028. Delta UniForm: Asynchronous Iceberg Metadata Manifest Generation & Trino Access
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data platform must serve both Databricks users and an external Snowflake / Trino analytics cluster without duplicating 100 TB of Parquet data across Delta and Iceberg formats.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure Delta tables with `IcebergCompatV2` + column mapping invariants required by Delta Universal Format (UniForm), verify physical column-mapped Parquet schemas locally, and validate zero-duplication data file pointers in `_delta_log`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta UniForm writes standard Delta commits to `_delta_log` and asynchronously emits Apache Iceberg metadata (`metadata.json` and Avro manifests) pointing to the exact same Parquet files. Asynchronous Iceberg metadata emission requires `'delta.universalFormat.enabledFormats' = 'iceberg'` on Databricks Unity Catalog or an attached `delta-iceberg` runtime artifact; in local OSS Delta 3.2, `IcebergCompatV2` and `delta.columnMapping.mode = 'name'` validate all storage-layer schema invariants.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Enforce Column Mapping & `IcebergCompatV2` Invariants Locally
# MAGIC
# MAGIC Create a Delta table with `'delta.columnMapping.mode' = 'name'` and `'delta.enableIcebergCompatV2' = 'true'`, write records, and verify Iceberg compatibility properties and schema evolution.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_028_", dir=globals().get("HANDBOOK_TMP_DIR")))
uni_path = str(lab_dir / "uniform_metrics")

# Create Delta table enforcing strict Iceberg v2 storage invariants
spark.sql(f"""
    CREATE TABLE t028_uniform (
        customer_id BIGINT,
        lifetime_value DOUBLE,
        segment STRING
    ) USING DELTA
    LOCATION '{uni_path}'
    TBLPROPERTIES (
        'delta.columnMapping.mode' = 'name',
        'delta.enableIcebergCompatV2' = 'true'
    )
""")

spark.createDataFrame(
    [(1001, 12500.50, "ENTERPRISE"), (1002, 420.00, "SMB"), (1003, 9800.75, "MIDMARKET")],
    ["customer_id", "lifetime_value", "segment"],
).coalesce(1).write.format("delta").mode("append").save(uni_path)

# IcebergCompatV2 allows safe metadata-only column renames via Column Mapping
spark.sql("ALTER TABLE t028_uniform RENAME COLUMN segment TO customer_segment")

props = dict(spark.sql("SHOW TBLPROPERTIES t028_uniform").collect())
cols = spark.table("t028_uniform").columns
print(f"Table IcebergCompatV2 property: {props.get('delta.enableIcebergCompatV2')}")
print(f"Renamed columns via name-mapping: {cols}")

assert props.get("delta.enableIcebergCompatV2") == "true"
assert props.get("delta.columnMapping.mode") == "name"
assert "customer_segment" in cols
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Verify Zero-Copy Single Parquet Storage Across Manifests
# MAGIC
# MAGIC Read active file paths from `_delta_log/*.json` and confirm every referenced Parquet file exists once on disk without duplicated format copies.
# COMMAND ----------

log_entries = []
for fpath in sorted((Path(uni_path) / "_delta_log").glob("*.json")):
    for line in fpath.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if "add" in entry:
            log_entries.append(entry["add"]["path"])

existing_parquets = [p.name for p in Path(uni_path).glob("*.parquet")]
input_files = [Path(f).name for f in spark.table("t028_uniform").inputFiles()]

print(f"Delta log Parquet paths : {log_entries}")
print(f"Physical Parquet files  : {existing_parquets}")
assert set(input_files) <= set(existing_parquets)
assert len(existing_parquets) == 1
assert spark.table("t028_uniform").count() == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Copy of Data**: Delta, Snowflake, Trino, and BigQuery read the exact same underlying Parquet files.
# MAGIC - **Storage Invariants**: `delta.columnMapping.mode = 'name'` and `delta.enableIcebergCompatV2 = 'true'` guarantee type and schema compatibility for Iceberg readers.
# MAGIC - **Asynchronous Generation**: In Unity Catalog, adding `'delta.universalFormat.enabledFormats' = 'iceberg'` emits Avro manifests asynchronously without blocking Delta writers.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Delta UniForm enable Snowflake and AWS Athena to query Delta tables as Apache Iceberg?
# MAGIC 2. Are writes to the Delta table delayed while Iceberg metadata manifests are being generated in UniForm?
