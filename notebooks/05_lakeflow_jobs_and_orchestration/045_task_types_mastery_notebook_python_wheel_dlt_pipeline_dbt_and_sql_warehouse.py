# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 045. Multi-Modal Task Types: Notebook, Python Wheel, DLT Pipeline, dbt & SQL Warehouse
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise platform combines multiple technology stacks: data ingestion runs in DLT, business transformations run in dbt Core, and BI aggregations run as SQL queries in a SQL Warehouse.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure a unified multi-task job orchestrating Notebook tasks, Python Wheel tasks, DLT Pipeline tasks, dbt tasks, and Databricks SQL tasks within a single pane of glass.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakeflow Jobs is multi-modal. Rather than restricting tasks to notebooks, it supports compiled Python Wheels, SQL Warehouse queries, dbt models, and DLT pipelines in one DAG.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Modal Task Specification
# MAGIC
# MAGIC Define resource blocks for various task types supported in Databricks Workflows.
# COMMAND ----------

task_types_spec = {
    "task_1_bronze": {"type": "pipeline_task", "pipeline_id": "dlt-pipeline-uuid-001"},
    "task_2_silver": {"type": "python_wheel_task", "package_name": "etl_core", "entry_point": "run_silver"},
    "task_3_dbt": {"type": "dbt_task", "commands": ["dbt run --select gold_marts"]},
    "task_4_gold_alert": {"type": "sql_task", "warehouse_id": "wh-serverless-001", "query_id": "qry-audit-summary"}
}

for task_name, spec in task_types_spec.items():
    print(f"Task: {task_name} | Type: {spec['type']}")
assert len(task_types_spec) == 4
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Beyond Notebooks**: Production teams increasingly package code into Python Wheels for clean versioning.
# MAGIC - **Native dbt Integration**: Databricks executes dbt models with native Photon acceleration.
# MAGIC - **Unified Monitoring**: Review run histories across DLT, SQL, and Python in one view.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why should complex production code be deployed as Python Wheels rather than raw notebooks in Lakeflow Jobs?
# MAGIC 2. How does Databricks orchestrate dbt tasks natively in Workflows?
