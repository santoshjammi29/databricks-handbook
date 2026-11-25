# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 089. Calculating DBU Consumption & Cloud Costs via system.billing.usage
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A FinOps analyst needs to produce a daily executive report calculating total DBU spend, converting DBUs to currency based on contract rates, and identifying cost drivers.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute Spark SQL aggregations over local telemetry modeled after `system.billing.usage` to calculate daily DBU consumption by workspace and SKU, converting DBUs to dollar costs with contract rates.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `system.billing.usage` records hourly DBU usage across workspaces (`workspace_id`, `sku_name`, `usage_quantity`). Locally we materialize the identical table schema as a Spark temp view and run the production SQL aggregation.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. FinOps DBU Aggregation Query Execution in Spark SQL
# MAGIC
# MAGIC Load hourly DBU telemetry modeled after `system.billing.usage` into a Spark view and aggregate cost drivers by SKU and workspace.
# COMMAND ----------

billing_records = [
    ("2026-11-20", "STANDARD_ALL_PURPOSE_COMPUTE", "ws-prod-01", 120.5),
    ("2026-11-20", "JOBS_COMPUTE", "ws-prod-01", 410.0),
    ("2026-11-20", "SERVERLESS_SQL", "ws-bi-02", 85.0),
    ("2026-11-21", "STANDARD_ALL_PURPOSE_COMPUTE", "ws-prod-01", 290.0),
    ("2026-11-21", "JOBS_COMPUTE", "ws-prod-01", 400.0),
]
spark.createDataFrame(
    billing_records, ["usage_date", "sku_name", "workspace_id", "usage_quantity"]
).createOrReplaceTempView("billing_usage")

# Equivalent to querying Databricks account `system.billing.usage`
daily_cost_df = spark.sql("""
    WITH daily_usage AS (
        SELECT usage_date, sku_name, workspace_id, SUM(usage_quantity) AS total_dbus
        FROM billing_usage
        GROUP BY 1, 2, 3
    )
    SELECT
        usage_date,
        sku_name,
        workspace_id,
        ROUND(total_dbus, 2) AS dbus,
        ROUND(total_dbus * 0.35, 2) AS estimated_cost_usd
    FROM daily_usage
    ORDER BY dbus DESC
""")

rows = daily_cost_df.collect()
total_usd = round(sum(r["estimated_cost_usd"] for r in rows), 2)
print(f"Top DBU consumer SKU: {rows[0]['sku_name']} ({rows[0]['dbus']} DBUs) | Total Spend: ${total_usd}")
assert rows[0]["sku_name"] == "JOBS_COMPUTE"
assert total_usd > 400.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Accurate SKU Tracking**: Distinguish between high-cost Interactive compute and cost-effective Job compute.
# MAGIC - **Contract Normalization**: Multiply DBUs by contracted tier rates to calculate exact monthly cloud spend.
# MAGIC - **Proactive Budgeting**: Monitor daily burn rates to forecast end-of-month budget overages.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between `usage_quantity` in `system.billing.usage` and the underlying cloud VM cost?
# MAGIC 2. How does `system.billing.usage` capture serverless compute versus classic compute consumption?
