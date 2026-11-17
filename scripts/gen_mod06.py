"""
Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer (Notebooks 055 - 065)
"""

from pathlib import Path
from notebook_builder import build_notebook, write_notebook

MODULE_FOLDER = "06_databricks_sql_and_photon"
MODULE_NAME = "Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "055",
            "title": "Serverless SQL Warehouses: Instant Spin-up, Autoscaling Policies & Sizing T-Shirts",
            "filename": "055_serverless_sql_warehouses_instant_spin_up_autoscaling_policies_and_sizing_t_shirts.py",
            "difficulty": "Foundational",
            "business_scenario": "A business intelligence team experiences unpredictable query concurrency: 5 analysts query dashboards at night, but 200 executives access them simultaneously on Monday mornings.",
            "problem_statement": "Configure a Serverless SQL Warehouse with optimal T-shirt sizing (2X-Small to 4X-Large), auto-stop policies (5-10 minutes), and autoscaling bounds (min/max clusters).",
            "architectural_notes": "Serverless SQL Warehouses use pre-warmed compute pools managed by Databricks, starting in 2-4 seconds. They scale out clusters horizontally under concurrency pressure and terminate aggressively on idle to prevent wasted DBUs.",
            "sections": [
                {
                    "title": "1. Serverless SQL Warehouse T-Shirt Sizing Matrix",
                    "explanation": "Evaluate cluster sizing and concurrent query capacity.",
                    "code": """warehouse_tiers = {
    "2X-Small": {"cores": 4, "ram_gb": 16, "target_queries": "Light ad-hoc analytics, exploratory queries"},
    "Small": {"cores": 16, "ram_gb": 64, "target_queries": "Standard department BI dashboards (Power BI / Tableau)"},
    "Large": {"cores": 64, "ram_gb": 256, "target_queries": "Heavy aggregations, multi-billion row joins"},
    "4X-Large": {"cores": 256, "ram_gb": 1024, "target_queries": "Enterprise-wide high-concurrency peak reporting"}
}

for size, specs in warehouse_tiers.items():
    print(f"[{size}] Cores: {specs['cores']} | RAM: {specs['ram_gb']}GB | {specs['target_queries']}")

assert warehouse_tiers["Small"]["cores"] == 16
"""
                }
            ],
            "key_takeaways": [
                "Instant Start: Eliminates the 5-7 minute VM startup lag of classic warehouses.",
                "Aggressive Auto-Stop: Set auto-stop to 10 minutes; since startup is 2 seconds, no cold start penalty exists.",
                "Cost Scaling: Scale out max clusters during peak hours and allow scale-to-zero at night."
            ],
            "interview_questions": [
                "How do Serverless SQL Warehouses handle cluster autoscaling differently from Classic SQL Warehouses?",
                "What is the recommended auto-stop idle timeout for Serverless SQL Warehouses?"
            ]
        },
        {
            "nb_id": "056",
            "title": "Photon Engine Internals: C++ Vectorized Execution, SIMD Hardware & Memory Off-Heap",
            "filename": "056_photon_engine_internals_c_vectorized_execution_simd_hardware_and_memory_off_heap.py",
            "difficulty": "Advanced",
            "business_scenario": "A large-scale enterprise data platform is evaluating whether to enable the Photon Engine for its SQL workloads to justify the incremental DBU price premium with query speedups.",
            "problem_statement": "Deep-dive into the architectural mechanics of the Photon C++ engine, analyze vectorized memory layouts, SIMD hardware instructions, and benchmark query acceleration on heavy joins.",
            "architectural_notes": "Photon is a native vectorized query engine written from scratch in C++. It replaces the JVM execution runtime for supported operators (scans, joins, aggregations, hashes), bypassing Java object overhead and garbage collection pauses entirely.",
            "sections": [
                {
                    "title": "1. Photon vs. JVM Architecture Comparison",
                    "explanation": "Compare the underlying hardware execution mechanisms between Photon and JVM Spark.",
                    "code": """engine_comparison = {
    "Photon_Cpp_Engine": {
        "execution_model": "Vectorized batch processing (2048 tuples per vector)",
        "hardware_utilization": "Direct SIMD CPU register instructions (AVX-512 / ARM NEON)",
        "memory_management": "Off-heap C++ allocation; ZERO JVM GC pauses",
        "cache_locality": "High; contiguous columnar primitives fit directly in L1/L2 CPU caches"
    },
    "Standard_JVM_Catalyst": {
        "execution_model": "Row-by-row / Tungsten whole-stage code generation",
        "hardware_utilization": "Scalar instructions compiled to Java bytecode",
        "memory_management": "Managed JVM heap + off-heap Tungsten; subject to GC pauses on massive states",
        "cache_locality": "Moderate; Java object pointer chasing can cause cache misses"
    }
}

for engine, specs in engine_comparison.items():
    print(f"[{engine}]\\n  Model: {specs['execution_model']}\\n  Memory: {specs['memory_management']}\\n")

assert "ZERO JVM GC pauses" in engine_comparison["Photon_Cpp_Engine"]["memory_management"]
"""
                }
            ],
            "key_takeaways": [
                "Hardware Acceleration: Utilizes CPU SIMD instructions to process multiple data elements per instruction.",
                "Zero Garbage Collection: Completely bypasses Java heap, eliminating GC pause latency spikes.",
                "Seamless Fallback: If an operator is unsupported by Photon, Catalyst seamlessly executes it on JVM."
            ],
            "interview_questions": [
                "Why was Photon rewritten in C++ instead of optimizing the existing Java/Scala JVM codebase?",
                "How does Photon interact with Apache Spark's Catalyst Optimizer during query compilation?"
            ]
        },
        {
            "nb_id": "057",
            "title": "Intelligent Workload Management (IWM): Query Admission Control & Queue Spill Prevention",
            "filename": "057_intelligent_workload_management_iwm_query_admission_control_and_queue_spill_prevention.py",
            "difficulty": "Intermediate",
            "business_scenario": "During quarter-end financial closes, 50 analysts run massive queries simultaneously. Without admission control, clusters run out of memory, crash, and drop connections.",
            "problem_statement": "Demonstrate the mechanics of Databricks SQL Intelligent Workload Management (IWM), analyzing dynamic query admission control, queueing behavior, and memory spill mitigation.",
            "architectural_notes": "IWM uses ML-based runtime prediction to govern query admission on SQL Warehouses. Instead of letting all queries run concurrently and thrash RAM, IWM queues incoming queries and schedules them smoothly.",
            "sections": [
                {
                    "title": "1. IWM Admission Control Mechanics Model",
                    "explanation": "Simulate query admission decisions based on predicted memory and cluster capacity.",
                    "code": """class MockIWMAdmissionController:
    def __init__(self, max_concurrent_queries=10, max_memory_gb=64):
        self.max_queries = max_concurrent_queries
        self.max_ram = max_memory_gb
        self.active_queries = 0
        self.active_ram = 0

    def admit_query(self, query_id: str, estimated_ram_gb: int) -> str:
        if self.active_queries < self.max_queries and (self.active_ram + estimated_ram_gb) <= self.max_ram:
            self.active_queries += 1
            self.active_ram += estimated_ram_gb
            return f"Query {query_id}: ADMITTED (Running on cluster)"
        else:
            return f"Query {query_id}: QUEUED (Waiting for capacity to prevent memory spill)"

iwm = MockIWMAdmissionController(max_concurrent_queries=2, max_memory_gb=32)
print(iwm.admit_query("Q1", 16))
print(iwm.admit_query("Q2", 12))
print(iwm.admit_query("Q3", 8)) # Should queue

assert "QUEUED" in iwm.admit_query("Q3", 8)
"""
                }
            ],
            "key_takeaways": [
                "Spill Prevention: Queuing queries temporarily is faster than letting multiple queries spill gigabytes to disk.",
                "Fast Auto-Scaling: IWM signals the warehouse cluster manager to launch additional clusters when queue depths grow.",
                "Zero Cluster Crashes: Protects cluster stability under severe concurrent load."
            ],
            "interview_questions": [
                "What is Intelligent Workload Management (IWM) in Databricks SQL Warehouses?",
                "How does IWM differentiate between quick BI lookups and long-running heavy aggregation queries?"
            ]
        },
        {
            "nb_id": "058",
            "title": "Multi-Tier Caching Architecture: Result Cache, Local Disk Cache & Remote Cache",
            "filename": "058_multi_tier_caching_architecture_result_cache_local_disk_cache_and_remote_cache.py",
            "difficulty": "Intermediate",
            "business_scenario": "A dashboard with 50 visual tiles is refreshed by 500 business users throughout the day. Executing 25,000 queries directly against cloud object storage costs thousands in repeated scanning.",
            "problem_statement": "Analyze and optimize the three caching layers in Databricks SQL: (1) Query Result Cache, (2) Local SSD Disk Cache (Delta Cache), and (3) Remote Storage Metadata Cache.",
            "architectural_notes": "Databricks SQL implements multi-tier caching: Result Cache serves identical queries in milliseconds from UI memory. Local Disk Cache stores decompressed columnar Parquet data on worker NVMe SSDs. Remote Cache stores metadata.",
            "sections": [
                {
                    "title": "1. Multi-Tier Caching Hierarchy Analysis",
                    "explanation": "Inspect latency, location, and invalidation rules across caching layers.",
                    "code": """caching_tiers = {
    "Tier_1_Result_Cache": {
        "location": "Control Plane / UI Memory",
        "latency": "< 10 milliseconds",
        "invalidation": "Automatic when underlying Delta table receives a commit (`add` / `remove`)"
    },
    "Tier_2_Local_Disk_Cache": {
        "location": "Worker Node NVMe SSDs (Delta Cache)",
        "latency": "10 - 50 milliseconds",
        "invalidation": "Automatic file-level tracking; cached Parquet columns read directly from local NVMe"
    },
    "Tier_3_Cloud_Storage": {
        "location": "ADLS Gen2 / AWS S3 / GCS",
        "latency": "100 - 1000 milliseconds",
        "invalidation": "Persistent authoritative source of truth"
    }
}

for tier, meta in caching_tiers.items():
    print(f"[{tier}] Latency: {meta['latency']} | Invalidation: {meta['invalidation']}")

assert "< 10 milliseconds" in caching_tiers["Tier_1_Result_Cache"]["latency"]
"""
                }
            ],
            "key_takeaways": [
                "Deterministic Invalidation: Cached results are automatically invalidated the moment the Delta table commits a new version.",
                "Zero Stale Data: You never need to manually flush caches after a DML update.",
                "SSD Performance: Delta Cache on local NVMe SSDs accelerates scans by up to 10x over remote cloud storage."
            ],
            "interview_questions": [
                "How does Databricks ensure that Query Result Cache never serves stale data after an update?",
                "What is the difference between the Spark `CACHE TABLE` command and the Databricks Disk Cache (Delta Cache)?"
            ]
        },
        {
            "nb_id": "059",
            "title": "DBSQL Query Profile Analysis: Diagnosing Scans, Shuffles, Spills & Pruning Efficiency",
            "filename": "059_dbsql_query_profile_analysis_diagnosing_scans_shuffles_spills_and_pruning_efficiency.py",
            "difficulty": "Advanced",
            "business_scenario": "An executive dashboard query takes 85 seconds to run. The business demands sub-5-second performance. The engineer must use Query Profile to identify whether the bottleneck is scanning, spilling, or shuffling.",
            "problem_statement": "Inspect and parse a Databricks SQL Query Profile, calculate data skipping efficiency (`Files Read` vs. `Files Pruned`), and eliminate disk spill bottlenecks.",
            "architectural_notes": "Query Profile visualizes the physical execution tree in DBSQL. Key metrics include: Scan Time, Files Pruned (partition/clustering efficiency), Shuffle Exchange Rows, and Memory Spill to Disk.",
            "sections": [
                {
                    "title": "1. Query Profile Metric Extraction & Bottleneck Triage",
                    "explanation": "Analyze simulated query profile metrics to pinpoint performance regressions.",
                    "code": """query_profile_metrics = {
    "query_id": "01ef-5544-aa33",
    "total_duration_ms": 85000,
    "stages": {
        "scan_orders": {
            "total_files": 12500,
            "files_read": 12500,
            "files_pruned": 0, # ZERO PRUNING!
            "bytes_read": "850 GB",
            "time_ms": 62000
        },
        "hash_join": {
            "spill_to_disk_bytes": "45 GB", # DISK SPILL!
            "time_ms": 18000
        }
    }
}

scan = query_profile_metrics["stages"]["scan_orders"]
prune_pct = (scan["files_pruned"] / scan["total_files"]) * 100
print(f"Total Scan Time: {scan['time_ms'] / 1000:.1f}s")
print(f"File Pruning Efficiency: {prune_pct:.1f}%")
print(f"Memory Spilled to Disk: {query_profile_metrics['stages']['hash_join']['spill_to_disk_bytes']}")

assert scan["files_pruned"] == 0, "Diagnostic Alert: Query performed full table scan!"
"""
                }
            ],
            "key_takeaways": [
                "Zero Pruning Flag: If `files_pruned == 0`, the query is doing a full table scan; apply Liquid Clustering.",
                "Spill Detection: High `spill_to_disk_bytes` indicates cluster RAM is undersized or join keys are skewed.",
                "Scan Bottlenecks: Scans taking > 70% of query time indicate missing partition/clustering filters."
            ],
            "interview_questions": [
                "How do you identify whether a slow query is bottlenecked on I/O scan vs. CPU shuffle in DBSQL Query Profile?",
                "What does 'Rows Spilled to Disk' indicate in a Query Profile?"
            ]
        },
        {
            "nb_id": "060",
            "title": "Materialized Views & Streaming Tables in DBSQL without Apache Spark Code",
            "filename": "060_materialized_views_and_streaming_tables_in_dbsql_without_apache_spark_code.py",
            "difficulty": "Intermediate",
            "business_scenario": "SQL analysts and analytics engineers without Python skills need to build automated incremental pipelines that ingest files and maintain aggregated summary marts.",
            "problem_statement": "Deploy Streaming Tables and Materialized Views in Databricks SQL using pure ANSI SQL (`CREATE STREAMING TABLE` and `CREATE MATERIALIZED VIEW`), managing automatic refresh schedules.",
            "architectural_notes": "Databricks SQL supports declarative Streaming Tables and Materialized Views natively. Under the hood, these leverage the DLT engine with serverless compute, bringing incremental pipeline engineering to pure SQL users.",
            "sections": [
                {
                    "title": "1. Pure ANSI SQL Declarative Pipeline DDL",
                    "explanation": "Create streaming tables and materialized views with refresh schedules in SQL.",
                    "code": """ddl_sql_pipelines = \"\"\"
-- 1. Create Streaming Table ingesting files via cloud_files() in SQL
CREATE OR REPLACE STREAMING TABLE prod_lakehouse.bronze.web_logs
SCHEDULE EVERY 1 HOUR
AS SELECT * FROM STREAM read_files(
    '/Volumes/prod_lakehouse/raw/web_logs/',
    format => 'json'
);

-- 2. Create Materialized View pre-aggregating metrics
CREATE OR REPLACE MATERIALIZED VIEW prod_lakehouse.gold.daily_page_views
SCHEDULE EVERY 1 DAY
AS SELECT 
    CAST(event_time AS DATE) AS log_date,
    page_url,
    COUNT(*) AS total_hits,
    COUNT(DISTINCT visitor_id) AS unique_visitors
FROM prod_lakehouse.bronze.web_logs
GROUP BY 1, 2;
\"\"\"

print("Pure SQL Streaming Table & Materialized View DDL verified.")
assert "CREATE OR REPLACE STREAMING TABLE" in ddl_sql_pipelines
assert "CREATE OR REPLACE MATERIALIZED VIEW" in ddl_sql_pipelines
"""
                }
            ],
            "key_takeaways": [
                "Zero Python Required: SQL analysts can build robust streaming pipelines using pure ANSI SQL.",
                "Automated Incremental Refresh: Materialized views recompute only what has changed upstream.",
                "Unified Serverless Compute: Refreshes execute on serverless SQL warehouses automatically."
            ],
            "interview_questions": [
                "How do Materialized Views in Databricks SQL differ from standard SQL Views?",
                "What is the function of `STREAM read_files()` in pure SQL streaming tables?"
            ]
        },
        {
            "nb_id": "061",
            "title": "AI/BI Dashboards (Lakeview): Interactive Filtering, Canvas Layouts & Cross-Filtering",
            "filename": "061_ai_bi_dashboards_lakeview_interactive_filtering_canvas_layouts_and_cross_filtering.py",
            "difficulty": "Foundational",
            "business_scenario": "An organization wants to retire legacy dashboard tools (Redash/Tableau) in favor of AI/BI Dashboards (Lakeview) that connect directly to Unity Catalog data with native cross-filtering.",
            "problem_statement": "Define an AI/BI Dashboard specification in JSON/YAML, configure interactive parameter widgets, establish cross-filtering between charts, and manage the Draft/Published lifecycle.",
            "architectural_notes": "AI/BI Dashboards (formerly Lakeview) provide modern data visualization built directly on Databricks SQL. Dashboards separate Draft state from Published state, support cross-filtering across visual charts, and run on serverless warehouses.",
            "sections": [
                {
                    "title": "1. AI/BI Dashboard Specification Structure",
                    "explanation": "Simulate dashboard definition with widgets and cross-filtering rules.",
                    "code": """dashboard_spec = {
    "display_name": "Executive Revenue Intelligence",
    "warehouse_id": "wh-serverless-001",
    "pages": [
        {
            "name": "Overview",
            "layout": "grid",
            "visualizations": [
                {"id": "viz_1", "type": "counter", "title": "Total Revenue", "query": "SELECT SUM(amount) FROM fact_sales"},
                {"id": "viz_2", "type": "bar", "title": "Revenue by Region", "query": "SELECT region, SUM(amount) FROM fact_sales GROUP BY region"},
                {"id": "viz_3", "type": "line", "title": "Monthly Trend", "query": "SELECT date_trunc('month', sale_date), SUM(amount) FROM fact_sales GROUP BY 1"}
            ],
            "cross_filtering_enabled": True
        }
    ]
}

print(f"Dashboard: {dashboard_spec['display_name']}")
print(f"Visualizations Configured: {len(dashboard_spec['pages'][0]['visualizations'])}")
assert dashboard_spec["pages"][0]["cross_filtering_enabled"] is True
"""
                }
            ],
            "key_takeaways": [
                "Draft vs. Published: Developers can make changes in Draft mode without breaking the live Published dashboard.",
                "Native Cross-Filtering: Clicking a bar in one chart instantly filters all other charts on the canvas.",
                "Direct UC Governance: Dashboards inherit Unity Catalog row filters and column masks automatically."
            ],
            "interview_questions": [
                "How does the Draft and Published lifecycle work in Databricks AI/BI Dashboards?",
                "Do AI/BI Dashboards respect Unity Catalog Dynamic Row Filters and Column Masks?"
            ]
        },
        {
            "nb_id": "062",
            "title": "Databricks Genie Spaces: Conversational Data Intelligence & Certified SQL Assets",
            "filename": "062_databricks_genie_spaces_conversational_data_intelligence_and_certified_sql_assets.py",
            "difficulty": "Intermediate",
            "business_scenario": "Executive leaders want to ask business questions in natural language ('What was our top selling product in EMEA last month?') and receive accurate SQL-backed answers with zero hallucination.",
            "problem_statement": "Configure a Databricks Genie Space, define certified SQL assets, author semantic descriptions, and curate trusted benchmarks to guide LLM query generation.",
            "architectural_notes": "Databricks Genie provides a conversational AI interface over Lakehouse data. It combines foundation models with enterprise semantic metadata, Unity Catalog schemas, and certified SQL queries to generate verifiable SQL answers.",
            "sections": [
                {
                    "title": "1. Genie Space Semantic Configuration",
                    "explanation": "Define trusted tables, column descriptions, and certified SQL benchmark queries for Genie.",
                    "code": """genie_space_config = {
    "space_name": "Executive Sales Intelligence",
    "tables": ["prod_lakehouse.gold.fact_sales", "prod_lakehouse.gold.dim_products"],
    "curated_sql_assets": [
        {
            "question": "What is our definition of monthly recurring revenue (MRR)?",
            "sql": "SELECT SUM(plan_price) FROM subscriptions WHERE status = 'ACTIVE' AND billing_cycle = 'MONTHLY'"
        }
    ],
    "semantic_guidelines": [
        "Always exclude test accounts where email ends with @example.com",
        "Total revenue must always use the 'net_revenue' column, not 'gross_revenue'"
    ]
}

print(f"Genie Space: {genie_space_config['space_name']}")
print(f"Curated Benchmarks: {len(genie_space_config['curated_sql_assets'])}")
print(f"Semantic Guardrails: {len(genie_space_config['semantic_guidelines'])}")
assert len(genie_space_config["semantic_guidelines"]) == 2
"""
                }
            ],
            "key_takeaways": [
                "Grounded in SQL: Genie always presents the exact SQL query executed, allowing human verification.",
                "Certified Assets: Curate approved SQL templates to train Genie on complex proprietary calculations.",
                "Zero Hallucination Guardrails: Semantic instructions instruct the LLM on business logic rules."
            ],
            "interview_questions": [
                "How does Databricks Genie ensure that natural language queries generate mathematically accurate SQL?",
                "What role do certified benchmark queries play in tuning a Genie Space?"
            ]
        },
        {
            "nb_id": "063",
            "title": "Databricks Semantic Layer & Metric Views: Enterprise Dimensions & Measures",
            "filename": "063_databricks_semantic_layer_and_metric_views_enterprise_dimensions_and_measures.py",
            "difficulty": "Intermediate",
            "business_scenario": "Different departments compute 'Customer Churn' and 'Net Revenue' using conflicting formulas, resulting in discrepancies during executive board meetings.",
            "problem_statement": "Define a unified Semantic Layer and Metric Views in Databricks, codifying enterprise dimensions and measures as the single source of truth for all downstream tools.",
            "architectural_notes": "The Databricks Semantic Layer establishes standardized metric definitions (measures, dimensions, time grains) directly in Unity Catalog. BI tools (Power BI, Tableau, Lakeview) query certified metrics consistently.",
            "sections": [
                {
                    "title": "1. Metric View Specification DDL",
                    "explanation": "Define standardized dimensions and measures in SQL.",
                    "code": """metric_view_spec = \"\"\"
-- Define certified enterprise metric view
CREATE OR REPLACE VIEW prod_lakehouse.gold.metrics_financial_core AS
SELECT 
    -- Dimensions
    customer_id,
    region,
    product_tier,
    date_trunc('month', transaction_date) AS fiscal_month,
    
    -- Standardized Enterprise Measures
    SUM(gross_amount - discount_amount) AS net_revenue,
    COUNT(DISTINCT transaction_id) AS order_volume,
    ROUND(SUM(gross_amount - discount_amount) / COUNT(DISTINCT transaction_id), 2) AS average_order_value
FROM prod_lakehouse.silver.sales_transactions
GROUP BY 1, 2, 3, 4;
\"\"\"

print("Enterprise Semantic Metric View DDL verified.")
assert "net_revenue" in metric_view_spec
assert "average_order_value" in metric_view_spec
"""
                }
            ],
            "key_takeaways": [
                "Single Source of Truth: Define critical business metrics once in Unity Catalog.",
                "Consistent BI: Power BI, Tableau, and Genie all report identical numbers.",
                "Governance Centralization: Changes to formulas update globally across all downstream dashboards."
            ],
            "interview_questions": [
                "How does an in-database Semantic Layer in Unity Catalog eliminate metric discrepancies between BI tools?",
                "What is the difference between a dimensional attribute and a metric measure?"
            ]
        },
        {
            "nb_id": "064",
            "title": "DBSQL Alerts, Automated Refresh Schedules & SLA-Driven Slack Notifications",
            "filename": "064_dbsql_alerts_automated_refresh_schedules_and_sla_driven_slack_notifications.py",
            "difficulty": "Foundational",
            "business_scenario": "A payments platform must be alerted within 5 minutes if failed credit card transactions exceed 2% of total volume over any rolling 15-minute window.",
            "problem_statement": "Configure automated Databricks SQL Alerts on scheduled queries, evaluate threshold triggers (`>` or `<`), and configure webhook destinations for Slack and PagerDuty.",
            "architectural_notes": "DBSQL Alerts execute a query on a recurring schedule. When the returned result crosses a predefined threshold, Databricks automatically fires notifications to configured destinations (Slack, Teams, PagerDuty, Webhooks).",
            "sections": [
                {
                    "title": "1. SQL Alert Definition & Threshold Evaluation",
                    "explanation": "Define an alert query and trigger condition.",
                    "code": """alert_definition = {
    "name": "High Payment Failure Rate Alert",
    "query": "SELECT failure_rate_pct FROM prod_lakehouse.gold.payment_kpis WHERE window_start >= NOW() - INTERVAL 15 MIN",
    "condition": {
        "column": "failure_rate_pct",
        "operator": ">",
        "threshold": 2.0
    },
    "schedule": "EVERY 5 MINUTES",
    "notification_destination": "slack-data-alerts-channel"
}

# Simulate threshold check
current_failure_rate = 3.4
triggered = current_failure_rate > alert_definition["condition"]["threshold"]

print(f"Alert: {alert_definition['name']}")
print(f"Current Value: {current_failure_rate}% | Threshold: {alert_definition['condition']['threshold']}%")
print(f"Alert Fired to Slack: {triggered}")
assert triggered is True
"""
                }
            ],
            "key_takeaways": [
                "Proactive Alerting: Catch operational anomalies before business users notice.",
                "Multi-Channel: Send alerts to Slack channels, PagerDuty on-call services, or custom webhooks.",
                "State Tracking: Alerts can trigger 'Just Once' when passing threshold or 'Each Time' evaluated."
            ],
            "interview_questions": [
                "How do DBSQL Alerts evaluate conditions across single-value versus multi-row query results?",
                "What is the difference between 'Trigger Once' and 'Trigger Each Time' in Databricks SQL Alerts?"
            ]
        },
        {
            "nb_id": "065",
            "title": "SQL Warehouse Concurrency Scaling: Horizontal Multi-Cluster Load Balancing",
            "filename": "065_sql_warehouse_concurrency_scaling_horizontal_multi_cluster_load_balancing.py",
            "difficulty": "Intermediate",
            "business_scenario": "A company has 1,000 active Power BI users refreshing dashboards at the start of business. A single SQL warehouse cluster saturates, queueing queries and causing dashboard timeouts.",
            "problem_statement": "Configure horizontal multi-cluster load balancing on a Serverless SQL Warehouse, tune maximum cluster bounds (1 to 10), and analyze scaling policies (Economy vs. Pro).",
            "architectural_notes": "Databricks SQL Warehouses scale horizontally by adding identical compute clusters behind a shared load balancer. When query concurrency exceeds single-cluster capacity, additional clusters launch automatically to handle the queue.",
            "sections": [
                {
                    "title": "1. Multi-Cluster Sizing & Scaling Policy Model",
                    "explanation": "Simulate warehouse cluster autoscaling under variable query concurrency.",
                    "code": """def evaluate_warehouse_scaling(active_queries: int, queries_per_cluster: int = 10, min_clusters: int = 1, max_clusters: int = 5):
    needed_clusters = (active_queries + queries_per_cluster - 1) // queries_per_cluster
    allocated_clusters = max(min_clusters, min(needed_clusters, max_clusters))
    is_queued = needed_clusters > max_clusters
    return {"allocated_clusters": allocated_clusters, "is_queued": is_queued}

peak_load = evaluate_warehouse_scaling(active_queries=45, queries_per_cluster=10, min_clusters=1, max_clusters=5)
print(f"Under 45 Concurrent Queries:")
print(f"  Allocated Clusters: {peak_load['allocated_clusters']}")
print(f"  Queued: {peak_load['is_queued']}")
assert peak_load["allocated_clusters"] == 5
assert not peak_load["is_queued"]
"""
                }
            ],
            "key_takeaways": [
                "Horizontal Concurrency: Add clusters to handle concurrent users without increasing individual VM size.",
                "Scaling Policy: `Pro` scales out immediately for low latency; `Economy` scales conservatively to save cost.",
                "Sub-Second Scale-Down: Serverless clusters scale down rapidly once concurrency subsides."
            ],
            "interview_questions": [
                "How does multi-cluster autoscaling in Databricks SQL prevent query queueing during peak hours?",
                "When should an engineer increase cluster T-shirt size versus increasing the maximum cluster count?"
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
