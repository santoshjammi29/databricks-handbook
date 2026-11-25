"""
Module 09: FinOps, Observability & System Tables Masterclass (Notebooks 088 - 098)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "09_finops_and_system_tables"
MODULE_NAME = "Module 09: FinOps, Observability & System Tables Masterclass"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "088",
            "title": "System Tables Architecture: Enabling and Navigating billing, access, and compute",
            "filename": "088_system_tables_architecture_enabling_and_navigating_billing_access_and_compute.py",
            "difficulty": "Foundational",
            "business_scenario": "An enterprise Cloud Center of Excellence (CCoE) needs automated visibility into compute usage, security audits, and storage optimization without managing custom logging pipelines.",
            "problem_statement": "Enable Unity Catalog System Tables at the account level, explore system schemas (`system.billing`, `system.access`, `system.compute`, `system.storage`), and verify metadata query permissions.",
            "architectural_notes": "System Tables are a Databricks-hosted analytical store of operational telemetry. They reside in the `system` catalog, populated automatically and queryable via standard SQL with zero data egress or pipeline maintenance.",
            "sections": [
                {
                    "title": "1. System Tables Schema Hierarchy & Scope",
                    "explanation": "Map operational domains to their corresponding system tables.",
                    "code": """system_table_schemas = {
    "system.billing.usage": "Historical DBU consumption records across all workspaces, SKUs, and cluster tags",
    "system.access.audit": "Audit logs capturing user logins, table access, DDL, and permission grants",
    "system.compute.clusters": "Cluster lifecycle events, node configurations, and creation metadata",
    "system.compute.query_history": "DBSQL query execution metrics, durations, rows produced, and memory spills",
    "system.storage.predictive_optimization_operations_history": "Telemetry on serverless OPTIMIZE and VACUUM jobs"
}

for tbl, desc in system_table_schemas.items():
    print(f"[{tbl}]\\n  Purpose: {desc}\\n")

assert "system.billing.usage" in system_table_schemas
"""
                }
            ],
            "key_takeaways": [
                "Zero-ETL Observability: Operational metrics appear automatically in the `system` catalog.",
                "Account-Level Visibility: Queries aggregate data across all workspaces in the cloud account.",
                "Granular Retention: Retains long-term historical telemetry (typically 1 year) for compliance audits."
            ],
            "interview_questions": [
                "How do you enable Unity Catalog System Tables for an entire Databricks account?",
                "What system tables provide visibility into query execution bottlenecks and cluster utilization?"
            ]
        },
        {
            "nb_id": "089",
            "title": "Calculating DBU Consumption & Cloud Costs via system.billing.usage",
            "filename": "089_calculating_dbu_consumption_and_cloud_costs_via_system_billing_usage.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "A FinOps analyst needs to produce a daily executive report calculating total DBU spend, converting DBUs to currency based on contract rates, and identifying cost drivers.",
            "problem_statement": "Execute Spark SQL aggregations over local telemetry modeled after `system.billing.usage` to calculate daily DBU consumption by workspace and SKU, converting DBUs to dollar costs with contract rates.",
            "architectural_notes": "`system.billing.usage` records hourly DBU usage across workspaces (`workspace_id`, `sku_name`, `usage_quantity`). Locally we materialize the identical table schema as a Spark temp view and run the production SQL aggregation.",
            "sections": [
                {
                    "title": "1. FinOps DBU Aggregation Query Execution in Spark SQL",
                    "explanation": "Load hourly DBU telemetry modeled after `system.billing.usage` into a Spark view and aggregate cost drivers by SKU and workspace.",
                    "code": """billing_records = [
    ("2026-11-20", "STANDARD_ALL_PURPOSE_COMPUTE", "ws-prod-01", 120.5),
    ("2026-11-20", "JOBS_COMPUTE", "ws-prod-01", 410.0),
    ("2026-11-20", "SERVERLESS_SQL", "ws-bi-02", 85.0),
    ("2026-11-21", "STANDARD_ALL_PURPOSE_COMPUTE", "ws-prod-01", 290.0),
    ("2026-11-21", "JOBS_COMPUTE", "ws-prod-01", 400.0),
]
spark.createDataFrame(
    billing_records, ["usage_date", "sku_name", "workspace_id", "usage_quantity"]
).createOrReplaceTempView("billing_usage")

