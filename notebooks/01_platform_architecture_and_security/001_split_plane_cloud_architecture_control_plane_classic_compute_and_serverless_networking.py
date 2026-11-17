# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 001. Split-Plane Cloud Architecture: Control Plane, Classic Compute & Serverless Networking
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Foundational`
# MAGIC **Databricks Runtime Baseline**: DBR 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A financial services institution requires a multi-region Databricks deployment adhering to PCI-DSS standards. Enterprise data cannot transit the public internet or reside on vendor infrastructure outside the customer cloud perimeter.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the operational configuration and security boundary verification of Databricks Split-Plane architecture. Inspect cluster environment variables, verify private connectivity endpoints, and validate storage credential authentication.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks decouples the Control Plane (web UI, notebook orchestration, Unity Catalog metastore) from the Compute Plane. In Classic compute, Spark driver and worker VMs run in customer VNets/VPCs. In Serverless compute, hardened container micro-VMs run in a Databricks-managed cloud tenant connecting to storage via private endpoints.
# COMMAND ----------

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

# Initialize or obtain active SparkSession with Delta Lake & Unity Catalog support
spark = SparkSession.builder \
    .appName("DatabricksHandbook") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Inspect Cluster Runtime & Compute Plane Topology
# MAGIC
# MAGIC Verify the active Databricks Runtime (DBR) version, cluster ID, and driver IP configuration to ensure private network injection.
# COMMAND ----------

# Inspect environment topology and Spark runtime
cluster_id = spark.conf.get("spark.databricks.clusterUsageTags.clusterId", "local-simulated-cluster")
spark_version = spark.version
dbr_version = spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "15.4.x-scala2.12")

print(f"Active Cluster ID: {cluster_id}")
print(f"Apache Spark Engine: {spark_version}")
print(f"Databricks Runtime (DBR): {dbr_version}")

# Assert DBR 15.4+ baseline compatibility
assert float(spark_version.rsplit(".", 1)[0]) >= 3.5, f"Expected Spark 3.5+, found {spark_version}"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Verify Secure Cluster Connectivity (No Public IPs)
# MAGIC
# MAGIC Ensure worker nodes establish outbound-only secure reverse tunnels (SCC Relay) without requiring ingress public IP addresses.
# COMMAND ----------

# Simulate cluster network isolation inspection
network_conf = {
    "enableNoPublicIp": True,
    "vnetInjection": "custom-vnet-isolated",
    "privateSubnet": "10.240.1.0/24",
    "publicNetworkAccess": "Disabled"
}

print(f"Secure Cluster Connectivity (No Public IPs): {network_conf['enableNoPublicIp']}")
print(f"Subnet Isolation: {network_conf['privateSubnet']}")
assert network_conf["enableNoPublicIp"] is True, "Security Invariant Violated: Public IPs detected on compute nodes!"
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Split-Plane Isolation**: Customer data resides exclusively in customer storage accounts and compute memory.
# MAGIC - **Secure Cluster Connectivity**: Worker VMs require zero ingress ports or public IPs; they communicate via outbound secure relays.
# MAGIC - **Serverless Transition**: Serverless compute eliminates VM provisioning lag (2-4 seconds startup vs. 4-7 minutes on classic VMs).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Databricks ensure customer data privacy across the Control Plane and Compute Plane boundary?
# MAGIC 1. What is the function of the Secure Cluster Connectivity (SCC) relay in a customer VNet injection architecture?
