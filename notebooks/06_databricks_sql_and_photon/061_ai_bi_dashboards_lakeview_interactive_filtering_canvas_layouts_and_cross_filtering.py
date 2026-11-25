# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 061. AI/BI Dashboards (Lakeview): Interactive Filtering, Canvas Layouts & Cross-Filtering
# MAGIC **Module**: Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An organization wants to retire legacy dashboard tools (Redash/Tableau) in favor of AI/BI Dashboards (Lakeview) that connect directly to Unity Catalog data with native cross-filtering.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define an AI/BI Dashboard specification in JSON/YAML, configure interactive parameter widgets, establish cross-filtering between charts, and manage the Draft/Published lifecycle.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC AI/BI Dashboards (formerly Lakeview) provide modern data visualization built directly on Databricks SQL. Dashboards separate Draft state from Published state, support cross-filtering across visual charts, and run on serverless warehouses.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. AI/BI Dashboard Specification Structure
# MAGIC
# MAGIC Simulate dashboard definition with widgets and cross-filtering rules.
# COMMAND ----------

dashboard_spec = {
    "display_name": "Executive Revenue Intelligence",
    "warehouse_id": "wh-serverless-001",
    "pages": [
        {
            "name": "Overview",
            "layout": "grid",
            "visualizations": [
                {"id": "viz_1", "type": "counter", "title": "Total Revenue", "query": "SELECT SUM(amount) FROM fact_sales"},
                {"id": "viz_2", "type": "bar", "title": "Revenue by Region", "query": "SELECT region, SUM(amount) FROM fact_sales GROUP BY region"},
                {"id": "viz_3", "type": "line", "title": "Monthly Trend", "query": "SELECT date_trunc('month', sale_date), SUM(amount) FROM fact_sales GROUP BY 1"}
            ],
            "cross_filtering_enabled": True
        }
    ]
}

print(f"Dashboard: {dashboard_spec['display_name']}")
print(f"Visualizations Configured: {len(dashboard_spec['pages'][0]['visualizations'])}")
assert dashboard_spec["pages"][0]["cross_filtering_enabled"] is True
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Draft vs. Published**: Developers can make changes in Draft mode without breaking the live Published dashboard.
# MAGIC - **Native Cross-Filtering**: Clicking a bar in one chart instantly filters all other charts on the canvas.
# MAGIC - **Direct UC Governance**: Dashboards inherit Unity Catalog row filters and column masks automatically.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does the Draft and Published lifecycle work in Databricks AI/BI Dashboards?
# MAGIC 2. Do AI/BI Dashboards respect Unity Catalog Dynamic Row Filters and Column Masks?
