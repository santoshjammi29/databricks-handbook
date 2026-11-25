# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 097. Aggressive Auto-Stop Policies & Cold Compute Idle Reduction Strategies
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Foundational` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An audit found developers leaving clusters active during lunch breaks and overnight because the default 120-minute auto-termination was never changed.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy cluster policies enforcing strict 10-15 minute auto-stop rules across all interactive compute, quantify idle cost reductions, and educate teams on serverless instant start.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Idle compute is the single largest source of cloud waste in analytics platforms. Enforcing aggressive auto-stop policies and transitioning users to Serverless compute (which spins up in seconds) eliminates the developer friction of waiting for clusters.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Idle Cost Waste Reduction Model
# MAGIC
# MAGIC Calculate annual savings from reducing auto-termination from 120 min to 15 min.
# COMMAND ----------

def calculate_idle_savings(num_clusters: int, idle_events_per_day: int, dbu_hourly_rate: float = 0.35, dbu_per_cluster: int = 8):
    # Old policy: 120 min (2 hours) idle per event
    old_idle_hours_per_day = num_clusters * idle_events_per_day * 2.0
    # New policy: 15 min (0.25 hours) idle per event
    new_idle_hours_per_day = num_clusters * idle_events_per_day * 0.25

    saved_hours_per_day = old_idle_hours_per_day - new_idle_hours_per_day
    annual_cost_savings = saved_hours_per_day * dbu_per_cluster * dbu_hourly_rate * 365
    return {"saved_hours_daily": saved_hours_per_day, "annual_savings_usd": annual_cost_savings}

savings = calculate_idle_savings(num_clusters=25, idle_events_per_day=2)
print(f"Daily Wasted Hours Eliminated: {savings['saved_hours_daily']:.1f} hrs")
print(f"Annual Cloud Cost Savings: ${savings['annual_savings_usd']:,.2f}")
assert savings["annual_savings_usd"] > 50000
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **15-Minute Standard**: Enforce 10-15 minute idle termination in cluster policies for all interactive clusters.
# MAGIC - **Serverless Migration**: Serverless SQL Warehouses start in 2 seconds; set their auto-stop to 5-10 minutes.
# MAGIC - **Tens of Thousands Saved**: Small policy changes compound into massive annual cloud savings.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why do developers resist short auto-stop timeouts, and how does Serverless compute resolve that friction?
# MAGIC 2. How can you audit which clusters frequently hit their auto-termination limit?
