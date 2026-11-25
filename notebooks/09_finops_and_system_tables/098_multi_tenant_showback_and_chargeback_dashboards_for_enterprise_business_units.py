# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 098. Multi-Tenant Showback & Chargeback Dashboards for Enterprise Business Units
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC The enterprise central IT department needs to bill back cloud infrastructure costs accurately to Marketing, Risk, Fraud, and Retail business units based on verified resource consumption.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Execute a proportional departmental chargeback allocation model in Spark SQL (direct cluster spend + shared platform infrastructure pool) and verify full bill reconciliation.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Chargeback allocates direct compute costs by `BusinessUnit` tag and splits indirect `SHARED_INFRA` platform spend proportionally by direct consumption weight so 100% of billing invoices reconcile to finance ledgers.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Tenant Chargeback Allocation & Reconciliation Query
# MAGIC
# MAGIC Execute a weighted CTE chargeback query in Spark SQL and assert the summed tenant bills reconcile 100% with total platform spend.
# COMMAND ----------

bu_usage = [
    ("FINANCE", 1000.0),
    ("RISK_ML", 600.0),
    ("RETAIL_BI", 400.0),
    (None, 200.0),  # Untaggable SHARED_INFRA metastore & governance overhead
]
spark.createDataFrame(bu_usage, ["business_unit", "usage_quantity"]).createOrReplaceTempView(
    "billing_chargeback_src"
)

bill_df = spark.sql("""
    WITH direct_costs AS (
        SELECT
            COALESCE(business_unit, 'SHARED_INFRA') AS business_unit,
            SUM(usage_quantity * 0.30) AS direct_spend_usd
        FROM billing_chargeback_src
        GROUP BY 1
    ),
    shared_pool AS (
        SELECT direct_spend_usd AS shared_amount
        FROM direct_costs
        WHERE business_unit = 'SHARED_INFRA'
    ),
    tenant_weights AS (
        SELECT
            business_unit,
            direct_spend_usd,
            direct_spend_usd / SUM(direct_spend_usd) OVER () AS weight
        FROM direct_costs
        WHERE business_unit != 'SHARED_INFRA'
    )
    SELECT
        t.business_unit,
        ROUND(t.direct_spend_usd, 2) AS direct_cost_usd,
        ROUND(t.weight * s.shared_amount, 2) AS allocated_shared_cost_usd,
        ROUND(t.direct_spend_usd + (t.weight * s.shared_amount), 2) AS total_monthly_bill_usd
    FROM tenant_weights t
    CROSS JOIN shared_pool s
    ORDER BY total_monthly_bill_usd DESC
""")

bills = {r["business_unit"]: r["total_monthly_bill_usd"] for r in bill_df.collect()}
total_billed = round(sum(bills.values()), 2)
raw_platform_usd = spark.sql("SELECT ROUND(SUM(usage_quantity * 0.30), 2) FROM billing_chargeback_src").first()[0]

print(f"Departmental Chargeback Bills: {bills} | Reconciled Total=${total_billed}")
assert bills["FINANCE"] == 330.0
assert abs(total_billed - raw_platform_usd) < 0.01
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Proportional Allocation**: Fairly distribute shared platform overhead based on direct consumption weights.
# MAGIC - **Full Ledger Reconciliation**: Sum of tenant bills equals total Databricks invoice with zero unallocated remainder.
# MAGIC - **Self-Policing Culture**: Transparent chargeback nudges teams to right-size clusters and auto-stop rules.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you handle shared, untagged platform costs in a multi-tenant Databricks chargeback model?
# MAGIC 2. What is the difference between a Showback model and a Chargeback model in enterprise FinOps?
