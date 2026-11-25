# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 050. Resilient Error Handling, Exponential Backoff Retries & PagerDuty/Slack Webhooks
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A production pipeline experiences transient network timeouts connecting to external cloud storage. Jobs must automatically retry with exponential backoff and page on-call engineers if retries are exhausted.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure task-level retry policies (`max_retries`, `min_retry_interval_millis`), timeout budgets, and notification system webhooks in Lakeflow Jobs.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Transient cloud infrastructure failures (HTTP 503, network blips) can be mitigated by configuring task retries. Lakeflow Jobs allows setting retries per task with exponential backoff, preventing immediate pipeline abortion.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Task Retry Policy & Notification Configuration
# MAGIC
# MAGIC Define retry parameters and notification webhooks in job specifications.
# COMMAND ----------

resilience_config = {
    "task_key": "fetch_external_api_data",
    "max_retries": 3,
    "min_retry_interval_millis": 30000, # 30 seconds
    "retry_on_timeout": True,
    "timeout_seconds": 3600,
    "notifications": {
        "on_failure": ["data-ops-pagerduty@company.pagerduty.com"],
        "on_retry": ["data-engineering-slack-webhook@company.com"]
    }
}

print(f"Task Retries Allowed: {resilience_config['max_retries']}")
print(f"Initial Retry Delay: {resilience_config['min_retry_interval_millis'] / 1000}s")
assert resilience_config["max_retries"] == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Task-Level Retries**: Configure `max_retries = 3` to absorb transient network blips.
# MAGIC - **Timeout Budgets**: Always set `timeout_seconds` to kill runaway zombie tasks automatically.
# MAGIC - **PagerDuty / Slack Webhooks**: Route critical alerts directly to on-call incident response channels.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the difference between job-level timeout and task-level timeout in Databricks Workflows?
# MAGIC 2. How do exponential backoff retries prevent exacerbating cloud service rate limits?
