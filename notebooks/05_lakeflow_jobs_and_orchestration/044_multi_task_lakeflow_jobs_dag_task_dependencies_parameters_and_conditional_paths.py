# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 044. Multi-Task Lakeflow Jobs: DAG Task Dependencies, Parameters & Conditional Paths
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial data pipeline consists of 8 sequential and parallel steps: ingest market feeds, validate records, branch based on market holiday status, and run downstream settlement.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define a multi-task Lakeflow DAG job structure with explicit dependencies (`depends_on`), conditional execution (`If/Else` tasks), and parameter inheritance.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakeflow Jobs orchestrate complex directed acyclic graphs (DAGs) of tasks within Databricks. Tasks can execute in parallel, wait for upstream parents, or branch conditionally based on dynamic task values.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Multi-Task DAG Task Structure Model
# MAGIC
# MAGIC Simulate and validate DAG topological dependencies and conditional task branches.
# COMMAND ----------

job_dag = {
    "job_name": "daily_market_settlement",
    "tasks": [
        {"task_key": "ingest_trades", "depends_on": []},
        {"task_key": "validate_data", "depends_on": ["ingest_trades"]},
        {"task_key": "check_market_holiday", "depends_on": ["validate_data"], "task_type": "condition"},
        {"task_key": "run_settlement", "depends_on": ["check_market_holiday"], "run_if": "ALL_SUCCESS"},
        {"task_key": "skip_settlement_notification", "depends_on": ["check_market_holiday"], "run_if": "AT_LEAST_ONE_FAILED"}
    ]
}

# Topological validation: ensure all dependency tasks exist
task_keys = {t["task_key"] for t in job_dag["tasks"]}
for t in job_dag["tasks"]:
    for parent in t["depends_on"]:
        assert parent in task_keys, f"Invalid DAG: Missing dependency {parent}"

print("DAG topology validated: All task dependencies resolved.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **DAG Native**: Lakeflow Jobs replace external schedulers like Airflow for Databricks-native pipelines.
# MAGIC - **Conditional Routing**: Use `If/Else` condition tasks to dynamically route workflow execution.
# MAGIC - **Zero Cluster Lock**: Each task can run on its own ephemeral cluster or serverless compute.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do conditional `If/Else` tasks work in Databricks Workflows?
# MAGIC 2. What is the difference between `run_if = ALL_SUCCESS` and `run_if = AT_LEAST_ONE_SUCCESS`?
