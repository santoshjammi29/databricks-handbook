# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 037. DLT Data Quality Expectations: expect, expect_or_drop, and expect_or_fail
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial data pipeline must enforce data quality rules: non-critical format anomalies should be tracked, invalid discount rates should be dropped, and negative ledger amounts must halt the pipeline immediately.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Deploy and test the three DLT Data Quality Expectation actions: `@dlt.expect`, `@dlt.expect_or_drop`, and `@dlt.expect_or_fail`.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DLT Expectations declare data quality constraints as SQL boolean expressions. DLT tracks pass/fail rates in the event log and takes automated actions: logging metrics (`expect`), filtering invalid rows (`expect_or_drop`), or failing the run (`expect_or_fail`).
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. DLT Expectations Severity Matrix
# MAGIC
# MAGIC Evaluate how DLT handles each expectation level upon detecting invalid data.
# COMMAND ----------

expectations_matrix = {
    "warn_only": {
        "decorator": '@dlt.expect("valid_email", "email LIKE \'%@%\'")',
        "action": "Records metric in event log; row continues downstream"
    },
    "drop_record": {
        "decorator": "@dlt.expect_or_drop('valid_age', 'age >= 18')",
        "action": "Drops invalid row from target table; records metric in event log"
    },
    "fail_pipeline": {
        "decorator": "@dlt.expect_or_fail('positive_balance', 'balance >= 0')",
        "action": "Immediately terminates pipeline run; fails transaction"
    }
}

for level, details in expectations_matrix.items():
    print(f"[{level.upper()}]\n  Syntax: {details['decorator']}\n  Behavior: {details['action']}\n")

assert "@dlt.expect_or_fail" in expectations_matrix["fail_pipeline"]["decorator"]
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **`expect`**: Non-blocking observability for soft quality rules.
# MAGIC - **`expect_or_drop`**: Surgical filtering for invalid rows without halting processing.
# MAGIC - **`expect_or_fail`**: Circuit breaker for critical financial/compliance invariants.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. Where are DLT expectation pass and fail metrics recorded for auditing?
# MAGIC 2. Can you apply multiple expectations with different severity levels to the same DLT table?
