# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 068. DABs Multi-Environment Targeting: dev, staging, and prod Promotion Topologies
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An enterprise requires strict deployment gates: code developed in feature branches is deployed to developer sandboxes, PR merges trigger Staging validation, and git tags deploy to Production.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Configure environment targets (`dev`, `staging`, `prod`) in DABs, enforcing path isolation (`/Users/.../.bundle` vs `/Shared/.bundle`) and permission controls.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Target environments ensure clean separation: `dev` deploys to personal developer folders with paused schedules; `staging` runs integration tests; `prod` enforces Service Principal ownership and active cron triggers.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Target Environment Configuration Matrix
# MAGIC
# MAGIC Define promotion settings, schedule states, and root paths across targets.
# COMMAND ----------

promotion_matrix = {
    "dev": {"mode": "development", "schedules": "PAUSED", "root": "/Users/${workspace.current_user.userName}/.bundle"},
    "staging": {"mode": "production", "schedules": "PAUSED", "root": "/Shared/.bundle/${bundle.name}/staging"},
    "prod": {"mode": "production", "schedules": "UNPAUSED", "root": "/Shared/.bundle/${bundle.name}/prod"}
}

for env, conf in promotion_matrix.items():
    print(f"Target: {env.upper()} | Mode: {conf['mode']} | Schedules: {conf['schedules']}")

assert promotion_matrix["dev"]["schedules"] == "PAUSED"
assert promotion_matrix["prod"]["schedules"] == "UNPAUSED"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Schedule Safety**: Developer bundles never accidentally trigger production cron schedules.
# MAGIC - **Namespace Isolation**: Each target writes to dedicated catalogs (`dev_catalog` vs `prod_catalog`).
# MAGIC - **Automated Promotion**: Promote code by passing `-t <target>` in CI/CD pipelines.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What changes automatically when a bundle target is switched from `mode: development` to `mode: production`?
# MAGIC 2. How do you prevent a developer from deploying a local bundle directly into the production target?
