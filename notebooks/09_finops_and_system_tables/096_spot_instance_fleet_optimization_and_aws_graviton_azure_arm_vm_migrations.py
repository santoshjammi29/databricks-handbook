# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 096. Spot Instance Fleet Optimization & AWS Graviton / Azure ARM VM Migrations
# MAGIC **Module**: Module 09: FinOps, Observability & System Tables Masterclass
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A large batch ETL infrastructure bill is $100,000 per month. The platform architect must cut VM infrastructure costs by 40% without compromising pipeline SLAs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Evaluate Spot instance configuration and migrate worker fleets to ARM-based VM architectures (AWS Graviton3 / Azure Cobalt/ARM), analyzing price-performance benchmarks.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Spot instances offer up to 70-80% discounts on cloud VM costs. Databricks handles Spot evictions gracefully in batch jobs. Migrating from x86 to ARM instances (e.g., `m6g` in AWS, `Dpsv5` in Azure) delivers 25-40% better price-performance.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Spot & ARM Architecture Economics Matrix
# MAGIC
# MAGIC Compare hourly VM costs and eviction resilience between On-Demand and Spot ARM fleets.
# COMMAND ----------

fleet_economics = {
    "x86_On_Demand": {"vm": "Standard_D8ds_v5", "hourly_vm_cost": 0.38, "spot_discount": "0%", "sla_risk": "Zero risk"},
    "x86_Spot_Workers": {"vm": "Standard_D8ds_v5", "hourly_vm_cost": 0.11, "spot_discount": "71%", "sla_risk": "Low (auto-replacement)"},
    "ARM_Graviton_Spot": {"vm": "Standard_D8ps_v5 (ARM)", "hourly_vm_cost": 0.08, "spot_discount": "79%", "sla_risk": "Low; 25% faster Photon execution"}
}

for arch, data in fleet_economics.items():
    print(f"[{arch}] Cost: ${data['hourly_vm_cost']}/hr | Discount: {data['spot_discount']} | Risk: {data['sla_risk']}")

assert fleet_economics["ARM_Graviton_Spot"]["hourly_vm_cost"] < 0.10
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Driver On-Demand, Workers Spot**: Always keep the driver on On-Demand to prevent cluster termination on Spot loss.
# MAGIC - **ARM Architecture Superiority**: Photon's vectorized C++ code is highly optimized for ARM NEON SIMD registers.
# MAGIC - **Batch ETL Savings**: Massive multi-thousand-dollar savings on nightly batch processing.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Why must the driver node always be provisioned as On-Demand even when worker nodes use Spot instances?
# MAGIC 2. What performance advantages does the Photon engine realize on ARM-based cloud VMs?
