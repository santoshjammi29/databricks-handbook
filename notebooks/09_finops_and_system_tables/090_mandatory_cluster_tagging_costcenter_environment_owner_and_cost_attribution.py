# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 090. Mandatory Cluster Tagging (CostCenter, Environment, Owner) & Cost Attribution
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Finance cannot allocate a $500,000 monthly Databricks bill to business units because 60% of clusters were launched without `CostCenter` or `Project` tags.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Parse the `custom_tags` map in Spark SQL over billing telemetry to attribute 100% of DBU spend across `CostCenter` and `Project` codes and quarantine untagged cluster leaks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Cluster policies enforce `custom_tags.CostCenter`, propagating automatically into `system.billing.usage.custom_tags` (`MAP<STRING, STRING>`).
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Query Tagged Costs & Untouched Leak Detection in Spark SQL
# MAGIC
# MAGIC Materialize `custom_tags` MapType telemetry in Spark SQL, coalesce untagged clusters as `UNALLOCATED_LEAK`, and compute cost-attribution share.
# COMMAND ----------

tagged_rows = [
    ("2026-11-20", {"CostCenter": "FIN-100", "Project": "RISK_DW"}, 300.0),
    ("2026-11-20", {"CostCenter": "MKT-220", "Project": "ATTRIBUTION"}, 180.0),
    ("2026-11-20", {"Owner": "contractor"}, 120.0),  # Missing CostCenter!
]
spark.createDataFrame(tagged_rows, ["usage_date", "custom_tags", "usage_quantity"]).createOrReplaceTempView(
    "billing_usage_tagged"
)

attr_df = spark.sql("""
    SELECT
        COALESCE(custom_tags['CostCenter'], 'UNALLOCATED_LEAK') AS cost_center,
        COALESCE(custom_tags['Project'], 'GENERAL') AS project,
        SUM(usage_quantity) AS total_dbus,
        ROUND(SUM(usage_quantity * 0.30), 2) AS cost_usd
    FROM billing_usage_tagged
    GROUP BY 1, 2
    ORDER BY total_dbus DESC
""")

by_cc = {r["cost_center"]: r["cost_usd"] for r in attr_df.collect()}
print(f"Cost Attribution USD: {by_cc}")
assert by_cc["UNALLOCATED_LEAK"] == 36.0
assert by_cc["FIN-100"] == 90.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Enforce at Policy Level**: Never rely on human memory for tagging; enforce via cluster policies.
# MAGIC - **Unallocated Leak Hunting**: Query for `custom_tags['CostCenter'] IS NULL` to isolate non-compliant workloads.
# MAGIC - **Automated Chargeback**: Export aggregated attribution tables directly to enterprise finance pipelines.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do cluster tags propagate into Databricks System Tables?
# MAGIC 2. How do you configure a Databricks Cluster Policy to mandate that users enter a valid 6-digit Cost Center code?
