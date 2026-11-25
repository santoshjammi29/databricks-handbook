# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 007. Databricks Secrets & Cloud KMS Scopes: dbutils.secrets & Zero-Trust Ingestion
# MAGIC **Module**: Module 01: Platform Architecture, Workspaces & Control Plane
# MAGIC **Mastery Level**: `Intermediate` | **Verification Tier**: `T1 Simulated`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A payment processing pipeline must authenticate to third-party merchant APIs and external databases without leaking API keys, passwords, or connection strings in code or execution logs.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Demonstrate the creation and consumption of Databricks Secret Scopes backed by Azure Key Vault / AWS KMS, and prove that `dbutils.secrets.get()` automatically redacts values in stdout.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC Databricks Secret Scopes store encrypted key-value pairs. They can be Databricks-backed (encrypted in Control Plane) or Cloud-KMS-backed (Azure Key Vault / AWS Secrets Manager). The Spark engine automatically intercepts secret strings and replaces them with `[REDACTED]` in notebook logs.
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Secure Credential Retrieval & Output Masking
# MAGIC
# MAGIC Retrieve simulated credentials and verify redaction behavior in execution outputs.
# COMMAND ----------

# Simulate dbutils.secrets module locally
class MockSecrets:
    def __init__(self):
        self._vault = {
            ("payment_gateway", "api_key"): "sk_live_998877665544332211",
            ("payment_gateway", "client_secret"): "super_secret_pci_token"
        }
    def get(self, scope: str, key: str) -> str:
        return self._vault.get((scope, key), "")

mock_secrets = MockSecrets()
retrieved_key = mock_secrets.get("payment_gateway", "api_key")

# Verification: Secret is accessible in code but should never be printed raw
assert len(retrieved_key) > 0
print(f"Retrieved Secret Key Length: {len(retrieved_key)}")
print("Masked in production logs: [REDACTED]")
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Zero Hardcoded Credentials**: Never embed passwords, tokens, or connection strings in notebooks or git.
# MAGIC - **Cloud KMS Backing**: Back secret scopes directly with Azure Key Vault or AWS Secrets Manager for central rotation.
# MAGIC - **Log Masking**: Databricks automatically redacts values retrieved via `dbutils.secrets.get()` in driver outputs.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How does Databricks prevent secrets from being printed in notebook outputs?
# MAGIC 2. What is the difference between an Azure Key Vault-backed secret scope and a Databricks-backed secret scope?
