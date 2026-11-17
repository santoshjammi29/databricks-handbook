# 🚨 Production Runbook 01: Driver & Executor OutOfMemory (OOM) Forensic Triage

> **Incident Severity**: SEV-1 (Production Pipeline Outage)  
> **Target Systems**: Apache Spark 3.5+, Databricks Runtime (DBR 15.4+ LTS), Driver & Executor JVMs  
> **Recovery Objective**: Identify root memory leak, terminate runaway tasks, and restore pipeline execution within 15 minutes.

---

## 1. Emergency Decision Tree

```
                       [Spark Job Fails: java.lang.OutOfMemoryError]
                                           │
                              Where Did the Failure Occur?
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
       [Driver OOM]                                                [Executor OOM]
  (OutOfMemoryError / Exit 137)                              (Container Killed by YARN/K8s)
             │                                                           │
   Did code call .collect()?                                   Check Shuffle Disk Spill in UI
             │                                                           │
     ┌───────┴───────┐                                           ┌───────┴───────┐
     ▼               ▼                                           ▼               ▼
   [YES]           [NO]                                        [High]          [Low]
 Eliminate      Driver-Side Broadcast                     Severe Data Skew   Tungsten Off-Heap
 .collect()     Threshold Exceeded                        Salting Mitigation Exceeded / Huge Rows
 or use         (spark.sql.auto                           (salt join key)    (scale worker VM
 .take(100)      BroadcastJoinThreshold)                                     or lower partition size)
```

### 📐 Visual Architectural Blueprint: Spark Memory Management & Tungsten Spill
![Spark Memory Management & Spill](../assets/whiteboards/spark_memory_management_spill_diagram.webp)

---

## 2. Immediate Diagnostic Procedures

### 2.1 Identify Driver vs. Executor Root Cause
Examine the Databricks Driver Logs (`log4j` / standard error):

```bash
# Search for JVM termination signatures
grep -Ei "OutOfMemoryError|Container killed by YARN for exceeding memory limits|Exit code 137" driver_stderr.log
```

- **Driver OOM (`java.lang.OutOfMemoryError: Java heap space`)**:
  - **Symptom**: Cluster remains running but UI hangs; notebook disconnected; driver restarts.
  - **Root Causes**:
    1. Calling `df.collect()`, `df.toPandas()`, or `display()` on an unpartitioned 50M-row dataset.
    2. Over-broadcasting: Broadcasting a DataFrame larger than `spark.driver.maxResultSize` or physical driver RAM.
    3. Inefficient Driver Aggregations: Accumulating massive Python lists/dictionaries on the driver.
- **Executor OOM (`Exit code 137` / `Container killed`)**:
  - **Symptom**: Task fails with `ExecutorLostFailure (executor X exited caused by one of the running tasks)`.
  - **Root Causes**:
    1. **Data Skew**: A single partition contains 10 GB while all others contain 50 MB, overwhelming one executor's heap.
    2. **Tungsten Buffer Depletion**: Massive arrays/strings (> 32 MB per row) exceeding Tungsten binary row limits.
    3. **Excessive PySpark Python Worker Heap**: Un-vectorized Python UDFs buffering millions of rows in Python worker sub-processes.

---

## 3. Surgical Remediation & Recovery Scripts

### 3.1 Immediate Driver Relief (Hotfix)
If a scheduled production job fails due to Driver OOM, immediately apply these cluster configuration overrides in the Job settings:

```json
{
  "spark_conf": {
    "spark.driver.memory": "16g",
    "spark.driver.maxResultSize": "8g",
    "spark.sql.autoBroadcastJoinThreshold": "10485760"
  }
}
```

### 3.2 Executor Skew Remediation (Two-Phase Salting)
Replace failing skewed joins with deterministic two-phase salting:

```python
import pyspark.sql.functions as F

# 1. Salt the skewed large DataFrame across 16 random buckets
SALT_BUCKETS = 16
df_large_salted = df_large.withColumn("_salt", F.concat(F.col("skewed_key"), F.lit("_"), F.floor(F.rand() * SALT_BUCKETS)))

# 2. Replicate the small lookup DataFrame across all 16 buckets
df_small_replicated = df_small.withColumn("_salt_array", F.array([F.lit(i) for i in range(SALT_BUCKETS)])) \
                              .withColumn("_sub_salt", F.explode("_salt_array")) \
                              .withColumn("_salt", F.concat(F.col("skewed_key"), F.lit("_"), F.col("_sub_salt"))) \
                              .drop("_salt_array", "_sub_salt")

# 3. Execute uniform hash join with zero memory spill
df_joined = df_large_salted.join(df_small_replicated, on="_salt").drop("_salt")
```

---

## 4. Permanent Architectural Prevention

1. **Mandatory AQE Configuration**: Verify `spark.sql.adaptive.enabled = true` and `spark.sql.adaptive.skewJoin.enabled = true` are active in all cluster policies.
2. **Code Linting Invariant**: Ban `df.collect()` and `df.toPandas()` in production code reviews. Mandate `.take(n)` or writing directly to Delta tables.
3. **Photon Engine Adoption**: Migrate compute to Photon-enabled nodes; Photon's C++ off-heap memory manager eliminates JVM garbage collection pauses and heap fragmentation.
