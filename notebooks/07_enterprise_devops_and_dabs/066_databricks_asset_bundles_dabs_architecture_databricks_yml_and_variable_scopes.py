# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 066. Databricks Asset Bundles (DABs) Architecture: databricks.yml & Variable Scopes
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A data platform engineering team needs to standardize pipeline deployments across 50 data engineers, eliminating manual UI clicks and establishing declarative Infrastructure as Code (IaC).
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Author and parse a root `databricks.yml` asset bundle specification with PyYAML, resolve target variable scopes (`dev` vs. `prod`), and materialize environment-isolated Delta targets in Spark.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Asset Bundles (DABs) provide declarative IaC for all Databricks assets. Target blocks override top-level `variables:` so developer bundles write into sandboxed locations while `prod` writes to governed catalogs.
# COMMAND ----------

import re
import tempfile
from pathlib import Path
import yaml
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Parse Bundle YAML, Resolve Variable Scopes & Materialize Target Delta Tables
# MAGIC
# MAGIC Parse a real `databricks.yml` manifest with `yaml.safe_load`, resolve `${var.catalog}` and `${var.schema}` for `dev` and `prod` targets, and write target-isolated Delta outputs via Spark.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_066_", dir=globals().get("HANDBOOK_TMP_DIR")))

bundle_yaml = """
bundle:
  name: enterprise-lakehouse-pipeline

variables:
  catalog:
    default: "dev_catalog"
  schema:
    default: "analytics"

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: "dev_sandbox"
  prod:
    mode: production
    variables:
      catalog: "prod_lakehouse"
"""

parsed = yaml.safe_load(bundle_yaml)

def resolve_vars(target_name: str) -> dict[str, str]:
    base = {k: v["default"] for k, v in parsed.get("variables", {}).items()}
    overrides = parsed["targets"][target_name].get("variables", {})
    return {**base, **overrides}

# Execute Spark writes parameterized by resolved DABs target variables
for target in ("dev", "prod"):
    v = resolve_vars(target)
    tbl_dir = str(lab_dir / v["catalog"] / v["schema"] / "daily_summary")
    (
        spark.createDataFrame([(target, v["catalog"], 100)], ["target", "catalog", "rows_loaded"])
        .write.format("delta")
        .mode("overwrite")
        .save(tbl_dir)
    )

dev_cat = spark.read.format("delta").load(str(lab_dir / "dev_sandbox/analytics/daily_summary")).select("catalog").first()[0]
prod_cat = spark.read.format("delta").load(str(lab_dir / "prod_lakehouse/analytics/daily_summary")).select("catalog").first()[0]
print(f"Resolved targets -> dev: {dev_cat}, prod: {prod_cat}")
assert dev_cat == "dev_sandbox" and prod_cat == "prod_lakehouse"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Declarative IaC**: Define all Databricks pipelines and resources as code in version-controlled YAML.
# MAGIC - **Target Overrides**: Dynamically alter catalogs, clusters, and permissions per target environment.
# MAGIC - **Development Mode**: `mode: development` isolates developer deployments to user sandboxes.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. What are Databricks Asset Bundles (DABs) and why did Databricks introduce them over classic Terraform?
# MAGIC 2. How does variable scoping work across different deployment targets in `databricks.yml`?
