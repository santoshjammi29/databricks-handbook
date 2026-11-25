# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 033. Auto Loader (cloudFiles): Incremental Lexical Directory Listing vs. File Notifications
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T0 Reference`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A logistics enterprise ingests IoT telematics files landing in cloud storage from 50,000 delivery vehicles. Ingestion must scale smoothly as file volume grows from thousands to millions of files per day without missing files.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Implement and compare Databricks Auto Loader (`cloudFiles`) using (1) Incremental Directory Listing and (2) File Notification mode (AWS SQS / Azure Event Grid), explaining scaling thresholds and cost trade-offs.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Auto Loader uses Structured Streaming to discover new files incrementally. Directory listing uses lexical scans and timestamp bounds. File notification mode provisions cloud event queues (Event Grid/SNS) to push file events, avoiding slow directory listings at petabyte scale.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Production Auto Loader Pipeline with cloudFiles
# MAGIC
# MAGIC Configure an end-to-end Auto Loader stream reading JSON payloads into Bronze.
# COMMAND ----------

# Production Auto Loader stream template
def get_autoloader_stream(source_path: str, schema_path: str, checkpoint_path: str, use_notifications: bool = False):
    stream_reader = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", schema_path)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("rescuedDataColumn", "_rescued_data")
    )
    if use_notifications:
        stream_reader = stream_reader.option("cloudFiles.useNotifications", "true")

    return stream_reader.load(source_path)

print("Auto Loader stream generator configured.")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Directory Listing (< 1M files)**: Zero cloud infrastructure setup; fast and cost-effective.
# MAGIC - **File Notification (> 1M files)**: Provisions SQS / Storage Queue automatically to scale to millions of files.
# MAGIC - **RocksDB State**: Auto Loader tracks processed files in an embedded RocksDB state store, guaranteeing exactly-once ingestion.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Auto Loader guarantee exactly-once file processing even if the streaming cluster restarts?
# MAGIC 2. What cloud resources does Auto Loader automatically create when `cloudFiles.useNotifications = true` is set?
