# ⚡ Databricks Technical Mastery: 50 Rapid-Fire Flashcards

> **Format**: Question & Immediate Senior Architect Answer  
> **Coverage**: 5 Questions per module across all 10 modules in the Databricks Handbook curriculum.

---

### Module 01: Platform Architecture, Workspaces & Security
1. **Q: What is the primary difference between Control Plane and Compute Plane?**  
   **A:** Control plane runs in Databricks cloud tenant (UI, scheduler, metastore); compute plane runs in customer VNet or Databricks-managed serverless containers where Spark processes execute.
2. **Q: Why should scheduled production jobs never run on All-Purpose Compute?**  
   **A:** All-Purpose compute costs $2\times$ to $3\times$ more DBUs per hour than Job Compute and lacks automated ephemeral cluster lifecycle management.
3. **Q: What does `enableNoPublicIp = true` do on Databricks clusters?**  
   **A:** Enforces Secure Cluster Connectivity (SCC) where worker VMs have zero public IP addresses and communicate outbound-only over private tunnels.
4. **Q: How do you retrieve a secret securely in Databricks code?**  
   **A:** Use `dbutils.secrets.get(scope="my_scope", key="my_key")`, which redacts the plaintext value from execution logs.
5. **Q: What is the replacement for legacy `/mnt/` DBFS mounts in modern Databricks?**  
   **A:** Unity Catalog Managed and External Volumes (`/Volumes/catalog/schema/volume_name`).

---

### Module 02: Unity Catalog — Governance, Security & Federation
6. **Q: What is the 3-level namespace in Unity Catalog?**  
   **A:** `catalog.schema.table_or_volume_or_model`.
7. **Q: What happens physically when you run `DROP TABLE` on a Managed vs. External Table?**  
   **A:** Managed table deletes both metadata and underlying cloud Parquet files; External table deletes metadata only, leaving cloud files intact.
8. **Q: How do you implement Dynamic Row-Level Security in Unity Catalog?**  
   **A:** Create a SQL function returning a boolean (`IS_ACCOUNT_GROUP_MEMBER()`) and attach it via `ALTER TABLE ... SET ROW FILTER func ON (col)`.
9. **Q: What is Lakehouse Federation?**  
   **A:** Querying remote database engines (Snowflake, BigQuery, Postgres) directly through Unity Catalog foreign catalogs with predicate pushdown and zero ETL.
10. **Q: What open protocol allows sharing Delta tables with non-Databricks consumers without copying data?**  
    **A:** Delta Sharing.

---

### Module 03: Delta Lake 3.x Storage Engine
11. **Q: What file records atomic commits in Delta Lake?**  
    **A:** Sequentially numbered JSON commit files in the `_delta_log/` directory (e.g., `000000.json`).
12. **Q: How do Deletion Vectors (Merge-on-Read) improve DML performance?**  
    **A:** Instead of rewriting an entire 500 MB Parquet file on update/delete, Delta writes a small roaring bitmap (.dv) of deleted row offsets, speeding writes by up to $100\times$.
13. **Q: What replaces Hive directory partitioning and Z-Ordering in Delta Lake 3.x?**  
    **A:** Liquid Clustering (`CLUSTER BY`), which uses incremental Hilbert-curve space-filling algorithms.
14. **Q: Can Liquid Clustering keys be changed without rewriting historical table data?**  
    **A:** Yes, via `ALTER TABLE ... CLUSTER BY (...)`; newly appended data clusters on the new keys during subsequent `OPTIMIZE`.
15. **Q: What is Delta UniForm?**  
    **A:** Automatic background generation of Apache Iceberg and Hudi metadata alongside Delta commits so external engines can read Delta tables natively.

---

### Module 04: Lakeflow Ingestion & DLT
16. **Q: What are the two file discovery modes in Databricks Auto Loader?**  
    **A:** Incremental Directory Listing (default, lexical scan) and File Notification Mode (AWS SQS / Azure Event Grid).
17. **Q: What is the purpose of the `_rescued_data` column in Auto Loader?**  
    **A:** To capture unparseable, malformed, or data-type-mismatched fields as JSON without failing the ingestion stream.
18. **Q: In Delta Live Tables, what is the difference between a Streaming Table and a Materialized View?**  
    **A:** Streaming tables ingest append-only streams incrementally; Materialized views precompute results and update based on current upstream state.
19. **Q: What are the three DLT expectation severity levels?**  
    **A:** `expect` (log metric only), `expect_or_drop` (drop invalid rows), `expect_or_fail` (terminate pipeline immediately).
20. **Q: What DLT function performs CDC upserts for SCD Type 1 and Type 2?**  
    **A:** `dlt.apply_changes()`.

---

### Module 05: Lakeflow Jobs & Orchestration
21. **Q: How do tasks in a Lakeflow Job pass dynamic values to downstream tasks?**  
    **A:** `dbutils.jobs.taskValues.set(key, value)` in the upstream task and `dbutils.jobs.taskValues.get(taskKey, key)` in downstream tasks.
22. **Q: What is the advantage of Serverless Jobs over classic job clusters?**  
    **A:** Zero VM allocation latency (starts in seconds), automated horizontal concurrency, and no cluster configuration maintenance.
23. **Q: What does the "Repair and Rerun" feature do in Databricks Workflows?**  
    **A:** Re-runs only the failed tasks and their downstream dependencies without re-executing successful upstream tasks.
