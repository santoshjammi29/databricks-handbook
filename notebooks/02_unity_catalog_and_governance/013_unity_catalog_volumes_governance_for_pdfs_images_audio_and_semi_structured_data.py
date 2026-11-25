# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 013. Unity Catalog Volumes: Governance for PDFs, Images, Audio & Semi-Structured Data
# MAGIC **Module**: Module 02: Unity Catalog — Governance, Security & Federation
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC An insurance company processes scanned claim documents (PDFs and JPEG damage photos). Compliance requires auditing who accesses which claim file and restricting access based on adjusters' group membership.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Create and manage Unity Catalog Volumes (`/Volumes/catalog/schema/volume`), upload unstructured files, query file metadata with SQL, and enforce access privileges.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Volumes represent governed storage objects in Unity Catalog that provide POSIX-compatible filesystem access to unstructured files, machine learning models, and raw data files. Managed Volumes reside in schema storage; External Volumes point to customer cloud buckets.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Volume Creation and File Operation Simulation
# MAGIC
# MAGIC Create a volume and demonstrate reading files via standard Python file I/O.
# COMMAND ----------

# Simulate Unity Catalog volume path resolution
volume_path = "/Volumes/prod_lakehouse/claims/raw_documents"
sample_file = f"{volume_path}/claim_1001_damage_report.pdf"

print(f"Target Volume Path: {volume_path}")
print(f"Sample POSIX File Access: {sample_file}")

# Standard Python POSIX path compatibility test
assert sample_file.startswith("/Volumes/"), "Volume path must conform to /Volumes/<catalog>/<schema>/<volume>"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **POSIX Compatibility**: Volumes can be read using standard Python libraries (`open()`, `PIL`, `pypdf`, `torch`).
# MAGIC - **Fine-Grained Auditing**: Every file read or write via Volumes is recorded in `system.access.audit`.
# MAGIC - **Governance Standard**: Volumes replace legacy DBFS mounts for unstructured data.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do Unity Catalog Volumes differ from traditional relational tables in Databricks?
# MAGIC 2. Can machine learning libraries like PyTorch or HuggingFace load model checkpoints directly from Volumes?
