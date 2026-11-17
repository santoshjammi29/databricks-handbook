# 🚨 Production Runbook 03: Streaming Checkpoint & RocksDB State Corruption Recovery

> **Incident Severity**: SEV-1 (Real-Time Pipeline Failure / SLA Breach)  
> **Target Systems**: Spark Structured Streaming, RocksDB State Store, Cloud Storage Checkpoints  
> **Recovery Objective**: Restore streaming ingestion, prevent data loss or duplicate records, and repair checkpoint metadata within 15 minutes.

---

## 1. Emergency Decision Tree

```
               [Streaming Alert: StreamingQueryException / StateStoreProviderException]
                                                   │
                                      Inspect Streaming Driver Log
                                                   │
                    ┌──────────────────────────────┴──────────────────────────────┐
                    ▼                                                             ▼
     [RocksDB Corruption / OOM]                                   [Checkpoint Metadata Desync]
   (RocksDBException / Out of Mem)                              (Offset / Commit Log Mismatch)
                    │                                                             │
        Check State Memory Footprint                                  Did upstream topic/folder
        and Event-Time Watermark                                      purge uncommitted offsets?
                    │                                                             │
            ┌───────┴───────┐                                             ┌───────┴───────┐
            ▼               ▼                                             ▼               ▼
          [Leak]          [Spill]                                       [YES]           [NO]
        Tighten         Configure NVMe                                Rewind Stream   Reconcile Head
        Watermark       RocksDB Local                                 to Earliest     Commit JSON and
        and State       Storage off-heap                              Available       Restart Stream
        TTL             options                                       Offset
```

### 📐 Visual Architectural Blueprint: Spark Streaming State Store & RocksDB
![Spark Streaming State Store Architecture](../assets/whiteboards/spark_streaming_state_store.webp)

### 📐 Visual Architectural Blueprint: Streaming DLQ Recovery Flow
![Streaming DLQ Recovery Flow](../assets/whiteboards/streaming_dlq_recovery_flow_architecture.webp)

---

## 2. Forensic Inspection Steps

### 2.1 Identify Corrupted Checkpoint Batch
Inspect the checkpoint directory structure in Unity Catalog Volumes:

```python
checkpoint_dir = "/Volumes/prod_catalog/metadata/checkpoints/orders_stream"

# List offsets and commits
offsets = dbutils.fs.ls(f"{checkpoint_dir}/offsets")
commits = dbutils.fs.ls(f"{checkpoint_dir}/commits")

latest_offset = sorted([int(f.name) for f in offsets])[-1]
latest_commit = sorted([int(f.name) for f in commits])[-1]

print(f"Latest Offset Batch: {latest_offset}")
print(f"Latest Commit Batch: {latest_commit}")

# If latest_offset > latest_commit, batch latest_offset failed mid-execution
if latest_offset > latest_commit:
    print(f"WARNING: Batch {latest_offset} is uncommitted and must be retried or rolled back.")
```

---

## 3. Surgical Recovery Procedures

### 3.1 Scenario A: Clean Rollback to Last Committed Batch
If an uncommitted batch wrote partial state to RocksDB, safely rollback the offset marker:

```python
# 1. Stop the failing streaming query gracefully
# 2. Delete the uncommitted offset file
uncommitted_batch = latest_offset
dbutils.fs.rm(f"{checkpoint_dir}/offsets/{uncommitted_batch}")

# 3. Clean any partial state delta for that uncommitted batch in RocksDB state store
dbutils.fs.rm(f"{checkpoint_dir}/state/0/0/{uncommitted_batch}.delta", recurse=True)

# 4. Restart the stream; Structured Streaming will re-read from latest_commit + 1
```

### 3.2 Scenario B: Off-Heap RocksDB State Store Configuration
To prevent driver/executor heap exhaustion from multi-million-key stateful aggregations, enforce native RocksDB off-heap memory storage:

```python
spark.conf.set(
    "spark.sql.streaming.stateStore.providerClass",
    "com.databricks.sql.streaming.state.RocksDBStateStoreProvider"
)
spark.conf.set("spark.sql.streaming.stateStore.rocksdb.compactOnCommit", "true")
spark.conf.set("spark.sql.streaming.stateStore.rocksdb.maxOpenFileLimit", "1000")
```

---

## 4. Permanent Architectural Safeguards

1. **Mandatory Event-Time Watermarking**: Never deploy stateful aggregations (`groupBy()`) or stream-stream joins without an explicit `.withWatermark("event_time", "2 hours")` to bound state size.
2. **Dedicated Checkpoint Volume**: Store checkpoints in high-performance Unity Catalog Managed Volumes (`/Volumes/catalog/schema/volume`), never on legacy DBFS root.
3. **Idempotent Sinks via `foreachBatch`**: Use `MERGE INTO` in the micro-batch writer so that replaying a rolled-back batch produces zero duplicate records.
