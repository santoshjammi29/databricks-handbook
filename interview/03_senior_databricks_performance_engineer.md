# 🎓 Databricks Interview Guide — Tier 3: Senior Performance & Systems Engineer (Deep Dive)

> **Focus Areas**: Catalyst AQE, Photon C++ Engine, Memory Triage & GC, Stateful Streaming & RocksDB, System Tables FinOps, and Dynamic Governance.

---

### Q3.1: How does the Photon Engine achieve $2\times$ to $5\times$ performance acceleration over standard Apache Spark?

**Answer:**  
Photon is Databricks' vectorized query engine written entirely in C++:
1. **Vectorized Execution**: Processes batches of data (typically tuples of 2,048 rows) at a time using CPU SIMD (Single Instruction, Multiple Data) instructions, maximizing modern CPU instruction pipelines.
2. **Direct Off-Heap Memory Management**: Completely bypasses the JVM heap. Allocates and manages raw memory off-heap in C++, eliminating JVM object overhead, pointer chasing, and JVM Garbage Collection (GC) pauses.
3. **Hardware-Level Optimization**: Optimizes CPU cache line utilization ($L1/L2/L3$ caches) and branch prediction by processing columnar primitives in contiguous memory arrays.
4. **Transparent Spark SQL Interoperability**: Executes alongside Apache Spark. When Catalyst encounters operators supported by Photon (scans, joins, aggregations, filters), it offloads them to Photon; unsupported operations gracefully fall back to the JVM.

---

### Q3.2: Explain Adaptive Query Execution (AQE) in Apache Spark 3.5+ and its three primary runtime optimizations.

**Answer:**  
AQE re-plans and optimizes query physical execution plans *dynamically at runtime* based on accurate runtime shuffle statistics collected at stage boundaries:
1. **Dynamically Coalescing Shuffle Partitions**:
   - If `spark.sql.shuffle.partitions` is set to 200, but the data after filtering is only 10 MB, AQE coalesces the 200 tiny partitions into 1 or 2 optimal partitions, eliminating task scheduling overhead.
2. **Dynamically Switching Join Strategies**:
   - If the optimizer initially planned a Sort-Merge Join because a table was estimated at 100 MB, but runtime filtering reduces it to 8 MB (below `spark.sql.autoBroadcastJoinThreshold`), AQE converts the physical plan to a Broadcast Hash Join (BHJ), eliminating a massive shuffle stage.
3. **Dynamically Optimizing Skew Joins**:
   - If one partition in a join contains 10 GB while all others contain 50 MB, AQE detects the skew, splits the 10 GB partition into smaller sub-partitions, and replicates matching keys from the opposing table to parallelize the join across multiple workers.

---

### Q3.3: How do you perform root-cause analysis on a Spark job that hangs at the 99% task completion mark?

**Answer:**  
A job hanging at 99% is almost always caused by **severe data skew** (one task processing 100x more records than all other parallel tasks) or an unpartitioned window function:
1. **Spark UI Stage Inspection**: Open the Stage Details tab and sort the **Task Metrics** table by `Duration` and `Shuffle Read Size`.
2. **Compare Median vs. Max**:
   - If the 50th percentile (Median) task duration is 4 seconds, but the Max task duration is 45 minutes, severe skew is confirmed.
3. **Identify the Skewed Key**: Examine the join key distribution in a temporary notebook:
   ```sql
   SELECT join_key, COUNT(*) FROM large_table GROUP BY join_key ORDER BY COUNT(*) DESC LIMIT 5;
   ```
4. **Remediation**:
   - Verify `spark.sql.adaptive.skewJoin.enabled = true`.
   - If AQE cannot split the partition (e.g., in complex non-equi joins or custom UDFs), implement **two-phase deterministic key salting**.

---

### Q3.4: How does Spark Structured Streaming manage stateful memory using RocksDB, and how do you prevent state store leaks?

**Answer:**  
In stateful streaming (windowed aggregations, stream-stream joins, `mapGroupsWithState`):
1. **State Store Mechanics**: Spark maintains intermediate state in memory. By default, the HDFS backed state store keeps all state in the JVM heap, causing OOMs as state grows.
2. **RocksDB State Store Provider**:
   - Databricks leverages RocksDB as an off-heap embedded key-value store.
   - RocksDB spills cold state to local NVMe SSD disks and keeps only hot keys in off-heap C++ memory, enabling state sizes of tens of terabytes without JVM GC pressure.
3. **Preventing State Memory Leaks**:
   - **Mandatory Event-Time Watermarking**: Always specify `.withWatermark("timestamp_col", "2 hours")`. This tells the engine when an event time is too late to update state, allowing RocksDB to physically purge expired keys from disk and memory.
   - **State TTL**: For arbitrary stateful operations (`flatMapGroupsWithState`), configure explicit Time-To-Live (TTL) timeouts to evict inactive sessions.

---

### Q3.5: How do you query Unity Catalog System Tables (`system.billing.usage`) to detect high-cost anomalies and calculate DBU spend?

**Answer:**  
Unity Catalog exposes billing and telemetry metadata via account-level system tables:
```sql
-- Calculate 30-day DBU consumption and estimated cost grouped by SKU and Workspace
SELECT 
    usage_date,
    sku_name,
    workspace_id,
    SUM(usage_quantity) AS total_dbus,
    ROUND(SUM(usage_quantity * 0.30), 2) AS estimated_cost_usd -- Assuming $0.30/DBU rate
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY usage_date, sku_name, workspace_id
ORDER BY total_dbus DESC;
```
**FinOps Actions**:
- Identify All-Purpose clusters running during off-hours and enforce automated cluster policies with 15-minute auto-termination.
- Flag scheduled workflows running on All-Purpose compute instead of Job Compute.
