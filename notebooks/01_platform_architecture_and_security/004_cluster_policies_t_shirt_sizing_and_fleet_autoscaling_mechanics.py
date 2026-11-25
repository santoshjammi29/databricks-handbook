# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 004. Cluster Policies, T-Shirt Sizing & Fleet Autoscaling Mechanics
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC Developers frequently spin up oversized 64-core clusters for simple data exploration, wasting tens of thousands in cloud spend each month.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Define, validate, and enforce a Databricks Cluster Policy JSON specification that mandates T-shirt sizing (Small, Medium, Large), limits maximum worker nodes, and forces aggressive 15-minute auto-termination.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Cluster policies enforce guardrails on cluster creation. They restrict allowable VM node types, mandate autoscale limits (`max_workers`), enforce tags (`CostCenter`, `Owner`), and lock idle auto-stop timeouts.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Construct Production Cluster Policy Definition
# MAGIC
# MAGIC Create an immutable JSON policy definition restricting developers to cost-effective instances with auto-stop.
# COMMAND ----------

import json

cluster_policy = {
    "autotermination_minutes": {
        "type": "range",
        "maxValue": 20,
        "defaultValue": 15,
        "isOptional": False
    },
    "autoscale.max_workers": {
        "type": "range",
        "maxValue": 8,
        "defaultValue": 4,
        "isOptional": False
    },
    "node_type_id": {
        "type": "allowlist",
        "values": ["Standard_D4ds_v5", "Standard_D8ds_v5"],
        "defaultValue": "Standard_D4ds_v5"
    },
    "custom_tags.CostCenter": {
        "type": "fixed",
        "value": "DataEngineering",
        "isOptional": False
    }
}

# Verify policy invariants
assert cluster_policy["autotermination_minutes"]["maxValue"] <= 20
assert "Standard_D4ds_v5" in cluster_policy["node_type_id"]["values"]
print("Cluster policy specification verified.")
print(json.dumps(cluster_policy, indent=2))
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Policy Enforcement**: Restrict node types to prevent expensive GPU/high-memory instances on dev workloads.
# MAGIC - **Auto-Stop Invariant**: Set interactive timeouts to 15-20 minutes maximum.
# MAGIC - **Mandatory Tags**: Enforce CostCenter tags directly in policy for downstream FinOps attribution.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do cluster policies prevent rogue cloud infrastructure spending in Databricks?
# MAGIC 2. Can a cluster policy override user-specified Spark configuration settings?