24. **Q: Why should production jobs run as a Service Principal instead of a user?**  
    **A:** To prevent pipeline failures when employees leave the company, change passwords, or have tokens revoked.
25. **Q: What trigger type should be used to run a job immediately when new files land in cloud storage?**  
    **A:** File Arrival Trigger.

---

### Module 06: Databricks SQL & Photon Engine
26. **Q: What programming language is the Photon Engine written in, and why?**  
    **A:** C++; to achieve SIMD-vectorized execution, direct off-heap memory management, and zero JVM garbage collection pauses.
27. **Q: What is Intelligent Workload Management (IWM) in SQL Warehouses?**  
    **A:** Databricks' dynamic admission control that queues queries when compute is saturated and predicts runtime to prevent memory spills.
28. **Q: What are the three layers of caching in Databricks SQL?**  
    **A:** Result Cache (UI/query level), Local SSD Disk/Delta Cache (executor level), and Remote Cloud Storage metadata cache.
29. **Q: What is the difference between Economy and Pro scaling policies on SQL Warehouses?**  
    **A:** Economy delays scaling out clusters until a consistent queue forms (optimizes cost); Pro scales out immediately upon detecting queued queries (optimizes latency).
30. **Q: What Databricks feature provides a conversational AI interface over curated lakehouse SQL data?**  
    **A:** Databricks Genie Spaces.

---

### Module 07: Enterprise DevOps & DABs
31. **Q: What is a Databricks Asset Bundle (DAB)?**  
    **A:** A declarative Infrastructure as Code (IaC) framework defined in YAML (`databricks.yml`) to deploy workflows, pipelines, apps, and schemas.
32. **Q: What does `databricks bundle validate` do?**  
    **A:** Performs offline and online syntax, variable substitution, and schema validation of all YAML bundle resources.
33. **Q: What is the behavioral difference between `mode: development` and `mode: production` in DABs?**  
    **A:** Development prefixes resources with user names, pauses schedules, and cleans up; Production enforces branch locks and unpauses schedules.
34. **Q: How does GitHub Actions authenticate to Databricks securely without static tokens?**  
    **A:** OpenID Connect (OIDC) cloud federation with Azure Federated Credentials or AWS IAM Roles.
35. **Q: What tool enables local IDE development in VS Code while executing against remote Databricks clusters?**  
    **A:** Databricks Connect v2.

---

### Module 08: Databricks Apps & Mosaic AI
36. **Q: What is Databricks Apps?**  
    **A:** Serverless hosting inside the Databricks workspace for Python web applications (Streamlit, Dash, Gradio, FastAPI).
37. **Q: What configuration file defines a Databricks App manifest?**  
    **A:** `app.yaml`.
38. **Q: What is a Delta Sync Index in Databricks Vector Search?**  
    **A:** A vector index that automatically and continuously syncs embeddings from an underlying Delta table as new rows are inserted or updated.
39. **Q: Where are MLflow models registered in modern Databricks?**  
    **A:** In Unity Catalog using the 3-level namespace (`catalog.schema.model_name`).
40. **Q: What SQL function allows invoking an LLM directly in a Databricks SQL query?**  
    **A:** `ai_query(endpoint_name, prompt)`.

---

### Module 09: FinOps & System Tables
41. **Q: Which system table tracks all DBU consumption across workspaces?**  
    **A:** `system.billing.usage`.
42. **Q: How do you enforce cost attribution by department in Databricks?**  
    **A:** Mandate cluster tagging (`CostCenter`, `Owner`, `Project`) via Cluster Policies; tags propagate directly into `system.billing.usage`.
43. **Q: Which system table tracks user logins, permission grants, and notebook edits?**  
    **A:** `system.access.audit`.
44. **Q: What is the recommended auto-stop idle timeout for Serverless SQL Warehouses?**  
    **A:** 5 to 10 minutes (serverless clusters start in 2–4 seconds, eliminating cold start delays).
45. **Q: What cloud VM architecture migration typically saves 30–40% on worker compute costs?**  
    **A:** Migrating to ARM-based instances (AWS Graviton or Azure ARM VM families).

---

### Module 10: Production Incidents & Blueprints
46. **Q: What is the most common cause of a Driver OutOfMemoryError in PySpark?**  
    **A:** Executing `df.collect()` or `df.toPandas()` on large distributed DataFrames, which forces all worker partitions into the driver JVM heap.
47. **Q: How do you resolve a `ConcurrentAppendException` when two jobs write to the same Delta table?**  
    **A:** Enable Deletion Vectors and Row Tracking (`delta.enableDeletionVectors = true`, `delta.enableRowTracking = true`) for Row-Level Concurrency.
48. **Q: How do you fix an unpartitioned window function causing stragglers?**  
    **A:** Add a `PARTITION BY` column to distribute rows across worker nodes, or rewrite using pre-aggregations.
49. **Q: What does a high `waiting_for_compute_ms` in `system.compute.query_history` indicate?**  
    **A:** Severe query queuing on the SQL Warehouse caused by insufficient maximum cluster concurrency.
50. **Q: What is the first recovery step when an uncommitted batch corrupts a Structured Streaming checkpoint?**  
    **A:** Remove the uncommitted offset file from `offsets/` and partial state delta from `state/` to rewind the stream to the last successful commit.
