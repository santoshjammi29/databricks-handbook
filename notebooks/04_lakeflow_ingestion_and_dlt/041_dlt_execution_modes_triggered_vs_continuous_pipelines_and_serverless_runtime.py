# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 041. DLT Execution Modes: Triggered vs. Continuous Pipelines & Serverless Runtime
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A lakehouse architect must optimize pipeline costs: high-priority fraud detection requires sub-minute continuous execution, while standard billing reconciliation runs hourly.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Compare Triggered (batch) vs. Continuous (streaming) pipeline execution modes in DLT, configure Serverless DLT compute, and analyze DBU consumption curves.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Triggered pipelines start compute, process all available data once, and terminate (ideal for hourly/daily batch ETL). Continuous pipelines run indefinitely with dedicated streaming micro-batches (sub-second latency). Serverless DLT removes cluster configuration and scales instantly.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. DLT Pipeline Execution Mode Decision Matrix
# MAGIC
# MAGIC Evaluate latency requirements vs compute cost across DLT execution models.
# COMMAND ----------

dlt_modes = {
    "Triggered_Serverless": {
        "latency": "Minutes to hours (scheduled)",
        "cost_efficiency": "High: Scales down to 0 DBUs immediately upon batch completion",
        "best_for": "Medallion batch pipelines, hourly reporting, cost-sensitive workloads"
    },
    "Continuous_Enhanced": {
        "latency": "Sub-second to seconds",
        "cost_efficiency": "Moderate: Clusters remain continuously warm and active",
        "best_for": "Real-time fraud alerting, live IoT telemetry, sub-minute SLAs"
    }
}

for mode, attrs in dlt_modes.items():
    print(f"[{mode}]\n  Latency: {attrs['latency']}\n  Cost: {attrs['cost_efficiency']}\n")

assert "Scales down to 0 DBUs" in dlt_modes["Triggered_Serverless"]["cost_efficiency"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Triggered Mode for Batch**: Always use Triggered mode unless the business explicitly demands sub-minute SLA.
# MAGIC - **Serverless DLT**: Eliminates cluster startup delay and automatically optimizes worker memory.
# MAGIC - **Enhanced Autoscaling**: DLT allocates compute based on streaming backlog queue depths.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. When should an enterprise use Continuous mode versus Triggered mode in Delta Live Tables?
# MAGIC 2. How does Serverless DLT handle worker autoscaling compared to Classic DLT?
