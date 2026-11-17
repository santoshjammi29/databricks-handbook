# 🚨 Production Runbook 02: Delta Concurrent Modification Conflict Resolution

> **Incident Severity**: SEV-2 (Data Pipeline Job Failure)  
> **Target Systems**: Delta Lake 3.x, Optimistic Concurrency Control (OCC), Row-Level Concurrency  
> **Recovery Objective**: Isolate concurrent writers, resolve transaction log commit collisions, and ensure idempotent job retries within 10 minutes.

---

## 1. Emergency Decision Tree

```
               [Delta Error: ConcurrentModificationException / ConcurrentAppendException]
                                                   │
                                      Inspect Transaction History
                                        (DESCRIBE HISTORY table)
                                                   │
                    ┌──────────────────────────────┴──────────────────────────────┐
                    ▼                                                             ▼
       [Append vs. Append Conflict]                                  [Update vs. Update Conflict]
                    │                                                             │
         Did target table enable                                       Are both writers touching
        Row-Level Concurrency (RLC)?                                  the same physical files?
                    │                                                             │
            ┌───────┴───────┐                                             ┌───────┴───────┐
            ▼               ▼                                             ▼               ▼
          [NO]            [YES]                                         [YES]           [NO]
        Enable          Transient File                                 Narrow down     Enable
        Row Tracking    Collision;                                     MERGE Predicate Deletion Vectors
        & Deletion      Auto-Retry                                     with Partition  (delta.enable
        Vectors         (maxRetries=5)                                 Pruning         DeletionVectors)
```

---

## 2. Forensic Inspection Queries

Execute these SQL commands in Databricks SQL or a notebook to determine which transactions collided:

```sql
-- 1. Inspect recent commits and identify conflicting operations
DESCRIBE HISTORY prod_catalog.silver.orders LIMIT 10;

-- 2. Check table properties to verify if concurrency optimizations are active
SHOW TBLPROPERTIES prod_catalog.silver.orders;

-- 3. Query system audit logs to find the colliding jobs and cluster IDs
SELECT 
    event_time,
    user_identity.email AS triggered_by,
    request_params.table_full_name AS table_name,
    service_name,
    response.status_code
FROM system.access.audit
WHERE request_params.table_full_name = 'prod_catalog.silver.orders'
  AND event_time >= NOW() - INTERVAL 2 HOURS
ORDER BY event_time DESC;
```

---

## 3. Surgical Remediation

### 3.1 Immediate Hotfix: Upgrade Table to Row-Level Concurrency
Enable Deletion Vectors and Row Tracking to allow concurrent DML against distinct rows in the same Parquet file:

```sql
ALTER TABLE prod_catalog.silver.orders SET TBLPROPERTIES (
  'delta.enableDeletionVectors' = true,
  'delta.enableRowTracking' = true
);
```

### 3.2 Partition-Pruned Merge Predicate
If two concurrent jobs execute `MERGE INTO`, ensure each merge explicitly includes a partition or clustering filter so the transactions scan and lock completely disjoint file subsets:

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, "prod_catalog.silver.orders")

# BAD: Full-table scan locks all files
# delta_table.merge(source_df, "target.order_id = source.order_id")

# GOOD: Explicit date range predicate prunes target files, eliminating conflict
delta_table.alias("target").merge(
    source_df.alias("source"),
    "target.order_date = source.order_date AND target.order_id = source.order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

---

## 4. Permanent Architectural Safeguards

1. **Stagger Scheduled Jobs**: Avoid scheduling simultaneous batch writers against the same target Delta table at the top of the hour.
2. **Switch to Lakeflow Declarative Pipelines (DLT)**: DLT automatically sequences streaming tables and materialized views, avoiding concurrent lock conflicts natively.
3. **Exponential Backoff in PySpark**: Wrap ad-hoc `MERGE` commands in Python retry blocks with exponential backoff:

```python
import time
from delta.exceptions import ConcurrentModificationException

def resilient_merge(merge_func, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return merge_func()
        except ConcurrentModificationException as e:
            if attempt == max_attempts - 1:
                raise e
            sleep_time = (2 ** attempt) + (time.time() % 1)
            time.sleep(sleep_time)
```
