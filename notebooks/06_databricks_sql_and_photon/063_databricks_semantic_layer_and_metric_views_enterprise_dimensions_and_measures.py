# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 063. Databricks Semantic Layer & Metric Views: Enterprise Dimensions & Measures
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Different departments compute 'Customer Churn' and 'Net Revenue' using conflicting formulas, resulting in discrepancies during executive board meetings.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy a canonical Semantic Metric View in Spark/Delta (`net_revenue`, `order_volume`, `average_order_value`), slice identical measures by different dimensional grains (`region` vs. `product_tier`), and prove 100% additive KPI consistency.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Centralizing metric expressions (`SUM(gross_amount - discount_amount)`) inside a governed Semantic View eliminates formula drift between Finance, BI dashboards, and Databricks Genie.
# COMMAND ----------

import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Canonical Metric View Materialization & Cross-Dimension Reconciliation
# MAGIC
# MAGIC Define `t063_metrics_financial_core` over Delta sales transactions and verify identical aggregate KPI totals across independent dimensional slices.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_063_", dir=globals().get("HANDBOOK_TMP_DIR")))
sales_path = str(lab_dir / "silver_sales_tx")

spark.createDataFrame(
    [
        (1, "C1", "EMEA", "ENTERPRISE", 1000.0, 100.0),
        (2, "C2", "NA", "PRO", 500.0, 50.0),
        (3, "C3", "EMEA", "PRO", 300.0, 0.0),
        (4, "C4", "APAC", "ENTERPRISE", 800.0, 80.0),
    ],
    ["tx_id", "customer_id", "region", "product_tier", "gross_amount", "discount_amount"],
).write.format("delta").save(sales_path)
spark.sql(f"CREATE TABLE t063_sales USING DELTA LOCATION '{sales_path}'")

spark.sql("""
    CREATE OR REPLACE VIEW t063_metrics_core AS
    SELECT
        region,
        product_tier,
        SUM(gross_amount - discount_amount) AS net_revenue,
        COUNT(DISTINCT tx_id) AS order_volume
    FROM t063_sales
    GROUP BY region, product_tier
""")

rev_by_region = {r["region"]: r["rev"] for r in spark.sql("SELECT region, SUM(net_revenue) AS rev FROM t063_metrics_core GROUP BY region").collect()}
rev_by_tier = {r["product_tier"]: r["rev"] for r in spark.sql("SELECT product_tier, SUM(net_revenue) AS rev FROM t063_metrics_core GROUP BY product_tier").collect()}
total_region = sum(rev_by_region.values())
total_tier = sum(rev_by_tier.values())
base_total = spark.sql("SELECT SUM(gross_amount - discount_amount) FROM t063_sales").first()[0]

print(f"Semantic Net Revenue -> by region={total_region}, by tier={total_tier}, base={base_total}")
assert total_region == total_tier == base_total == 2370.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Source of Truth**: Define critical business measures once in governed Unity Catalog views.
# MAGIC - **Metric Parity**: Power BI, Lakeview Dashboards, and Genie consume the identical net-revenue logic.
# MAGIC - **Centralized Evolution**: Formula changes propagate globally downstream without dashboard rewrites.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does an in-database Semantic Layer in Unity Catalog eliminate metric discrepancies between BI tools?
# MAGIC 2. What is the difference between a dimensional attribute and a metric measure?
