# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 076. Blue/Green Pipeline Deployment & Zero-Downtime Bundle Rollouts
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Architect` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A 24/7 financial reporting system cannot tolerate downtime during pipeline upgrades. Upgrades must run in parallel, validate results, and switch user queries with zero interruption.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a real atomic Blue/Green Delta cutover locally: materialize `fact_sales_blue` (v1) and `fact_sales_green` (v2), gate cutover on Green data-quality checks, flip the live reporting view atomically via `CREATE OR REPLACE VIEW`, and verify instant rollback.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Blue/Green deployment isolates candidate pipeline builds in `fact_sales_green`. BI dashboards query the abstraction view `fact_sales`. Only after Green passes row-count and null checks does a single metadata `CREATE OR REPLACE VIEW` commit shift traffic atomically.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Live Blue/Green Atomic View Cutover & Rollback Verification
# MAGIC
# MAGIC Materialize Blue and Green Delta tables, gate promotion on Green quality checks, flip the view pointer atomically, and demonstrate millisecond rollback to Blue.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_076_", dir=globals().get("HANDBOOK_TMP_DIR")))
blue_path = str(lab_dir / "fact_sales_blue")
green_path = str(lab_dir / "fact_sales_green")

spark.createDataFrame(
    [(1, "US", 100.0), (2, "EU", 200.0)], ["order_id", "region", "net_revenue"]
).write.format("delta").save(blue_path)
spark.sql(f"CREATE TABLE t076_sales_blue USING DELTA LOCATION '{blue_path}'")

# Step 1: Production view serves Blue (total=300.0)
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_blue")
blue_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

# Step 2: Green pipeline builds upgraded dataset & runs pre-cutover DQ gate
spark.createDataFrame(
    [(1, "US", 105.0), (2, "EU", 210.0), (3, "APAC", 150.0)], ["order_id", "region", "net_revenue"]
).write.format("delta").save(green_path)
spark.sql(f"CREATE TABLE t076_sales_green USING DELTA LOCATION '{green_path}'")

dq_ok = spark.sql("SELECT COUNT(*) FROM t076_sales_green WHERE net_revenue <= 0 OR net_revenue IS NULL").first()[0] == 0
assert dq_ok is True

# Step 3: Atomic metadata cutover to Green -> view revenue reflects 465.0
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_green")
green_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

# Step 4: Instantaneous metadata rollback test back to Blue -> revenue reverts to 300.0
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_blue")
rollback_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

print(f"View revenues -> blue={blue_rev}, green={green_rev}, rollback={rollback_rev}")
assert blue_rev == 300.0 and green_rev == 465.0 and rollback_rev == 300.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Query Interruption**: Readers never observe empty or partially overwritten tables during deploys.
# MAGIC - **Instant Rollback**: Re-pointing the SQL view back to Blue takes milliseconds with zero table rebuilds.
# MAGIC - **Safe Schema Evolution**: Breaking transformations validate cleanly on Green before serving BI users.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does an atomic view redirection enable zero-downtime upgrades in a lakehouse architecture?
# MAGIC 2. What is the rollback procedure if a newly cutover Green pipeline encounters corrupted data?
