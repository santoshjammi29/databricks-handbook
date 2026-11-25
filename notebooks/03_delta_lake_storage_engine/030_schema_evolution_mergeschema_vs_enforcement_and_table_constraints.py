# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 030. Schema Evolution (`mergeSchema`) vs. Enforcement & Table Constraints
# MAGIC **Module**: Module 03: Delta Lake 3.x Deep Dive — Storage Engine & UniForm
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An API integration team frequently alters incoming JSON payloads, adding new tracking fields. The data pipeline must enforce data types on core columns while allowing safe addition of new fields without crashing.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Prove Delta Schema Enforcement blocks unexpected columns by default, unlock safe column evolution with `.option('mergeSchema', 'true')`, and enforce domain invariants via real `ALTER TABLE ... ADD CONSTRAINT ... CHECK` constraints.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Delta Lake validates schemas at commit time (Schema-on-Write). Unexpected columns fail immediately unless `mergeSchema = true` is explicitly passed. Table `CHECK` constraints enforce row-level business invariants directly inside Delta's write execution path.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Schema Enforcement Protection vs. Controlled `mergeSchema` Evolution
# MAGIC
# MAGIC Verify Delta blocks unannounced columns by default (capturing `AnalysisException`), then evolve cleanly with `mergeSchema = 'true'` and verify existing rows backfill with `NULL`.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_030_", dir=globals().get("HANDBOOK_TMP_DIR")))
orders_path = str(lab_dir / "orders_schema")

spark.createDataFrame(
    [(1, "C100", 125.0), (2, "C101", 80.5)], ["order_id", "customer_id", "amount"]
).write.format("delta").save(orders_path)
spark.sql(f"CREATE TABLE t030_orders USING DELTA LOCATION '{orders_path}'")

drifted_df = spark.createDataFrame(
    [(3, "C102", 210.0, "SAVE10")], ["order_id", "customer_id", "amount", "discount_code"]
)

# BAD / DEFAULT: Strict schema enforcement rejects surprise columns
rejected = False
try:
    drifted_df.write.format("delta").mode("append").save(orders_path)
except Exception as exc:
    rejected = "schema mismatch" in str(exc).lower() or "AnalysisException" in type(exc).__name__

print(f"Schema Enforcement rejected extra column cleanly: {rejected}")
assert rejected is True

# GOOD: Controlled schema evolution adds column safely
drifted_df.write.format("delta").mode("append").option("mergeSchema", "true").save(orders_path)
evolved_df = spark.read.format("delta").load(orders_path)
null_backfilled = evolved_df.filter("discount_code IS NULL").count()

print(f"Evolved columns: {evolved_df.columns}, existing null backfills: {null_backfilled}")
assert evolved_df.columns == ["order_id", "customer_id", "amount", "discount_code"]
assert null_backfilled == 2 and evolved_df.count() == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Transactional Business Rules with Delta `CHECK` Constraints
# MAGIC
# MAGIC Add a storage-layer `CHECK (amount > 0)` invariant, confirm invalid negative transactions fail atomically with zero partial corruption, and verify row count stability.
# COMMAND ----------

spark.sql("ALTER TABLE t030_orders ADD CONSTRAINT valid_amount CHECK (amount > 0)")

constraint_blocked = False
try:
    spark.sql("INSERT INTO t030_orders VALUES (4, 'C103', -49.99, 'BAD')")
except Exception as exc:
    constraint_blocked = "CHECK constraint" in str(exc) or "DELTA_VIOLATE_CONSTRAINT" in str(exc)

spark.sql("INSERT INTO t030_orders VALUES (4, 'C103', 49.99, 'WELCOME')")
final_count = spark.table("t030_orders").count()
min_amount = spark.table("t030_orders").agg({"amount": "min"}).first()[0]

print(f"Invalid row blocked by CHECK constraint: {constraint_blocked}")
print(f"Final count={final_count}, min_amount={min_amount}")
assert constraint_blocked is True
assert final_count == 4 and min_amount > 0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Schema Enforcement Default**: Prevents silent column pollution from malformed upstream feeds.
# MAGIC - **Controlled Evolution**: Pass `.option('mergeSchema', 'true')` to allowlist safe backward-compatible column additions.
# MAGIC - **Storage-Layer Constraints**: `ALTER TABLE ... ADD CONSTRAINT ... CHECK (...)` guarantees corrupted domain values never commit.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between `mergeSchema` and `overwriteSchema` in Delta Lake?
# MAGIC 2. How do `CHECK` constraints in Delta Lake compare to traditional RDBMS constraints?
