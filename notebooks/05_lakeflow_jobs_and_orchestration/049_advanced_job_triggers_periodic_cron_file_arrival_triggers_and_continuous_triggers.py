# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 049. Advanced Job Triggers: Periodic Cron, File Arrival Triggers & Continuous Triggers
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Different enterprise workloads have distinct invocation triggers: sales reporting runs on a cron schedule, partner invoice processing triggers on file arrival, and streaming monitoring runs continuously.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure and test the three Databricks Workflows trigger types: (1) Periodic Quartz Cron, (2) Storage File Arrival Trigger, and (3) Continuous Execution Loop.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Lakeflow Jobs support multiple trigger mechanisms. File Arrival Triggers monitor cloud storage folders and trigger jobs instantly when new files land, avoiding polling scripts. Continuous triggers keep a job constantly running, restarting immediately on failure.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Job Trigger Architecture Specification
# MAGIC
# MAGIC Define YAML/JSON trigger definitions for cron, file arrival, and continuous execution.
# COMMAND ----------

trigger_definitions = {
    "scheduled_cron": {
        "type": "cron",
        "quartz_cron_expression": "0 0 4 * * ?", # 04:00 AM UTC daily
        "timezone_id": "UTC"
    },
    "file_arrival": {
        "type": "file_arrival",
        "url": "abfss://landing@storage.dfs.core.windows.net/vendor_invoices/",
        "min_time_between_triggers_seconds": 60
    },
    "continuous_service": {
        "type": "continuous",
        "pause_status": "UNPAUSED"
    }
}

for name, trig in trigger_definitions.items():
    print(f"Trigger: {name} | Type: {trig['type']}")
assert trigger_definitions["file_arrival"]["min_time_between_triggers_seconds"] == 60
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **File Arrival Automation**: Eliminates external Lambda functions or cron polling scripts.
# MAGIC - **Throttling Protection**: Use `min_time_between_triggers_seconds` to batch bursts of file arrivals.
# MAGIC - **Continuous Mode**: Ideal for continuous real-time streaming pipelines requiring automatic restarts.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do File Arrival Triggers detect new files in cloud storage without causing high API call costs?
# MAGIC 2. What happens if a new file arrives while a previous run triggered by File Arrival is still executing?