# Equivalent to querying Databricks account `system.billing.usage`
daily_cost_df = spark.sql(\"\"\"
    WITH daily_usage AS (
        SELECT usage_date, sku_name, workspace_id, SUM(usage_quantity) AS total_dbus
        FROM billing_usage
        GROUP BY 1, 2, 3
    )
    SELECT
        usage_date,
        sku_name,
        workspace_id,
        ROUND(total_dbus, 2) AS dbus,
        ROUND(total_dbus * 0.35, 2) AS estimated_cost_usd
    FROM daily_usage
    ORDER BY dbus DESC
\"\"\")

rows = daily_cost_df.collect()
total_usd = round(sum(r["estimated_cost_usd"] for r in rows), 2)
print(f"Top DBU consumer SKU: {rows[0]['sku_name']} ({rows[0]['dbus']} DBUs) | Total Spend: ${total_usd}")
assert rows[0]["sku_name"] == "JOBS_COMPUTE"
assert total_usd > 400.0
""",
                }
            ],
            "key_takeaways": [
                "Accurate SKU Tracking: Distinguish between high-cost Interactive compute and cost-effective Job compute.",
                "Contract Normalization: Multiply DBUs by contracted tier rates to calculate exact monthly cloud spend.",
                "Proactive Budgeting: Monitor daily burn rates to forecast end-of-month budget overages.",
            ],
            "interview_questions": [
                "What is the difference between `usage_quantity` in `system.billing.usage` and the underlying cloud VM cost?",
                "How does `system.billing.usage` capture serverless compute versus classic compute consumption?",
            ],
        },
        {
            "nb_id": "090",
            "title": "Mandatory Cluster Tagging (CostCenter, Environment, Owner) & Cost Attribution",
            "filename": "090_mandatory_cluster_tagging_costcenter_environment_owner_and_cost_attribution.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "Finance cannot allocate a $500,000 monthly Databricks bill to business units because 60% of clusters were launched without `CostCenter` or `Project` tags.",
            "problem_statement": "Parse the `custom_tags` map in Spark SQL over billing telemetry to attribute 100% of DBU spend across `CostCenter` and `Project` codes and quarantine untagged cluster leaks.",
            "architectural_notes": "Cluster policies enforce `custom_tags.CostCenter`, propagating automatically into `system.billing.usage.custom_tags` (`MAP<STRING, STRING>`).",
            "sections": [
                {
                    "title": "1. Query Tagged Costs & Untouched Leak Detection in Spark SQL",
                    "explanation": "Materialize `custom_tags` MapType telemetry in Spark SQL, coalesce untagged clusters as `UNALLOCATED_LEAK`, and compute cost-attribution share.",
                    "code": """tagged_rows = [
    ("2026-11-20", {"CostCenter": "FIN-100", "Project": "RISK_DW"}, 300.0),
    ("2026-11-20", {"CostCenter": "MKT-220", "Project": "ATTRIBUTION"}, 180.0),
    ("2026-11-20", {"Owner": "contractor"}, 120.0),  # Missing CostCenter!
]
spark.createDataFrame(tagged_rows, ["usage_date", "custom_tags", "usage_quantity"]).createOrReplaceTempView(
    "billing_usage_tagged"
)

attr_df = spark.sql(\"\"\"
    SELECT
        COALESCE(custom_tags['CostCenter'], 'UNALLOCATED_LEAK') AS cost_center,
        COALESCE(custom_tags['Project'], 'GENERAL') AS project,
        SUM(usage_quantity) AS total_dbus,
        ROUND(SUM(usage_quantity * 0.30), 2) AS cost_usd
    FROM billing_usage_tagged
    GROUP BY 1, 2
    ORDER BY total_dbus DESC
\"\"\")

by_cc = {r["cost_center"]: r["cost_usd"] for r in attr_df.collect()}
print(f"Cost Attribution USD: {by_cc}")
assert by_cc["UNALLOCATED_LEAK"] == 36.0
assert by_cc["FIN-100"] == 90.0
""",
                }
            ],
            "key_takeaways": [
                "Enforce at Policy Level: Never rely on human memory for tagging; enforce via cluster policies.",
                "Unallocated Leak Hunting: Query for `custom_tags['CostCenter'] IS NULL` to isolate non-compliant workloads.",
                "Automated Chargeback: Export aggregated attribution tables directly to enterprise finance pipelines.",
            ],
            "interview_questions": [
                "How do cluster tags propagate into Databricks System Tables?",
                "How do you configure a Databricks Cluster Policy to mandate that users enter a valid 6-digit Cost Center code?",
            ],
        },
        {
            "nb_id": "091",
            "title": "Cost Breakdown Analysis: Interactive vs. Job vs. DBSQL vs. Serverless vs. DLT",
            "filename": "091_cost_breakdown_analysis_interactive_vs_job_vs_dbsql_vs_serverless_vs_dlt.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "A VP of Data Engineering wants to know whether recent platform modernization efforts (migrating batch jobs to DLT and Serverless) successfully reduced interactive development waste.",
            "problem_statement": "Execute a Spark SQL workload categorization pipeline mapping billing SKUs into five FinOps pillars (`Interactive`, `Jobs`, `DBSQL`, `DLT`, `Serverless`) and verify share percentages sum cleanly.",
            "architectural_notes": "Grouping `sku_name` prefixes reveals workload efficiency ratios. Mature Databricks platforms keep `ALL_PURPOSE` interactive spend below 20% and shift scheduled production pipelines to `JOBS`, `DLT`, or `SERVERLESS`.",
            "sections": [
                {
                    "title": "1. Workload Categorization & Share Window Function in Spark SQL",
                    "explanation": "Categorize billing SKU records using Spark SQL `CASE WHEN` + window share calculation and validate interactive waste thresholds.",
                    "code": """sku_samples = [
    ("PREMIUM_ALL_PURPOSE_COMPUTE", 150.0),
    ("JOBS_COMPUTE", 450.0),
    ("ENTERPRISE_SQL_PRO_COMPUTE", 200.0),
    ("DLT_ADVANCED_COMPUTE", 120.0),
    ("SERVERLESS_JOBS_COMPUTE", 80.0),
]
spark.createDataFrame(sku_samples, ["sku_name", "usage_quantity"]).createOrReplaceTempView(
    "billing_sku_samples"
)

breakdown_df = spark.sql(\"\"\"
    SELECT
        CASE
            WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Development'
            WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless Compute'
            WHEN sku_name LIKE '%JOBS%' THEN 'Automated Batch Jobs'
            WHEN sku_name LIKE '%SQL%' THEN 'Databricks SQL / BI'
            WHEN sku_name LIKE '%DLT%' THEN 'Delta Live Tables'
            ELSE 'Other Services'
        END AS workload_category,
        SUM(usage_quantity) AS total_dbus,
        ROUND(SUM(usage_quantity) * 100.0 / SUM(SUM(usage_quantity)) OVER (), 1) AS dbu_share_pct
    FROM billing_sku_samples
    GROUP BY 1
    ORDER BY total_dbus DESC
\"\"\")

cats = {r["workload_category"]: r["dbu_share_pct"] for r in breakdown_df.collect()}
total_pct = round(sum(cats.values()), 1)
print(f"Workload DBU shares (%): {cats} (sum={total_pct}%)")
assert total_pct == 100.0
assert cats["Interactive Development"] < 20.0
""",
                }
            ],
            "key_takeaways": [
                "Healthy Ratio Benchmark: Production enterprises target < 20% Interactive and > 80% Automated/Serverless spend.",
                "Migration ROI: Track declining `ALL_PURPOSE` shares as pipelines migrate to DABs and Lakeflow.",
                "Executive Summary: Translate raw billing SKUs into clear engineering pillar allocation.",
            ],
            "interview_questions": [
                "What is considered a healthy ratio of Interactive vs. Automated Job DBU consumption in an enterprise?",
                "How can you identify scheduled batch workloads incorrectly running under an `ALL_PURPOSE` SKU?",
            ],
        },
        {
            "nb_id": "092",
            "title": "Audit & Security Analytics: Investigating Access Logs with system.access.audit",
            "filename": "092_audit_and_security_analytics_investigating_access_logs_with_system_access_audit.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "business_scenario": "Following an employee departure, the security team needs a forensic audit of every table queried, exported, or modified by that employee during their final two weeks.",
            "problem_statement": "Run forensic Spark SQL queries over Unity Catalog audit telemetry modeled after `system.access.audit`, identifying bulk table exports, permission denials, and untrusted source IP addresses.",
            "architectural_notes": "`system.access.audit` captures immutable workspace authentication, SQL table reads, permission grants, and export events. Locally we query a structured audit log temp view capturing the identical nested JSON fields.",
            "sections": [
                {
                    "title": "1. Forensic User Activity & Exfiltration Investigation Query",
                    "explanation": "Query nested audit telemetry for offboarding forensics, flagging external IP table exports and failed authorization probes.",
                    "code": """audit_events = [
    ("2026-11-18T14:00:00Z", "ws-01", "former_employee@company.com", "getTable", "unityCatalog", "10.20.1.5", "prod.pii.customers", 200),
    ("2026-11-18T14:05:00Z", "ws-01", "former_employee@company.com", "exportResults", "databrickssql", "198.51.100.99", "prod.pii.customers", 200),
    ("2026-11-18T14:07:00Z", "ws-01", "former_employee@company.com", "getSecret", "secrets", "198.51.100.99", "prod_kv_scope/api_key", 403),
    ("2026-11-18T15:00:00Z", "ws-01", "etl_sp@company.com", "commitTransaction", "unityCatalog", "10.20.0.10", "prod.silver.orders", 200),
]
spark.createDataFrame(
    audit_events,
    ["event_time", "workspace_id", "user_email", "action_name", "service_name", "source_ip", "target_asset", "status_code"],
).createOrReplaceTempView("access_audit_events")

suspect_df = spark.sql(\"\"\"
    SELECT event_time, user_email, action_name, source_ip, target_asset, status_code
    FROM access_audit_events
    WHERE user_email = 'former_employee@company.com'
      AND (NOT source_ip LIKE '10.%' OR status_code >= 400)
    ORDER BY event_time
\"\"\")

suspect_rows = suspect_df.collect()
print(f"Flagged high-risk offboarding events: {len(suspect_rows)}")
assert len(suspect_rows) == 2
assert {r["action_name"] for r in suspect_rows} == {"exportResults", "getSecret"}
""",
                }
            ],
            "key_takeaways": [
                "Immutable Audit Trail: Account-level audit tables cannot be modified by workspace users or admins.",
                "IP Anomaly Detection: Correlate `source_ip_address` outside corporate CIDR blocks with export actions.",
                "SOC 2 Compliance: Automate post-offboarding access reviews cleanly in SQL.",
            ],
            "interview_questions": [
                "What specific user actions are tracked in `system.access.audit`?",
                "How can you detect anomalous large data downloads or notebook exports using audit telemetry?",
            ],
        },
        {
            "nb_id": "093",
            "title": "Compute Right-Sizing: Detecting Zombie Clusters & Low-CPU Utilization",
            "filename": "093_compute_right_sizing_detecting_zombie_clusters_and_low_cpu_utilization.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "An enterprise cluster audit discovered 15 interactive clusters that were left running overnight with 0% CPU utilization, wasting $1,200 per day in idle compute.",
            "problem_statement": "Join cluster uptime metadata with query execution history in Spark SQL to detect zombie clusters (`uptime > 2h` with `0` queries executed) and calculate reclaimable DBU waste.",
            "architectural_notes": "Correlating `system.compute.clusters` uptime windows against `system.compute.query_history` surfaces orphaned All-Purpose clusters that were left un-terminated or bypassed cluster auto-stop policies.",
            "sections": [
                {
                    "title": "1. Zombie Cluster SQL Correlation & Waste Quantification",
                    "explanation": "Join cluster telemetry with query execution logs in Spark SQL to flag zero-query zombie compute and compute daily wasted DBUs.",
                    "code": """clusters = [
    ("cl-001", "prod-etl-stream", 24.0, 16.0),
    ("cl-002", "analyst-sandbox-1", 14.0, 8.0),
    ("cl-003", "dev-scratch", 8.0, 4.0),
]
queries = [
    ("q-1", "cl-001", 1200),
    ("q-2", "cl-003", 180),
]
spark.createDataFrame(clusters, ["cluster_id", "cluster_name", "uptime_hours", "dbu_per_hour"]).createOrReplaceTempView("compute_clusters")
spark.createDataFrame(queries, ["query_id", "cluster_id", "exec_ms"]).createOrReplaceTempView("compute_queries")

zombies_df = spark.sql(\"\"\"
    SELECT
        c.cluster_id,
        c.cluster_name,
        c.uptime_hours,
        COUNT(q.query_id) AS queries_executed,
        ROUND(c.uptime_hours * c.dbu_per_hour, 2) AS wasted_dbus
    FROM compute_clusters c
    LEFT JOIN compute_queries q ON c.cluster_id = q.cluster_id
    GROUP BY c.cluster_id, c.cluster_name, c.uptime_hours, c.dbu_per_hour
    HAVING queries_executed = 0 AND uptime_hours > 2.0
\"\"\")

zombies = zombies_df.collect()
print(f"Detected zombie clusters: {[(z['cluster_id'], z['wasted_dbus']) for z in zombies]}")
assert len(zombies) == 1
assert zombies[0]["cluster_id"] == "cl-002" and zombies[0]["wasted_dbus"] == 112.0
""",
                }
            ],
            "key_takeaways": [
                "Eliminate Zombie Spend: Enforce 10–15 minute auto-termination on all interactive clusters via Cluster Policies.",
                "Right-Sizing Audits: Correlate cluster DBU burn with actual SQL/job query counts.",
                "Automated Remediation: Wire zombie-detection queries into Databricks Alerts + Cluster Termination API.",
            ],
            "interview_questions": [
                "How do you correlate compute cluster runtime with actual query activity to identify idle resources?",
                "What cluster policy settings prevent developers from disabling auto-termination?",
            ],
        },
        {
            "nb_id": "094",
            "title": "Evaluating Predictive Optimization ROI with system.storage.predictive_optimization",
            "filename": "094_evaluating_predictive_optimization_roi_with_system_storage_predictive_optimization.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "Leadership wants to verify that enabling Predictive Optimization in Unity Catalog actually saves money on storage and improves query performance rather than consuming excess serverless DBUs.",
            "problem_statement": "Execute a Spark SQL ROI calculation over predictive-optimization operation telemetry (`OPTIMIZE`, `VACUUM`), measuring small files eliminated, terabytes reclaimed, and net storage-vs-compute savings.",
            "architectural_notes": "`system.storage.predictive_optimization_operations_history` records every background `OPTIMIZE`, `VACUUM`, and `ANALYZE` execution along with `usage_quantity` (DBUs) and storage bytes reclaimed.",
            "sections": [
                {
                    "title": "1. Predictive Optimization Net ROI Query in Spark SQL",
                    "explanation": "Aggregate files eliminated, storage GB reclaimed, and net monthly savings (`storage_saved_usd - dbu_cost_usd`) across managed tables.",
                    "code": """po_ops = [
    ("fact_events", "OPTIMIZE", 1800, 0, 14.0),
    ("fact_events", "VACUUM", 0, 2400 * 1024 * 1024 * 1024, 2.0),
    ("dim_users", "OPTIMIZE", 120, 0, 1.5),
]
spark.createDataFrame(
    po_ops, ["table_name", "operation_type", "files_compacted", "bytes_purged", "dbus_used"]
).createOrReplaceTempView("po_history")

roi_df = spark.sql(\"\"\"
    SELECT
        table_name,
        SUM(files_compacted) AS files_eliminated,
        ROUND(SUM(bytes_purged) / POW(1024, 3), 2) AS gb_reclaimed,
        ROUND(SUM(dbus_used) * 0.40, 2) AS po_compute_cost_usd,
        ROUND((SUM(bytes_purged) / POW(1024, 3)) * 0.023, 2) AS monthly_storage_saved_usd
    FROM po_history
    GROUP BY table_name
    ORDER BY files_eliminated DESC
\"\"\")

roi_rows = {r["table_name"]: r for r in roi_df.collect()}
fact_row = roi_rows["fact_events"]
print(f"fact_events -> files_eliminated={fact_row['files_eliminated']}, gb_reclaimed={fact_row['gb_reclaimed']}, storage_saved=${fact_row['monthly_storage_saved_usd']}")
assert fact_row["files_eliminated"] == 1800
assert fact_row["monthly_storage_saved_usd"] > fact_row["po_compute_cost_usd"]
""",
                }
            ],
            "key_takeaways": [
                "Quantifiable Hygiene: Measure exact small-file reduction and purged GBs per table.",
                "Positive Net ROI: Reclaiming terabytes via automated `VACUUM` directly offsets serverless maintenance DBUs.",
                "Faster Reads: Eliminating thousands of tiny Parquet files cuts object-store listing latency dramatically.",
            ],
            "interview_questions": [
                "What metrics are recorded in `system.storage.predictive_optimization_operations_history`?",
                "How do you evaluate whether automated compaction is reducing downstream query scan times?",
            ],
        },
        {
            "nb_id": "095",
            "title": "Automated FinOps Anomaly Detection & Daily Budget Exceedance Alerting",
            "filename": "095_automated_finops_anomaly_detection_and_daily_budget_exceedance_alerting.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "business_scenario": "A buggy recursive query triggered by a contractor consumed 5,000 DBUs in 4 hours, causing a $2,000 billing surprise. FinOps requires automated anomaly detection alerting when daily spend spikes.",
            "problem_statement": "Implement an automated rolling 14-day Z-score ($Z = (X - \\mu)/\\sigma$) anomaly detector in Spark SQL over multi-day daily spend history and assert runaway spikes exceeding $3\\sigma$ trigger `CRITICAL_COST_ANOMALY`.",
            "architectural_notes": "Static dollar thresholds trigger false alarms during seasonal peaks. Moving 14-day baseline window functions (`AVG` and `STDDEV` with `ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING`) adapt automatically and isolate $3\\sigma$ outliers cleanly.",
            "sections": [
                {
                    "title": "1. Rolling 14-Day Z-Score Anomaly Detection in Spark SQL",
                    "explanation": "Generate a 16-day baseline with subtle daily variance followed by a runaway 4,500-DBU spike on Day 16, and execute Spark SQL rolling window statistics to classify alerts.",
                    "code": """daily_spend = [(f"2026-11-{d:02d}", float(500 + (d % 4) * 15)) for d in range(1, 16)]
daily_spend.append(("2026-11-16", 4500.0))  # Runaway contractor job spike!

spark.createDataFrame(daily_spend, ["usage_date", "daily_dbus"]).createOrReplaceTempView("daily_dbu_usage")

alerts_df = spark.sql(\"\"\"
    WITH stats AS (
        SELECT
            usage_date,
            daily_dbus,
            AVG(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_mean,
            STDDEV(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_std
        FROM daily_dbu_usage
    )
    SELECT
        usage_date,
        daily_dbus,
        ROUND(rolling_mean, 1) AS baseline_mean,
        ROUND((daily_dbus - rolling_mean) / NULLIF(rolling_std, 0), 2) AS z_score,
        CASE
            WHEN (daily_dbus - rolling_mean) / NULLIF(rolling_std, 0) > 3.0 THEN 'CRITICAL_COST_ANOMALY'
            WHEN (daily_dbus - rolling_mean) / NULLIF(rolling_std, 0) > 2.0 THEN 'WARNING_COST_SPIKE'
            ELSE 'NORMAL'
        END AS anomaly_status
    FROM stats
    ORDER BY usage_date DESC
\"\"\")

latest = alerts_df.first()
print(f"Day {latest['usage_date']}: {latest['daily_dbus']} DBUs (z={latest['z_score']}) -> {latest['anomaly_status']}")
assert latest["anomaly_status"] == "CRITICAL_COST_ANOMALY"
assert latest["z_score"] > 10.0
""",
                }
            ],
            "key_takeaways": [
                "Statistical Baselines: Avoid brittle static thresholds; use rolling 14-day z-scores excluding the current day (`1 PRECEDING`).",
                "Automate Alerts: Schedule the anomaly query in a DBSQL Alert connected to Slack/PagerDuty.",
                "Root-Cause Linkage: Join anomalies with top-consuming `cluster_id` or `job_id` for immediate triage.",
            ],
            "interview_questions": [
                "How do you implement statistical anomaly detection over Databricks billing telemetry?",
                "What action should an automated FinOps system take when a runaway query anomaly is detected?",
            ],
        },
        {
            "nb_id": "096",
            "title": "Spot Instance Fleet Optimization & AWS Graviton / Azure ARM VM Migrations",
            "filename": "096_spot_instance_fleet_optimization_and_aws_graviton_azure_arm_vm_migrations.py",
            "difficulty": "Intermediate",
            "business_scenario": "A large batch ETL infrastructure bill is $100,000 per month. The platform architect must cut VM infrastructure costs by 40% without compromising pipeline SLAs.",
            "problem_statement": "Evaluate Spot instance configuration and migrate worker fleets to ARM-based VM architectures (AWS Graviton3 / Azure Cobalt/ARM), analyzing price-performance benchmarks.",
            "architectural_notes": "Spot instances offer up to 70-80% discounts on cloud VM costs. Databricks handles Spot evictions gracefully in batch jobs. Migrating from x86 to ARM instances (e.g., `m6g` in AWS, `Dpsv5` in Azure) delivers 25-40% better price-performance.",
            "sections": [
                {
                    "title": "1. Spot & ARM Architecture Economics Matrix",
                    "explanation": "Compare hourly VM costs and eviction resilience between On-Demand and Spot ARM fleets.",
                    "code": """fleet_economics = {
    "x86_On_Demand": {"vm": "Standard_D8ds_v5", "hourly_vm_cost": 0.38, "spot_discount": "0%", "sla_risk": "Zero risk"},
    "x86_Spot_Workers": {"vm": "Standard_D8ds_v5", "hourly_vm_cost": 0.11, "spot_discount": "71%", "sla_risk": "Low (auto-replacement)"},
    "ARM_Graviton_Spot": {"vm": "Standard_D8ps_v5 (ARM)", "hourly_vm_cost": 0.08, "spot_discount": "79%", "sla_risk": "Low; 25% faster Photon execution"}
}

for arch, data in fleet_economics.items():
    print(f"[{arch}] Cost: ${data['hourly_vm_cost']}/hr | Discount: {data['spot_discount']} | Risk: {data['sla_risk']}")

assert fleet_economics["ARM_Graviton_Spot"]["hourly_vm_cost"] < 0.10
"""
                }
            ],
            "key_takeaways": [
                "Driver On-Demand, Workers Spot: Always keep the driver on On-Demand to prevent cluster termination on Spot loss.",
                "ARM Architecture Superiority: Photon's vectorized C++ code is highly optimized for ARM NEON SIMD registers.",
                "Batch ETL Savings: Massive multi-thousand-dollar savings on nightly batch processing."
            ],
            "interview_questions": [
                "Why must the driver node always be provisioned as On-Demand even when worker nodes use Spot instances?",
                "What performance advantages does the Photon engine realize on ARM-based cloud VMs?"
            ]
        },
        {
            "nb_id": "097",
            "title": "Aggressive Auto-Stop Policies & Cold Compute Idle Reduction Strategies",
            "filename": "097_aggressive_auto_stop_policies_and_cold_compute_idle_reduction_strategies.py",
            "difficulty": "Foundational",
            "business_scenario": "An audit found developers leaving clusters active during lunch breaks and overnight because the default 120-minute auto-termination was never changed.",
            "problem_statement": "Deploy cluster policies enforcing strict 10-15 minute auto-stop rules across all interactive compute, quantify idle cost reductions, and educate teams on serverless instant start.",
            "architectural_notes": "Idle compute is the single largest source of cloud waste in analytics platforms. Enforcing aggressive auto-stop policies and transitioning users to Serverless compute (which spins up in seconds) eliminates the developer friction of waiting for clusters.",
            "sections": [
                {
                    "title": "1. Idle Cost Waste Reduction Model",
                    "explanation": "Calculate annual savings from reducing auto-termination from 120 min to 15 min.",
                    "code": """def calculate_idle_savings(num_clusters: int, idle_events_per_day: int, dbu_hourly_rate: float = 0.35, dbu_per_cluster: int = 8):
    # Old policy: 120 min (2 hours) idle per event
    old_idle_hours_per_day = num_clusters * idle_events_per_day * 2.0
    # New policy: 15 min (0.25 hours) idle per event
    new_idle_hours_per_day = num_clusters * idle_events_per_day * 0.25
    
    saved_hours_per_day = old_idle_hours_per_day - new_idle_hours_per_day
    annual_cost_savings = saved_hours_per_day * dbu_per_cluster * dbu_hourly_rate * 365
    return {"saved_hours_daily": saved_hours_per_day, "annual_savings_usd": annual_cost_savings}

savings = calculate_idle_savings(num_clusters=25, idle_events_per_day=2)
print(f"Daily Wasted Hours Eliminated: {savings['saved_hours_daily']:.1f} hrs")
print(f"Annual Cloud Cost Savings: ${savings['annual_savings_usd']:,.2f}")
assert savings["annual_savings_usd"] > 50000
"""
                }
            ],
            "key_takeaways": [
                "15-Minute Standard: Enforce 10-15 minute idle termination in cluster policies for all interactive clusters.",
                "Serverless Migration: Serverless SQL Warehouses start in 2 seconds; set their auto-stop to 5-10 minutes.",
                "Tens of Thousands Saved: Small policy changes compound into massive annual cloud savings."
            ],
            "interview_questions": [
                "Why do developers resist short auto-stop timeouts, and how does Serverless compute resolve that friction?",
                "How can you audit which clusters frequently hit their auto-termination limit?"
            ]
        },
        {
            "nb_id": "098",
            "title": "Multi-Tenant Showback & Chargeback Dashboards for Enterprise Business Units",
            "filename": "098_multi_tenant_showback_and_chargeback_dashboards_for_enterprise_business_units.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "business_scenario": "The enterprise central IT department needs to bill back cloud infrastructure costs accurately to Marketing, Risk, Fraud, and Retail business units based on verified resource consumption.",
            "problem_statement": "Execute a proportional departmental chargeback allocation model in Spark SQL (direct cluster spend + shared platform infrastructure pool) and verify full bill reconciliation.",
            "architectural_notes": "Chargeback allocates direct compute costs by `BusinessUnit` tag and splits indirect `SHARED_INFRA` platform spend proportionally by direct consumption weight so 100% of billing invoices reconcile to finance ledgers.",
            "sections": [
                {
                    "title": "1. Multi-Tenant Chargeback Allocation & Reconciliation Query",
                    "explanation": "Execute a weighted CTE chargeback query in Spark SQL and assert the summed tenant bills reconcile 100% with total platform spend.",
                    "code": """bu_usage = [
    ("FINANCE", 1000.0),
    ("RISK_ML", 600.0),
    ("RETAIL_BI", 400.0),
    (None, 200.0),  # Untaggable SHARED_INFRA metastore & governance overhead
]
spark.createDataFrame(bu_usage, ["business_unit", "usage_quantity"]).createOrReplaceTempView(
    "billing_chargeback_src"
)

bill_df = spark.sql(\"\"\"
    WITH direct_costs AS (
        SELECT
            COALESCE(business_unit, 'SHARED_INFRA') AS business_unit,
            SUM(usage_quantity * 0.30) AS direct_spend_usd
        FROM billing_chargeback_src
        GROUP BY 1
    ),
    shared_pool AS (
        SELECT direct_spend_usd AS shared_amount
        FROM direct_costs
        WHERE business_unit = 'SHARED_INFRA'
    ),
    tenant_weights AS (
        SELECT
            business_unit,
            direct_spend_usd,
            direct_spend_usd / SUM(direct_spend_usd) OVER () AS weight
        FROM direct_costs
        WHERE business_unit != 'SHARED_INFRA'
    )
    SELECT
        t.business_unit,
        ROUND(t.direct_spend_usd, 2) AS direct_cost_usd,
        ROUND(t.weight * s.shared_amount, 2) AS allocated_shared_cost_usd,
        ROUND(t.direct_spend_usd + (t.weight * s.shared_amount), 2) AS total_monthly_bill_usd
    FROM tenant_weights t
    CROSS JOIN shared_pool s
    ORDER BY total_monthly_bill_usd DESC
\"\"\")

bills = {r["business_unit"]: r["total_monthly_bill_usd"] for r in bill_df.collect()}
total_billed = round(sum(bills.values()), 2)
raw_platform_usd = spark.sql("SELECT ROUND(SUM(usage_quantity * 0.30), 2) FROM billing_chargeback_src").first()[0]

print(f"Departmental Chargeback Bills: {bills} | Reconciled Total=${total_billed}")
assert bills["FINANCE"] == 330.0
assert abs(total_billed - raw_platform_usd) < 0.01
""",
                }
            ],
            "key_takeaways": [
                "Proportional Allocation: Fairly distribute shared platform overhead based on direct consumption weights.",
                "Full Ledger Reconciliation: Sum of tenant bills equals total Databricks invoice with zero unallocated remainder.",
                "Self-Policing Culture: Transparent chargeback nudges teams to right-size clusters and auto-stop rules.",
            ],
            "interview_questions": [
                "How do you handle shared, untagged platform costs in a multi-tenant Databricks chargeback model?",
                "What is the difference between a Showback model and a Chargeback model in enterprise FinOps?",
            ],
        }
    ]

    for nb_data in notebooks:
        fname = nb_data.pop("filename")
        nb_data["module_folder"] = MODULE_FOLDER
        nb_data["module_name"] = MODULE_NAME
        content = build_notebook(**nb_data)
        write_notebook(out_dir / fname, content)
    print(f"Generated {len(notebooks)} notebooks for {MODULE_FOLDER}")

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent
    generate(base_path)
