# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 074. Unit Testing Databricks Data Pipelines with pytest, chispa & Mock DataFrames
# MAGIC **Module**: Module 07: Enterprise DevOps — DABs, CI/CD & Testing
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A team experiences pipeline regressions when code changes accidentally alter decimal rounding logic. Data transformations must be validated by automated unit test suites before deployment.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop modular unit test suites using pytest and `chispa.assert_df_equality`, validating both positive schema/value parity and negative regression catching.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC `chispa` provides clean DataFrame assertion helpers (`assert_df_equality`) highlighting row, value, and schema mismatches in CI test output without brittle manual `.collect()` loops.
# COMMAND ----------

from chispa.dataframe_comparer import assert_df_equality
from pyspark.sql import functions as F
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Unit Test with `chispa.assert_df_equality` & Regression Detection
# MAGIC
# MAGIC Compare actual transformed Spark output against an expected DataFrame via `assert_df_equality`, then prove a buggy transformation fails `assert_df_equality` cleanly.
# COMMAND ----------

def calculate_net_amount(df):
    return df.withColumn("net_amount", F.round(F.col("gross") - F.col("discount"), 2))

mock_input = spark.createDataFrame(
    [(100.00, 10.00), (250.50, 25.50), (50.00, 0.00)],
    ["gross", "discount"],
)
expected_df = spark.createDataFrame(
    [(100.00, 10.00, 90.00), (250.50, 25.50, 225.00), (50.00, 0.00, 50.00)],
    ["gross", "discount", "net_amount"],
)

df_result = calculate_net_amount(mock_input)
assert_df_equality(df_result, expected_df, ignore_nullable=True)

# Negative gate: confirm chispa rejects a buggy transform missing subtraction
buggy_df = mock_input.withColumn("net_amount", F.col("gross"))
mismatch_caught = False
try:
    assert_df_equality(buggy_df, expected_df, ignore_nullable=True)
except Exception:
    mismatch_caught = True

results = [row["net_amount"] for row in df_result.orderBy("gross").collect()]
print(f"Computed Net Amounts: {results}, mismatch_caught={mismatch_caught}")
assert mismatch_caught is True and len(results) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Decouple Transformations**: Write business logic as pure functions accepting and returning DataFrames.
# MAGIC - **Expressive Diffs**: `chispa.assert_df_equality` pinpoints exact mismatched cells and schema differences.
# MAGIC - **Automated CI Guardrail**: Run local Spark unit tests in seconds on every Pull Request.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you test PySpark data transformations in CI/CD without spinning up an expensive Databricks cluster?
# MAGIC 2. What is `chispa` and how does `assert_df_equality` improve PySpark test assertions?
