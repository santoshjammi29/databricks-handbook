# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 052. Repair and Rerun Workflows: Surgical Partial DAG Replay on Upstream Failures
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC In a 12-task pipeline that took 3 hours to process 10 tasks, Task 11 failed due to a schema bug in an external dimension table. Re-running the entire 3-hour job from scratch violates executive SLAs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the 'Repair and Rerun' operational workflow in Databricks Jobs, executing only the failed task and its downstream children while preserving upstream state.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Workflows records the state of each task in a job run. The Repair and Rerun capability allows operators to fix the underlying issue and replay only failed and downstream tasks, saving hours of compute time.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Repair and Rerun DAG State Simulation
# MAGIC
# MAGIC Simulate partial DAG state and determine which tasks require re-execution.
# COMMAND ----------

job_run_state = {
    "run_id": 998822,
    "tasks": {
        "task_1_bronze": "SUCCESS",
        "task_2_silver": "SUCCESS",
        "task_3_feature_prep": "SUCCESS",
        "task_4_model_training": "FAILED", # FAILED TASK
        "task_5_model_evaluation": "UPSTREAM_FAILED" # SKIPPED CHILD
    }
}

# Repair algorithm: find failed tasks and all downstream dependencies
tasks_to_rerun = [k for k, v in job_run_state["tasks"].items() if v in ("FAILED", "UPSTREAM_FAILED")]
preserved_tasks = [k for k, v in job_run_state["tasks"].items() if v == "SUCCESS"]

print(f"Tasks Preserved (Zero re-computation): {preserved_tasks}")
print(f"Tasks Surgically Re-executed: {tasks_to_rerun}")
assert len(tasks_to_rerun) == 2
assert len(preserved_tasks) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **SLA Protection**: Saves hours of re-computation by skipping completed upstream tasks.
# MAGIC - **Cost Efficient**: Prevents paying twice for successful heavy ETL transformations.
# MAGIC - **Idempotent Sinks**: Ensure target tables support safe retries via `MERGE INTO` or atomic overwrites.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does the Repair and Rerun feature in Databricks Workflows preserve upstream task context?
# MAGIC 2. Can you alter task parameters before triggering a Repair and Rerun?
