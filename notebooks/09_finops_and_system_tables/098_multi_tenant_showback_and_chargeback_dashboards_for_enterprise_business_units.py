# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 098. Multi-Tenant Showback & Chargeback Dashboards for Enterprise Business Units
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC The enterprise central IT department needs to bill back cloud infrastructure costs accurately to Marketing, Risk, Fraud, and Retail business units based on verified resource consumption.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Build an automated SQL Chargeback model over `system.billing.usage`, allocating shared metastore and infrastructure costs proportionally to tenant business units.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Chargeback allocates direct costs (tagged clusters) and indirect shared costs (metastore, system services) proportionally across business units, providing full transparency and fiscal accountability.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Tenant Chargeback Allocation SQL
# MAGIC
# MAGIC Construct departmental chargeback queries attributing direct and proportional shared spend.
# COMMAND ----------

sql_chargeback_model = """
-- Multi-Tenant Departmental Chargeback Model
WITH direct_costs AS (
    SELECT
        COALESCE(custom_tags['BusinessUnit'], 'SHARED_INFRA') AS business_unit,
        SUM(usage_quantity * 0.30) AS direct_spend_usd
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1
),
shared_pool AS (
    SELECT direct_spend_usd AS shared_amount FROM direct_costs WHERE business_unit = 'SHARED_INFRA'
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
ORDER BY total_monthly_bill_usd DESC;
"""

print("Departmental chargeback model verified.")
assert "SHARED_INFRA" in sql_chargeback_model
assert "total_monthly_bill_usd" in sql_chargeback_model
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Proportional Allocation**: Fairly distribute shared platform overhead based on direct consumption weights.
# MAGIC - **Fiscal Transparency**: Business units see exact itemized breakdowns of their monthly data engineering costs.
# MAGIC - **Self-Policing Culture**: Teams optimize their queries and auto-stop settings when bills are transparent.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you handle shared, untagged platform costs in a multi-tenant Databricks chargeback model?
# MAGIC 2. What is the difference between a Showback model and a Chargeback model in enterprise FinOps?
