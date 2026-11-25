# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 046. Inter-Task Communication & Context Sharing via dbutils.jobs.taskValues
# MAGIC **Module**: Module 05: Lakeflow Jobs, Workflows & Orchestration
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC In a nightly batch ETL workflow, an upstream ingestion task computes the dynamic date partition and processed row count. Downstream tasks require these dynamic values to run incremental updates.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the use of `dbutils.jobs.taskValues.set()` in an upstream task and `dbutils.jobs.taskValues.get()` in a downstream task to share execution state.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `taskValues` allows tasks within the same job run to pass scalar values, JSON dictionaries, and execution flags across task boundaries without writing temporary metadata files to cloud storage.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Set and Retrieve Task Values
# MAGIC
# MAGIC Simulate inter-task state passing using the taskValues API pattern.
# COMMAND ----------

# Simulate dbutils.jobs.taskValues in Python
class MockTaskValues:
    def __init__(self):
        self._store = {}
    def set(self, key: str, value):
        self._store[key] = value
    def get(self, task_key: str, key: str, default=None):
        return self._store.get(key, default)

mock_tv = MockTaskValues()

# Upstream Task 1 (Ingestion) sets values
mock_tv.set("batch_id", "20261117_01")
mock_tv.set("records_processed", 450000)
mock_tv.set("status", "SUCCESS")

# Downstream Task 2 retrieves values
retrieved_batch = mock_tv.get("ingest_task", "batch_id")
retrieved_count = mock_tv.get("ingest_task", "records_processed")

print(f"Downstream Task Received: Batch ID = {retrieved_batch}, Rows = {retrieved_count}")
assert retrieved_batch == "20261117_01"
assert retrieved_count == 450000
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **State Propagation**: Share dynamic dates, metrics, and thresholds between tasks.
# MAGIC - **Zero Storage Footprint**: State is held in the Control Plane metadata store for the run duration.
# MAGIC - **Conditional Gating**: Downstream condition tasks can evaluate task values to make branching decisions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What is the maximum payload size supported for `dbutils.jobs.taskValues`?
# MAGIC 2. Can a task access task values from a previous run of the same job?
