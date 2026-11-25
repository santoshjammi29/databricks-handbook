# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 043. Metaprogramming DLT: Dynamic Pipeline Generation from Data Contracts & YAML Specs
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A large platform ingests 200 distinct ERP tables. Writing 200 individual DLT notebook files is repetitive and error-prone. The pipeline must generate tables dynamically from YAML data contracts.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Develop a metaprogramming framework using Python decorators and loops to instantiate DLT streaming tables, schemas, and expectations dynamically from a configuration dictionary.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Because DLT pipelines are written in standard Python, developers can dynamically generate `@dlt.table` definitions inside loops, reading table names, schemas, and expectation rules from external YAML contracts.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Dynamic DLT Table Generator Pattern
# MAGIC
# MAGIC Iterate over table metadata specifications and instantiate DLT tables dynamically.
# COMMAND ----------

# Simulating metadata-driven DLT table generator
table_contracts = [
    {"name": "orders", "source": "/landing/orders", "primary_key": "order_id"},
    {"name": "line_items", "source": "/landing/line_items", "primary_key": "item_id"},
    {"name": "payments", "source": "/landing/payments", "primary_key": "payment_id"}
]

def generate_pipeline_definitions(contracts: list):
    generated_tables = []
    for contract in contracts:
        table_def = f"Instantiated DLT Table: {contract['name']} from {contract['source']} (PK: {contract['primary_key']})"
        generated_tables.append(table_def)
    return generated_tables

tables = generate_pipeline_definitions(table_contracts)
for t in tables:
    print(t)
assert len(tables) == 3
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Metadata-Driven Engineering**: Add new tables to the pipeline simply by updating a YAML configuration file.
# MAGIC - **Maintainability**: Standardize ingestion rules, audit columns, and error handling across hundreds of tables.
# MAGIC - **Contract Enforcement**: Integrates directly with enterprise Data Contracts.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Python closure scoping affect dynamic DLT table generation inside loops?
# MAGIC 2. What are the best practices for passing external configuration files into a DLT pipeline?
