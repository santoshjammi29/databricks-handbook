# 🚨 Production Runbook 05: Serverless SQL Warehouse Queueing & Spill Tuning

> **Incident Severity**: SEV-2 (BI Dashboard Degradation / Query Timeout Spikes)  
> **Target Systems**: Databricks SQL (DBSQL), Serverless SQL Warehouses, Photon Engine, Intelligent Workload Management (IWM)  
> **Recovery Objective**: Eliminate query queue times, stop disk spills, and restore sub-second BI query latency within 10 minutes.

---

## 1. Emergency Decision Tree

```
               [Alert: BI Dashboard Latency Spike / DBSQL Query Timeout]
                                           │
                         Inspect DBSQL Query Profile & Queuing
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
    [High Queuing Time (> 5s)]                                  [High Execution Time]
  (Queries Waiting in IWM Queue)                              (Query Spilling or Full Table Scan)
             │                                                           │
 Did concurrency exceed cluster limit?                         Check Query Profile Metrics
             │                                                           │
     ┌───────┴───────┐                                           ┌───────┴───────┐
     ▼               ▼                                           ▼               ▼
   [YES]           [NO]                                    [Disk Spill]     [Zero Pruning]
 Increase Max    Switch Scaling                          Scale T-Shirt    Apply Liquid
 Clusters on     Policy from                             Size (S -> L)    Clustering
 Warehouse       Economy to Pro                          to increase      (CLUSTER BY filter_col)
                                                         RAM per query
```

### 📐 Visual Architectural Blueprint: Catalyst Optimizer & Vectorized Photon C++ Engine
![Catalyst & Photon Engine Architecture](../assets/whiteboards/catalyst_photon_engine.webp)

---

## 2. Forensic Investigation Queries

Execute these system queries to diagnose warehouse saturation and identify runaway queries:

```sql
-- 1. Identify queries with severe queuing times in the last 1 hour
SELECT 
    query_id,
    executed_by,
    warehouse_id,
    query_text,
    duration_ms,
    waiting_for_compute_ms AS queue_time_ms,
    rows_produced,
    spill_to_disk_bytes
FROM system.compute.query_history
WHERE start_time >= NOW() - INTERVAL 1 HOUR
  AND waiting_for_compute_ms > 3000
ORDER BY waiting_for_compute_ms DESC
LIMIT 15;

-- 2. Check cluster scaling events on the target warehouse
SELECT 
    event_time,
    warehouse_name,
    cluster_count,
    active_query_count,
    queued_query_count
FROM system.compute.warehouse_events
WHERE warehouse_name = 'Analytics BI Warehouse'
  AND event_time >= NOW() - INTERVAL 2 HOURS
ORDER BY event_time DESC;
```

---

## 3. Surgical Remediation & Warehouse Tuning

### 3.1 Immediate Hotfix: Scale Warehouse Max Clusters & Size
1. In Databricks SQL Console, open **SQL Warehouses** -> Target Warehouse -> **Edit**.
2. **Increase Max Clusters**: If BI reports spike during Monday morning executive reviews, raise `Max Clusters` from `2` to `6`.
3. **Switch Scaling Policy**: Change Scaling Policy from `Economy` (waits for consistent backlog before launching nodes) to `Pro` (scales immediately upon detecting queued queries).
4. **Auto-Stop Optimization**: Ensure Auto-Stop is set to `10 minutes` for Serverless (serverless clusters start in 2–4 seconds, eliminating the cold-start penalty).

### 3.2 Query Optimization: Eliminate Disk Spill with Liquid Clustering
If high execution time is caused by reading 500 GB of Parquet for a query that returns 100 rows, cluster the underlying Delta table:

```sql
-- Replace full scans with sub-second Hilbert-curve file skipping
ALTER TABLE prod_catalog.gold.fact_sales CLUSTER BY (customer_id, transaction_date);
OPTIMIZE prod_catalog.gold.fact_sales;
```

---

## 4. Permanent Architectural Prevention

1. **Materialized Views for BI**: Pre-aggregate repeated dashboard queries into Materialized Views in Databricks SQL:
   ```sql
   CREATE MATERIALIZED VIEW prod_catalog.gold.mv_daily_sales_summary AS
   SELECT transaction_date, region, SUM(amount) AS total_revenue
   FROM prod_catalog.silver.sales_transactions
   GROUP BY transaction_date, region;
   ```
2. **Workload Separation**: Never share a single SQL warehouse between scheduled heavy reporting jobs (e.g., Tableau extract refreshes) and ad-hoc executive dashboard browsing.
3. **Query Limits**: Enforce maximum execution timeout limits (e.g., 600 seconds) in warehouse configuration to automatically terminate accidental Cartesian products.
