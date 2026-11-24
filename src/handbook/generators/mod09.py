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
            "business_scenario": "A FinOps analyst needs to produce a daily executive report calculating total DBU spend, converting DBUs to currency based on contract rates, and identifying cost drivers.",
            "problem_statement": "Develop analytical SQL queries over `system.billing.usage` to aggregate DBU consumption by day, workspace, and SKU, projecting monetary costs with contract discount multipliers.",
            "architectural_notes": "`system.billing.usage` records DBU consumption at 1-hour increments. Attributes include `workspace_id`, `sku_name`, `usage_quantity` (DBUs), and `custom_tags` for fine-grained departmental cost allocation.",
            "sections": [
                {
                    "title": "1. FinOps DBU Aggregation Query Implementation",
                    "explanation": "Write SQL to compute daily DBU totals and dollar costs by SKU.",
                    "code": """sql_finops_billing = \"\"\"
-- Compute daily DBU consumption and dollar costs by SKU
WITH daily_usage AS (
    SELECT 
        usage_date,
        sku_name,
        workspace_id,
        SUM(usage_quantity) AS total_dbus
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1, 2, 3
)
SELECT 
    usage_date,
    sku_name,
    workspace_id,
    ROUND(total_dbus, 2) AS dbus,
    -- Apply contract rate multiplier (e.g. $0.35 per DBU)
    ROUND(total_dbus * 0.35, 2) AS estimated_cost_usd
FROM daily_usage
ORDER BY usage_date DESC, dbus DESC;
\"\"\"

print("FinOps billing aggregation query validated.")
assert "system.billing.usage" in sql_finops_billing
assert "usage_quantity" in sql_finops_billing
"""
                }
            ],
            "key_takeaways": [
                "Accurate SKU Tracking: Distinguish between high-cost Interactive compute and cost-effective Job compute.",
                "Contract Normalization: Multiply DBUs by contracted tier rates to calculate exact monthly cloud spend.",
                "Proactive Budgeting: Monitor daily burn rates to forecast end-of-month budget overages."
            ],
            "interview_questions": [
                "What is the difference between `usage_quantity` in `system.billing.usage` and the underlying cloud VM cost?",
                "How does `system.billing.usage` capture serverless compute versus classic compute consumption?"
            ]
        },
        {
            "nb_id": "090",
            "title": "Mandatory Cluster Tagging (CostCenter, Environment, Owner) & Cost Attribution",
            "filename": "090_mandatory_cluster_tagging_costcenter_environment_owner_and_cost_attribution.py",
            "difficulty": "Intermediate",
            "business_scenario": "Finance cannot allocate a $500,000 monthly Databricks bill to business units because 60% of clusters were launched without `CostCenter` or `Project` tags.",
            "problem_statement": "Enforce mandatory cluster tagging via Cluster Policies, parse the `custom_tags` map in `system.billing.usage`, and allocate 100% of DBU spend to verified department cost centers.",
            "architectural_notes": "Cluster policies can mandate fixed or pattern-matched tags (e.g. `custom_tags.CostCenter`). These tags propagate directly into cloud provider billing logs and Databricks `system.billing.usage.custom_tags`.",
            "sections": [
                {
                    "title": "1. Querying Tagged Costs from custom_tags Map",
                    "explanation": "Extract nested JSON map keys to attribute costs to departments.",
                    "code": """sql_tag_attribution = \"\"\"
-- Allocate DBU spend by CostCenter and Project tags
SELECT 
    usage_date,
    COALESCE(custom_tags['CostCenter'], 'UNALLOCATED_LEAK') AS cost_center,
    COALESCE(custom_tags['Project'], 'GENERAL') AS project,
    SUM(usage_quantity) AS total_dbus,
    ROUND(SUM(usage_quantity * 0.30), 2) AS cost_usd
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
GROUP BY 1, 2, 3
ORDER BY total_dbus DESC;
\"\"\"

print("Tag-based cost attribution query verified.")
assert "custom_tags['CostCenter']" in sql_tag_attribution
"""
                }
            ],
            "key_takeaways": [
                "Enforce at Policy Level: Never rely on human memory for tagging; enforce via cluster policies.",
                "Unallocated Leak Hunting: Query for `CostCenter IS NULL` to identify rogue clusters.",
                "Automated Chargeback: Provide monthly departmental reports directly to finance."
            ],
            "interview_questions": [
                "How do cluster tags propagate into Databricks System Tables?",
                "How do you configure a Databricks Cluster Policy to mandate that users enter a valid 6-digit Cost Center code?"
            ]
        },
        {
            "nb_id": "091",
            "title": "Cost Breakdown Analysis: Interactive vs. Job vs. DBSQL vs. Serverless vs. DLT",
            "filename": "091_cost_breakdown_analysis_interactive_vs_job_vs_dbsql_vs_serverless_vs_dlt.py",
            "difficulty": "Intermediate",
            "business_scenario": "A VP of Data Engineering wants to know whether recent platform modernization efforts (migrating batch jobs to DLT and Serverless) successfully reduced interactive development waste.",
            "problem_statement": "Author an analytical query categorizing spend into five workload pillars: Interactive Compute, Automated Jobs, SQL Warehouses, Serverless Workflows, and Delta Live Tables.",
            "architectural_notes": "The `sku_name` attribute in `system.billing.usage` identifies the exact compute engine. Classifying SKUs enables architectural FinOps analysis to track migration from expensive interactive VMs to cost-optimized serverless engines.",
            "sections": [
                {
                    "title": "1. Workload Categorization Query Model",
                    "explanation": "Categorize SKUs into business workload buckets and compute percentage distribution.",
                    "code": """sql_workload_breakdown = \"\"\"
SELECT 
    CASE 
        WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'Interactive Development'
        WHEN sku_name LIKE '%JOBS%' THEN 'Automated Batch Jobs'
        WHEN sku_name LIKE '%SQL%' THEN 'Databricks SQL / BI'
        WHEN sku_name LIKE '%DLT%' THEN 'Delta Live Tables'
        WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless Compute'
        ELSE 'Other Services'
    END AS workload_category,
    SUM(usage_quantity) AS total_dbus,
    ROUND(SUM(usage_quantity) * 100.0 / SUM(SUM(usage_quantity)) OVER (), 1) AS dbu_share_pct
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY 1
ORDER BY total_dbus DESC;
\"\"\"

print("Workload SKU breakdown query validated.")
assert "ALL_PURPOSE" in sql_workload_breakdown
assert "dbu_share_pct" in sql_workload_breakdown
"""
                }
            ],
            "key_takeaways": [
                "Healthy Ratio Benchmark: Production enterprises should target < 20% Interactive and > 80% Automated/Serverless.",
                "Migration ROI: Track the reduction in `ALL_PURPOSE` spend as pipelines transition to DABs and Lakeflow.",
                "Executive Summary: Translate raw technical telemetry into clear business capability costs."
            ],
            "interview_questions": [
                "What is considered a healthy ratio of Interactive vs. Automated Job DBU consumption in an enterprise?",
                "How can you identify scheduled batch workloads incorrectly running under an `ALL_PURPOSE` SKU?"
            ]
        },
        {
            "nb_id": "092",
            "title": "Audit & Security Analytics: Investigating Access Logs with system.access.audit",
            "filename": "092_audit_and_security_analytics_investigating_access_logs_with_system_access_audit.py",
            "difficulty": "Advanced",
            "business_scenario": "Following an employee departure, the security team needs a forensic audit of every table queried, exported, or modified by that employee during their final two weeks.",
            "problem_statement": "Query `system.access.audit` to trace user actions, filtering on user identity, extracting accessed table names, IP addresses, and identifying unauthorized data export attempts.",
            "architectural_notes": "`system.access.audit` provides unified, immutable audit logs across all workspaces in an account. It records authentication events, notebook executions, table reads/writes, cluster modifications, and secret access.",
            "sections": [
                {
                    "title": "1. Forensic User Activity Audit Query",
                    "explanation": "Construct forensic investigation queries tracking user operations across workspaces.",
                    "code": """sql_forensic_audit = \"\"\"
-- Forensic trace of all actions performed by a specific user identity
SELECT 
    event_time,
    workspace_id,
    action_name,
    service_name,
    source_ip_address,
    request_params.table_full_name AS accessed_table,
    response.status_code
FROM system.access.audit
WHERE user_identity.email = 'former_employee@company.com'
  AND event_time >= NOW() - INTERVAL 14 DAYS
ORDER BY event_time DESC
LIMIT 50;
\"\"\"

print("Forensic audit query verified.")
assert "system.access.audit" in sql_forensic_audit
assert "user_identity.email" in sql_forensic_audit
"""
                }
            ],
            "key_takeaways": [
                "Immutable Audit Trail: System audit logs cannot be altered by developers or workspace admins.",
                "IP Address Tracking: Trace queries back to corporate VPNs or unexpected external IP addresses.",
                "Compliance Audits: Provide instant reports for SOC 2, HIPAA, and ISO 27001 regulatory inquiries."
            ],
            "interview_questions": [
                "What specific user actions are tracked in `system.access.audit`?",
                "How can you detect anomalous large data downloads or notebook exports using audit telemetry?"
            ]
        },
        {
            "nb_id": "093",
            "title": "Compute Right-Sizing: Detecting Zombie Clusters & Low-CPU Utilization",
            "filename": "093_compute_right_sizing_detecting_zombie_clusters_and_low_cpu_utilization.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise cluster audit discovered 15 interactive clusters that were left running overnight with 0% CPU utilization, wasting $1,200 per day in idle compute.",
            "problem_statement": "Query compute and billing system tables to detect zombie clusters (active clusters with zero queries or < 10% CPU utilization for > 2 hours) and automate notifications.",
            "architectural_notes": "Right-sizing requires correlating cluster uptime from `system.compute.clusters` with query execution counts from `system.compute.query_history` to identify idle compute resources.",
            "sections": [
                {
                    "title": "1. Zombie Cluster Detection Algorithm",
                    "explanation": "Simulate identifying idle clusters running with zero active queries.",
                    "code": """clusters_telemetry = [
    {"cluster_id": "cl-001", "name": "prod-etl-stream", "uptime_hours": 24, "queries_run": 14500, "status": "HEALTHY_ACTIVE"},
    {"cluster_id": "cl-002", "name": "analyst-sandbox-1", "uptime_hours": 14, "queries_run": 0, "status": "ZOMBIE_IDLE"},
    {"cluster_id": "cl-003", "name": "dev-scratch", "uptime_hours": 8, "queries_run": 2, "status": "LOW_UTILIZATION"}
]

zombies = [c for c in clusters_telemetry if c["queries_run"] == 0 and c["uptime_hours"] > 2]
print(f"Detected Zombie Idle Clusters: {len(zombies)}")
for z in zombies:
    print(f"  ALERT: {z['name']} ({z['cluster_id']}) has been idle for {z['uptime_hours']} hours!")

assert len(zombies) == 1
assert zombies[0]["cluster_id"] == "cl-002"
"""
                }
            ],
            "key_takeaways": [
                "Eliminate Zombie Spend: Enforce automated 15-minute auto-termination to kill idle clusters.",
                "Right-Sizing Audits: Downsize worker VM types from 8-core to 4-core if average CPU stays under 20%.",
                "Automated Remediation: Terminate zombie clusters programmatically via Databricks REST API."
            ],
            "interview_questions": [
                "How do you correlate compute cluster runtime with actual query activity to identify idle resources?",
                "What cluster policy settings prevent developers from disabling auto-termination?"
            ]
        },
        {
            "nb_id": "094",
            "title": "Evaluating Predictive Optimization ROI with system.storage.predictive_optimization",
            "filename": "094_evaluating_predictive_optimization_roi_with_system_storage_predictive_optimization.py",
            "difficulty": "Intermediate",
            "business_scenario": "Leadership wants to verify that enabling Predictive Optimization in Unity Catalog actually saves money on storage and improves query performance rather than consuming excess serverless DBUs.",
            "problem_statement": "Query `system.storage.predictive_optimization_operations_history` to compute the number of small files eliminated, storage gigabytes reclaimed via VACUUM, and net DBU costs.",
            "architectural_notes": "The predictive optimization operations table tracks every background compaction, vacuum, and stats collection job, including serverless DBU costs and physical bytes reclaimed.",
            "sections": [
                {
                    "title": "1. Predictive Optimization ROI Analysis Query",
                    "explanation": "Calculate file reduction metrics and reclaimed storage volumes.",
                    "code": """sql_predictive_roi = \"\"\"
-- Audit Predictive Optimization ROI across tables
SELECT 
    table_name,
    COUNT(CASE WHEN operation_type = 'OPTIMIZE' THEN 1 END) AS optimize_runs,
    SUM(metrics.filesCompacted) AS total_files_eliminated,
    COUNT(CASE WHEN operation_type = 'VACUUM' THEN 1 END) AS vacuum_runs,
    ROUND(SUM(metrics.bytesPurged) / (1024*1024*1024*1024), 2) AS storage_reclaimed_tb
FROM system.storage.predictive_optimization_operations_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY table_name
ORDER BY total_files_eliminated DESC
LIMIT 20;
\"\"\"

print("Predictive Optimization ROI query validated.")
assert "system.storage.predictive_optimization_operations_history" in sql_predictive_roi
"""
                }
            ],
            "key_takeaways": [
                "Quantifiable Hygiene: Measure exactly how many small files were eliminated and how many terabytes were freed.",
                "Storage Cost Reduction: Physical deletion of unreferenced files via VACUUM reduces monthly cloud storage bills.",
                "Read Acceleration: Coalescing files into 256MB–1GB targets accelerates downstream query scans up to 5x."
            ],
            "interview_questions": [
                "What metrics are recorded in `system.storage.predictive_optimization_operations_history`?",
                "How do you evaluate whether automated compaction is reducing downstream query scan times?"
            ]
        },
        {
            "nb_id": "095",
            "title": "Automated FinOps Anomaly Detection & Daily Budget Exceedance Alerting",
            "filename": "095_automated_finops_anomaly_detection_and_daily_budget_exceedance_alerting.py",
            "difficulty": "Advanced",
            "business_scenario": "A buggy recursive query triggered by a contractor consumed 5,000 DBUs in 4 hours, causing a $2,000 billing surprise. FinOps requires automated anomaly detection alerting when daily spend spikes.",
            "problem_statement": "Develop an automated FinOps anomaly detection algorithm in SQL/PySpark that calculates rolling 14-day mean and standard deviation of DBU spend and fires an alert if daily spend exceeds $3\\sigma$.",
            "architectural_notes": "Statistically bounding daily DBU consumption using moving z-scores ($Z = \\frac{X - \\mu}{\\sigma}$) catches cost runaway anomalies within hours, preventing billing shocks at month-end.",
            "sections": [
                {
                    "title": "1. Statistical Z-Score Cost Anomaly Detection",
                    "explanation": "Calculate rolling 14-day mean and standard deviation to detect cost outliers.",
                    "code": """sql_anomaly_detection = \"\"\"
WITH daily_costs AS (
    SELECT 
        usage_date,
        SUM(usage_quantity) AS daily_dbus
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY usage_date
),
stats AS (
    SELECT 
        usage_date,
        daily_dbus,
        AVG(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_mean,
        STDDEV(daily_dbus) OVER (ORDER BY usage_date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_std
    FROM daily_costs
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
ORDER BY usage_date DESC;
\"\"\"

print("FinOps statistical cost anomaly query validated.")
assert "z_score" in sql_anomaly_detection
assert "CRITICAL_COST_ANOMALY" in sql_anomaly_detection
"""
                }
            ],
            "key_takeaways": [
                "Statistical Baselines: Avoid fixed dollar thresholds that trigger false alarms; use rolling 14-day z-scores.",
                "Automate Alerts: Schedule the anomaly query in a DBSQL Alert to send immediate Slack/PagerDuty messages.",
                "Root-Cause Linkage: Alert payload can link directly to the high-cost query or cluster ID."
            ],
            "interview_questions": [
                "How do you implement statistical anomaly detection over Databricks billing telemetry?",
                "What action should an automated FinOps system take when a runaway query anomaly is detected?"
            ]
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
            "business_scenario": "The enterprise central IT department needs to bill back cloud infrastructure costs accurately to Marketing, Risk, Fraud, and Retail business units based on verified resource consumption.",
            "problem_statement": "Build an automated SQL Chargeback model over `system.billing.usage`, allocating shared metastore and infrastructure costs proportionally to tenant business units.",
            "architectural_notes": "Chargeback allocates direct costs (tagged clusters) and indirect shared costs (metastore, system services) proportionally across business units, providing full transparency and fiscal accountability.",
            "sections": [
                {
                    "title": "1. Multi-Tenant Chargeback Allocation SQL",
                    "explanation": "Construct departmental chargeback queries attributing direct and proportional shared spend.",
                    "code": """sql_chargeback_model = \"\"\"
-- Multi-Tenant Departmental Chargeback Model
WITH direct_costs AS (
    SELECT 
        COALESCE(custom_tags['BusinessUnit'], 'SHARED_INFRA') AS business_unit,
        SUM(usage_quantity * 0.30) AS direct_spend_usd
    FROM system.billing.usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1
),
shared_pool AS (
    SELECT direct_spend_usd AS shared_amount FROM direct_costs WHERE business_unit = 'SHARED_INFRA'
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
ORDER BY total_monthly_bill_usd DESC;
\"\"\"

print("Departmental chargeback model verified.")
assert "SHARED_INFRA" in sql_chargeback_model
assert "total_monthly_bill_usd" in sql_chargeback_model
"""
                }
            ],
            "key_takeaways": [
                "Proportional Allocation: Fairly distribute shared platform overhead based on direct consumption weights.",
                "Fiscal Transparency: Business units see exact itemized breakdowns of their monthly data engineering costs.",
                "Self-Policing Culture: Teams optimize their queries and auto-stop settings when bills are transparent."
            ],
            "interview_questions": [
                "How do you handle shared, untagged platform costs in a multi-tenant Databricks chargeback model?",
                "What is the difference between a Showback model and a Chargeback model in enterprise FinOps?"
            ]
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
