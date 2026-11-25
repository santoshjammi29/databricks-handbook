# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 003. Cluster Types & Workload Isolation: All-Purpose vs. Automated Job vs. SQL Warehouses
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise FinOps audit revealed that data engineering teams are running scheduled nightly batch ETL jobs on interactive All-Purpose clusters, causing a 2.5x cost inflation.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement automated checks and cluster configuration generators that enforce the correct compute type (Job Compute vs. All-Purpose vs. Serverless SQL) based on workload semantics.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC All-Purpose compute is priced higher for developer interactivity. Job compute runs automated ephemeral clusters that terminate immediately on job completion. SQL Warehouses feature Photon C++ engines and Intelligent Workload Management for BI.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Compute Type Cost & Allocation Decision Matrix
# MAGIC
# MAGIC Evaluate workload attributes and return optimal cluster configuration specifications.
# COMMAND ----------

def recommend_compute(workload_type: str, is_scheduled: bool, concurrency: int) -> dict:
    if is_scheduled and workload_type == "ETL":
        return {
            "type": "JOB_COMPUTE",
            "dbu_multiplier": 1.0,
            "lifecycle": "ephemeral",
            "photon": True,
            "description": "Ephemeral Job Cluster provisioned via Lakeflow Jobs"
        }
    elif workload_type == "BI_DASHBOARD":
        return {
            "type": "SERVERLESS_SQL_WAREHOUSE",
            "dbu_multiplier": 1.5,
            "lifecycle": "serverless_autostop_10min",
            "photon": True,
            "description": "Serverless Photon SQL Warehouse with instant spinup"
        }
    else:
        return {
            "type": "ALL_PURPOSE",
            "dbu_multiplier": 2.5,
            "lifecycle": "interactive_autostop_20min",
            "photon": False,
            "description": "Shared Interactive Cluster for exploratory notebook development"
        }

rec = recommend_compute("ETL", is_scheduled=True, concurrency=1)
assert rec["type"] == "JOB_COMPUTE", "Scheduled batch jobs must use Job Compute!"
print(f"Recommended Compute: {rec['type']} | Cost Factor: {rec['dbu_multiplier']}x")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Job Compute Rule**: Never schedule production workflows on All-Purpose clusters.
# MAGIC - **Serverless SQL**: Use for high-concurrency BI dashboards (Tableau, Power BI, Lakeview).
# MAGIC - **Ephemeral Lifecycle**: Job clusters spin up on task start and terminate on completion, preventing idle spend.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why is Job Compute significantly cheaper than All-Purpose Compute?
# MAGIC 2. When should you choose a Serverless SQL Warehouse over an All-Purpose cluster for query workloads?
