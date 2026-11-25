# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 091. Cost Breakdown Analysis: Interactive vs. Job vs. DBSQL vs. Serverless vs. DLT
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A VP of Data Engineering wants to know whether recent platform modernization efforts (migrating batch jobs to DLT and Serverless) successfully reduced interactive development waste.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a Spark SQL workload categorization pipeline mapping billing SKUs into five FinOps pillars (`Interactive`, `Jobs`, `DBSQL`, `DLT`, `Serverless`) and verify share percentages sum cleanly.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Grouping `sku_name` prefixes reveals workload efficiency ratios. Mature Databricks platforms keep `ALL_PURPOSE` interactive spend below 20% and shift scheduled production pipelines to `JOBS`, `DLT`, or `SERVERLESS`.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Workload Categorization & Share Window Function in Spark SQL
# MAGIC
# MAGIC Categorize billing SKU records using Spark SQL `CASE WHEN` + window share calculation and validate interactive waste thresholds.
# COMMAND ----------

sku_samples = [
    ("PREMIUM_ALL_PURPOSE_COMPUTE", 150.0),
    ("JOBS_COMPUTE", 450.0),
    ("ENTERPRISE_SQL_PRO_COMPUTE", 200.0),
    ("DLT_ADVANCED_COMPUTE", 120.0),
    ("SERVERLESS_JOBS_COMPUTE", 80.0),
]
spark.createDataFrame(sku_samples, ["sku_name", "usage_quantity"]).createOrReplaceTempView(
    "billing_sku_samples"
)

breakdown_df = spark.sql("""
    SELECT
        CASE
            WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Development'
            WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless Compute'
            WHEN sku_name LIKE '%JOBS%' THEN 'Automated Batch Jobs'
            WHEN sku_name LIKE '%SQL%' THEN 'Databricks SQL / BI'
            WHEN sku_name LIKE '%DLT%' THEN 'Delta Live Tables'
            ELSE 'Other Services'
        END AS workload_category,
        SUM(usage_quantity) AS total_dbus,
        ROUND(SUM(usage_quantity) * 100.0 / SUM(SUM(usage_quantity)) OVER (), 1) AS dbu_share_pct
    FROM billing_sku_samples
    GROUP BY 1
    ORDER BY total_dbus DESC
""")

cats = {r["workload_category"]: r["dbu_share_pct"] for r in breakdown_df.collect()}
total_pct = round(sum(cats.values()), 1)
print(f"Workload DBU shares (%): {cats} (sum={total_pct}%)")
assert total_pct == 100.0
assert cats["Interactive Development"] < 20.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Healthy Ratio Benchmark**: Production enterprises target < 20% Interactive and > 80% Automated/Serverless spend.
# MAGIC - **Migration ROI**: Track declining `ALL_PURPOSE` shares as pipelines migrate to DABs and Lakeflow.
# MAGIC - **Executive Summary**: Translate raw billing SKUs into clear engineering pillar allocation.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is considered a healthy ratio of Interactive vs. Automated Job DBU consumption in an enterprise?
# MAGIC 2. How can you identify scheduled batch workloads incorrectly running under an `ALL_PURPOSE` SKU?
