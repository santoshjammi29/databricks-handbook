"""
Module 05: Lakeflow Jobs, Workflows & Orchestration (Notebooks 044 - 054)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "05_lakeflow_jobs_and_orchestration"
MODULE_NAME = "Module 05: Lakeflow Jobs, Workflows & Orchestration"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "044",
            "title": "Multi-Task Lakeflow Jobs: DAG Task Dependencies, Parameters & Conditional Paths",
            "filename": "044_multi_task_lakeflow_jobs_dag_task_dependencies_parameters_and_conditional_paths.py",
            "difficulty": "Intermediate",
            "business_scenario": "A financial data pipeline consists of 8 sequential and parallel steps: ingest market feeds, validate records, branch based on market holiday status, and run downstream settlement.",
            "problem_statement": "Define a multi-task Lakeflow DAG job structure with explicit dependencies (`depends_on`), conditional execution (`If/Else` tasks), and parameter inheritance.",
            "architectural_notes": "Lakeflow Jobs orchestrate complex directed acyclic graphs (DAGs) of tasks within Databricks. Tasks can execute in parallel, wait for upstream parents, or branch conditionally based on dynamic task values.",
            "sections": [
                {
                    "title": "1. Multi-Task DAG Task Structure Model",
                    "explanation": "Simulate and validate DAG topological dependencies and conditional task branches.",
                    "code": """job_dag = {
    "job_name": "daily_market_settlement",
    "tasks": [
        {"task_key": "ingest_trades", "depends_on": []},
        {"task_key": "validate_data", "depends_on": ["ingest_trades"]},
        {"task_key": "check_market_holiday", "depends_on": ["validate_data"], "task_type": "condition"},
        {"task_key": "run_settlement", "depends_on": ["check_market_holiday"], "run_if": "ALL_SUCCESS"},
        {"task_key": "skip_settlement_notification", "depends_on": ["check_market_holiday"], "run_if": "AT_LEAST_ONE_FAILED"}
    ]
}

# Topological validation: ensure all dependency tasks exist
task_keys = {t["task_key"] for t in job_dag["tasks"]}
for t in job_dag["tasks"]:
    for parent in t["depends_on"]:
        assert parent in task_keys, f"Invalid DAG: Missing dependency {parent}"

print("DAG topology validated: All task dependencies resolved.")
"""
                }
            ],
            "key_takeaways": [
                "DAG Native: Lakeflow Jobs replace external schedulers like Airflow for Databricks-native pipelines.",
                "Conditional Routing: Use `If/Else` condition tasks to dynamically route workflow execution.",
                "Zero Cluster Lock: Each task can run on its own ephemeral cluster or serverless compute."
            ],
            "interview_questions": [
                "How do conditional `If/Else` tasks work in Databricks Workflows?",
                "What is the difference between `run_if = ALL_SUCCESS` and `run_if = AT_LEAST_ONE_SUCCESS`?"
            ]
        },
        {
            "nb_id": "045",
            "title": "Multi-Modal Task Types: Notebook, Python Wheel, DLT Pipeline, dbt & SQL Warehouse",
            "filename": "045_task_types_mastery_notebook_python_wheel_dlt_pipeline_dbt_and_sql_warehouse.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise platform combines multiple technology stacks: data ingestion runs in DLT, business transformations run in dbt Core, and BI aggregations run as SQL queries in a SQL Warehouse.",
            "problem_statement": "Configure a unified multi-task job orchestrating Notebook tasks, Python Wheel tasks, DLT Pipeline tasks, dbt tasks, and Databricks SQL tasks within a single pane of glass.",
            "architectural_notes": "Lakeflow Jobs is multi-modal. Rather than restricting tasks to notebooks, it supports compiled Python Wheels, SQL Warehouse queries, dbt models, and DLT pipelines in one DAG.",
            "sections": [
                {
                    "title": "1. Multi-Modal Task Specification",
                    "explanation": "Define resource blocks for various task types supported in Databricks Workflows.",
                    "code": """task_types_spec = {
    "task_1_bronze": {"type": "pipeline_task", "pipeline_id": "dlt-pipeline-uuid-001"},
    "task_2_silver": {"type": "python_wheel_task", "package_name": "etl_core", "entry_point": "run_silver"},
    "task_3_dbt": {"type": "dbt_task", "commands": ["dbt run --select gold_marts"]},
    "task_4_gold_alert": {"type": "sql_task", "warehouse_id": "wh-serverless-001", "query_id": "qry-audit-summary"}
}

for task_name, spec in task_types_spec.items():
    print(f"Task: {task_name} | Type: {spec['type']}")
assert len(task_types_spec) == 4
"""
                }
            ],
            "key_takeaways": [
                "Beyond Notebooks: Production teams increasingly package code into Python Wheels for clean versioning.",
                "Native dbt Integration: Databricks executes dbt models with native Photon acceleration.",
                "Unified Monitoring: Review run histories across DLT, SQL, and Python in one view."
            ],
            "interview_questions": [
                "Why should complex production code be deployed as Python Wheels rather than raw notebooks in Lakeflow Jobs?",
                "How does Databricks orchestrate dbt tasks natively in Workflows?"
            ]
        },
        {
            "nb_id": "046",
            "title": "Inter-Task Communication & Context Sharing via dbutils.jobs.taskValues",
            "filename": "046_inter_task_communication_and_context_sharing_via_dbutils_jobs_taskvalues.py",
            "difficulty": "Intermediate",
            "business_scenario": "In a nightly batch ETL workflow, an upstream ingestion task computes the dynamic date partition and processed row count. Downstream tasks require these dynamic values to run incremental updates.",
            "problem_statement": "Demonstrate the use of `dbutils.jobs.taskValues.set()` in an upstream task and `dbutils.jobs.taskValues.get()` in a downstream task to share execution state.",
            "architectural_notes": "`taskValues` allows tasks within the same job run to pass scalar values, JSON dictionaries, and execution flags across task boundaries without writing temporary metadata files to cloud storage.",
            "sections": [
                {
                    "title": "1. Set and Retrieve Task Values",
                    "explanation": "Simulate inter-task state passing using the taskValues API pattern.",
                    "code": """# Simulate dbutils.jobs.taskValues in Python
class MockTaskValues:
    def __init__(self):
        self._store = {}
    def set(self, key: str, value):
        self._store[key] = value
    def get(self, task_key: str, key: str, default=None):
        return self._store.get(key, default)

mock_tv = MockTaskValues()

# Upstream Task 1 (Ingestion) sets values
mock_tv.set("batch_id", "20261117_01")
mock_tv.set("records_processed", 450000)
mock_tv.set("status", "SUCCESS")

# Downstream Task 2 retrieves values
retrieved_batch = mock_tv.get("ingest_task", "batch_id")
retrieved_count = mock_tv.get("ingest_task", "records_processed")

print(f"Downstream Task Received: Batch ID = {retrieved_batch}, Rows = {retrieved_count}")
assert retrieved_batch == "20261117_01"
assert retrieved_count == 450000
"""
                }
            ],
            "key_takeaways": [
                "State Propagation: Share dynamic dates, metrics, and thresholds between tasks.",
                "Zero Storage Footprint: State is held in the Control Plane metadata store for the run duration.",
                "Conditional Gating: Downstream condition tasks can evaluate task values to make branching decisions."
            ],
            "interview_questions": [
                "What is the maximum payload size supported for `dbutils.jobs.taskValues`?",
                "Can a task access task values from a previous run of the same job?"
            ]
        },
        {
            "nb_id": "047",
            "title": "Production Job Execution: Run As Service Principal & Zero-Interactive Identity",
            "filename": "047_production_job_execution_run_as_service_principal_and_zero_interactive_identity.py",
            "difficulty": "Intermediate",
            "business_scenario": "A critical production job failed because the data engineer who configured it transferred to another team and their user account was deactivated.",
            "problem_statement": "Configure production Lakeflow Jobs to execute under a dedicated Service Principal identity (`run_as`), eliminating personal user identity dependencies.",
            "architectural_notes": "The `run_as` setting decouples job ownership from human users. Production jobs should run as a Service Principal identity authenticated via OAuth M2M tokens, ensuring unbroken pipeline operations.",
            "sections": [
                {
                    "title": "1. Configure Run As Service Principal Specification",
                    "explanation": "Define DABs and Job JSON properties enforcing Service Principal ownership.",
                    "code": """job_security_spec = {
    "job_name": "prod_financial_reconciliation",
    "run_as": {
        "service_principal_name": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4"
    },
    "permissions": [
        {"service_principal_name": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4", "level": "IS_OWNER"},
        {"group_name": "data-platform-engineers", "level": "CAN_MANAGE_RUN"}
    ]
}

print(f"Job Owner Service Principal: {job_security_spec['run_as']['service_principal_name']}")
assert "service_principal_name" in job_security_spec["run_as"]
"""
                }
            ],
            "key_takeaways": [
                "Business Continuity: Service Principals never leave the company or reset personal passwords.",
                "Least Privilege: Grant Service Principals exact permissions on Unity Catalog catalogs and schemas.",
                "Audit Trail: Security teams can distinctly track automated vs. interactive queries in `system.access.audit`."
            ],
            "interview_questions": [
                "How do you assign a Service Principal as the owner of a Databricks Workflow?",
                "What privileges in Unity Catalog are required for a Service Principal to execute a multi-task job?"
            ]
        },
        {
            "nb_id": "048",
            "title": "Cluster Allocation Strategy: Ephemeral Job Clusters vs. Shared Compute Pools",
            "filename": "048_cluster_allocation_strategy_ephemeral_job_clusters_vs_shared_compute_pools.py",
            "difficulty": "Intermediate",
            "business_scenario": "A data engineering team wants to minimize cluster initialization time (4-6 minutes per task) without incurring the higher cost of running an all-day All-Purpose cluster.",
            "problem_statement": "Evaluate and configure cluster allocation strategies: (1) Ephemeral New Clusters per task, (2) Shared Job Clusters across multiple tasks, and (3) Pre-warmed Instance Pools.",
            "architectural_notes": "In a multi-task job, tasks can share a single **Job Cluster** (`job_cluster_key`), eliminating VM spinup time for downstream tasks while maintaining the lower Job DBU pricing tier. Pre-warmed Instance Pools reduce VM provisioning latency to under 45 seconds.",
            "sections": [
                {
                    "title": "1. Shared Job Cluster Configuration Analysis",
                    "explanation": "Compare cold-start provisioning delays and DBU consumption models.",
                    "code": """cluster_strategies = {
    "New_Cluster_Per_Task": {
        "spinup_time": "4-7 minutes per task",
        "isolation": "Complete VM isolation between tasks",
        "cost_efficiency": "Moderate; repeated VM initialization overhead"
    },
    "Shared_Job_Cluster": {
        "spinup_time": "4-7 minutes once for Task 1; instant for Tasks 2-N",
        "isolation": "Shared driver/worker across DAG tasks; cluster terminates when job completes",
        "cost_efficiency": "High; eliminates repeated startup lag at Job DBU rate"
    },
    "Instance_Pool": {
        "spinup_time": "30-60 seconds (pre-warmed VMs)",
        "isolation": "Clean OS boot from pooled instances",
        "cost_efficiency": "High; incurs idle VM cloud cost only for minimum idle instances"
    }
}

for name, strat in cluster_strategies.items():
    print(f"[{name}]\\n  Spinup: {strat['spinup_time']}\\n  Efficiency: {strat['cost_efficiency']}\\n")

assert "Shared driver/worker" in cluster_strategies["Shared_Job_Cluster"]["isolation"]
"""
                }
            ],
            "key_takeaways": [
                "Use `job_clusters`: Define a single `job_cluster_key` in DABs so all DAG tasks share the cluster.",
                "Ephemeral Teardown: Shared job clusters terminate automatically when the final task finishes.",
                "Instance Pools: Use pools for latency-sensitive batch pipelines requiring rapid VM acquisition."
            ],
            "interview_questions": [
                "What is the difference between sharing a Job Cluster across tasks in a workflow vs. using an All-Purpose cluster?",
                "How do Instance Pools reduce cluster startup latency?"
            ]
        },
        {
            "nb_id": "049",
            "title": "Advanced Job Triggers: Periodic Cron, File Arrival Triggers & Continuous Triggers",
            "filename": "049_advanced_job_triggers_periodic_cron_file_arrival_triggers_and_continuous_triggers.py",
            "difficulty": "Intermediate",
            "business_scenario": "Different enterprise workloads have distinct invocation triggers: sales reporting runs on a cron schedule, partner invoice processing triggers on file arrival, and streaming monitoring runs continuously.",
            "problem_statement": "Configure and test the three Databricks Workflows trigger types: (1) Periodic Quartz Cron, (2) Storage File Arrival Trigger, and (3) Continuous Execution Loop.",
            "architectural_notes": "Lakeflow Jobs support multiple trigger mechanisms. File Arrival Triggers monitor cloud storage folders and trigger jobs instantly when new files land, avoiding polling scripts. Continuous triggers keep a job constantly running, restarting immediately on failure.",
            "sections": [
                {
                    "title": "1. Job Trigger Architecture Specification",
                    "explanation": "Define YAML/JSON trigger definitions for cron, file arrival, and continuous execution.",
                    "code": """trigger_definitions = {
    "scheduled_cron": {
        "type": "cron",
        "quartz_cron_expression": "0 0 4 * * ?", # 04:00 AM UTC daily
        "timezone_id": "UTC"
    },
    "file_arrival": {
        "type": "file_arrival",
        "url": "abfss://landing@storage.dfs.core.windows.net/vendor_invoices/",
        "min_time_between_triggers_seconds": 60
    },
    "continuous_service": {
        "type": "continuous",
        "pause_status": "UNPAUSED"
    }
}

for name, trig in trigger_definitions.items():
    print(f"Trigger: {name} | Type: {trig['type']}")
assert trigger_definitions["file_arrival"]["min_time_between_triggers_seconds"] == 60
"""
                }
            ],
            "key_takeaways": [
                "File Arrival Automation: Eliminates external Lambda functions or cron polling scripts.",
                "Throttling Protection: Use `min_time_between_triggers_seconds` to batch bursts of file arrivals.",
                "Continuous Mode: Ideal for continuous real-time streaming pipelines requiring automatic restarts."
            ],
            "interview_questions": [
                "How do File Arrival Triggers detect new files in cloud storage without causing high API call costs?",
                "What happens if a new file arrives while a previous run triggered by File Arrival is still executing?"
            ]
        },
        {
            "nb_id": "050",
            "title": "Resilient Error Handling, Exponential Backoff Retries & PagerDuty/Slack Webhooks",
            "filename": "050_resilient_error_handling_exponential_backoff_retries_and_pagerduty_slack_webhooks.py",
            "difficulty": "Intermediate",
            "business_scenario": "A production pipeline experiences transient network timeouts connecting to external cloud storage. Jobs must automatically retry with exponential backoff and page on-call engineers if retries are exhausted.",
            "problem_statement": "Configure task-level retry policies (`max_retries`, `min_retry_interval_millis`), timeout budgets, and notification system webhooks in Lakeflow Jobs.",
            "architectural_notes": "Transient cloud infrastructure failures (HTTP 503, network blips) can be mitigated by configuring task retries. Lakeflow Jobs allows setting retries per task with exponential backoff, preventing immediate pipeline abortion.",
            "sections": [
                {
                    "title": "1. Task Retry Policy & Notification Configuration",
                    "explanation": "Define retry parameters and notification webhooks in job specifications.",
                    "code": """resilience_config = {
    "task_key": "fetch_external_api_data",
    "max_retries": 3,
    "min_retry_interval_millis": 30000, # 30 seconds
    "retry_on_timeout": True,
    "timeout_seconds": 3600,
    "notifications": {
        "on_failure": ["data-ops-pagerduty@company.pagerduty.com"],
        "on_retry": ["data-engineering-slack-webhook@company.com"]
    }
}

print(f"Task Retries Allowed: {resilience_config['max_retries']}")
print(f"Initial Retry Delay: {resilience_config['min_retry_interval_millis'] / 1000}s")
assert resilience_config["max_retries"] == 3
"""
                }
            ],
            "key_takeaways": [
                "Task-Level Retries: Configure `max_retries = 3` to absorb transient network blips.",
                "Timeout Budgets: Always set `timeout_seconds` to kill runaway zombie tasks automatically.",
                "PagerDuty / Slack Webhooks: Route critical alerts directly to on-call incident response channels."
            ],
            "interview_questions": [
                "What is the difference between job-level timeout and task-level timeout in Databricks Workflows?",
                "How do exponential backoff retries prevent exacerbating cloud service rate limits?"
            ]
        },
        {
            "nb_id": "051",
            "title": "Serverless Workflows: Zero-Startup-Latency Scheduling & Managed Concurrency",
            "filename": "051_serverless_workflows_zero_startup_latency_scheduling_and_managed_concurrency.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise runs 500 small batch jobs every hour. On classic compute, each job spends 5 minutes booting VMs to execute 30 seconds of code. Infrastructure waste exceeds 80%.",
            "problem_statement": "Deploy and benchmark Serverless Workflows, demonstrating instant task execution (< 5 seconds), automated horizontal scaling, and complete elimination of VM provisioning overhead.",
            "architectural_notes": "Serverless compute for Lakeflow Jobs provisions pre-warmed container micro-VMs in seconds. It scales worker capacity dynamically to match workload demand and scales to zero immediately upon job completion.",
            "sections": [
                {
                    "title": "1. Serverless vs. Classic Job Compute Latency Model",
                    "explanation": "Calculate time and cost savings achieved by migrating to Serverless Workflows.",
                    "code": """def evaluate_serverless_savings(daily_jobs: int, avg_execution_sec: int):
    # Classic: 300 seconds startup + execution
    classic_runtime_sec = (300 + avg_execution_sec) * daily_jobs
    # Serverless: 3 seconds startup + execution
    serverless_runtime_sec = (3 + avg_execution_sec) * daily_jobs
    
    saved_seconds = classic_runtime_sec - serverless_runtime_sec
    saved_hours = saved_seconds / 3600
    return {"classic_hours": classic_runtime_sec / 3600, "serverless_hours": serverless_runtime_sec / 3600, "saved_hours": saved_hours}

savings = evaluate_serverless_savings(daily_jobs=500, avg_execution_sec=60)
print(f"Classic Daily Compute Hours: {savings['classic_hours']:.1f} hrs")
print(f"Serverless Daily Compute Hours: {savings['serverless_hours']:.1f} hrs")
print(f"Daily Wasted Compute Hours Eliminated: {savings['saved_hours']:.1f} hrs")
assert savings["serverless_hours"] < savings["classic_hours"] / 4
"""
                }
            ],
            "key_takeaways": [
                "Instant Start: Tasks start in 2-4 seconds instead of 4-7 minutes.",
                "Zero Cluster Configuration: No need to tune VM node types, DBR versions, or driver memory.",
                "Optimized for Micro-Batches: Drastically reduces costs for short, frequent jobs."
            ],
            "interview_questions": [
                "How does Serverless compute for Workflows eliminate VM provisioning latency?",
                "What are the networking and storage access prerequisites for enabling Serverless Workflows?"
            ]
        },
        {
            "nb_id": "052",
            "title": "Repair and Rerun Workflows: Surgical Partial DAG Replay on Upstream Failures",
            "filename": "052_repair_and_rerun_workflows_surgical_partial_dag_replay_on_upstream_failures.py",
            "difficulty": "Intermediate",
            "business_scenario": "In a 12-task pipeline that took 3 hours to process 10 tasks, Task 11 failed due to a schema bug in an external dimension table. Re-running the entire 3-hour job from scratch violates executive SLAs.",
            "problem_statement": "Demonstrate the 'Repair and Rerun' operational workflow in Databricks Jobs, executing only the failed task and its downstream children while preserving upstream state.",
            "architectural_notes": "Databricks Workflows records the state of each task in a job run. The Repair and Rerun capability allows operators to fix the underlying issue and replay only failed and downstream tasks, saving hours of compute time.",
            "sections": [
                {
                    "title": "1. Repair and Rerun DAG State Simulation",
                    "explanation": "Simulate partial DAG state and determine which tasks require re-execution.",
                    "code": """job_run_state = {
    "run_id": 998822,
    "tasks": {
        "task_1_bronze": "SUCCESS",
        "task_2_silver": "SUCCESS",
        "task_3_feature_prep": "SUCCESS",
        "task_4_model_training": "FAILED", # FAILED TASK
        "task_5_model_evaluation": "UPSTREAM_FAILED" # SKIPPED CHILD
    }
}

# Repair algorithm: find failed tasks and all downstream dependencies
tasks_to_rerun = [k for k, v in job_run_state["tasks"].items() if v in ("FAILED", "UPSTREAM_FAILED")]
preserved_tasks = [k for k, v in job_run_state["tasks"].items() if v == "SUCCESS"]

print(f"Tasks Preserved (Zero re-computation): {preserved_tasks}")
print(f"Tasks Surgically Re-executed: {tasks_to_rerun}")
assert len(tasks_to_rerun) == 2
assert len(preserved_tasks) == 3
"""
                }
            ],
            "key_takeaways": [
                "SLA Protection: Saves hours of re-computation by skipping completed upstream tasks.",
                "Cost Efficient: Prevents paying twice for successful heavy ETL transformations.",
                "Idempotent Sinks: Ensure target tables support safe retries via `MERGE INTO` or atomic overwrites."
            ],
            "interview_questions": [
                "How does the Repair and Rerun feature in Databricks Workflows preserve upstream task context?",
                "Can you alter task parameters before triggering a Repair and Rerun?"
            ]
        },
        {
            "nb_id": "053",
            "title": "Lakeflow Job Parameters & Dynamic Base Parameters Inheritance",
            "filename": "053_lakeflow_job_parameters_and_dynamic_base_parameters_inheritance.py",
            "difficulty": "Foundational",
            "business_scenario": "A reusable enterprise workflow template is executed across multiple business units and dates. The job must accept runtime parameters (`env`, `target_date`, `batch_id`) and propagate them to child tasks.",
            "problem_statement": "Configure top-level Job Parameters in Lakeflow Jobs, pass them into task `base_parameters`, and consume them via `dbutils.widgets.get()` inside notebooks.",
            "architectural_notes": "Lakeflow Jobs provides dynamic parameter substitution. Top-level job parameters can be referenced in task configurations using `{{job.parameters.param_name}}` and dynamic values like `{{job.start_time.iso_date}}`.",
            "sections": [
                {
                    "title": "1. Parameter Inheritance & Widget Binding",
                    "explanation": "Verify parameter substitution syntax and consumption in Python tasks.",
                    "code": """# Simulate notebook widget extraction
mock_widgets = {
    "target_date": "2026-11-17",
    "environment": "production",
    "batch_size": "50000"
}

def get_job_param(key: str, default: str = "") -> str:
    return mock_widgets.get(key, default)

target_date = get_job_param("target_date")
env = get_job_param("environment")

print(f"Execution Target Date: {target_date} | Environment: {env}")
assert target_date == "2026-11-17"
assert env == "production"
"""
                }
            ],
            "key_takeaways": [
                "Dynamic Variables: Use built-in variables like `{{job.start_time.iso_date}}` for automated date slicing.",
                "Widget Decoupling: Notebooks can be tested interactively with default widget values or run via Jobs.",
                "Parameter Scoping: Override top-level parameters for specific tasks where needed."
            ],
            "interview_questions": [
                "What built-in dynamic parameter variables are available in Databricks Workflows?",
                "How do you pass dynamic parameters to a Databricks Job when triggering it via the REST API?"
            ]
        },
        {
            "nb_id": "054",
            "title": "Orchestration Governance: Monitoring Job Run History via System Tables",
            "filename": "054_orchestration_governance_monitoring_job_run_history_via_system_tables.py",
            "difficulty": "Intermediate",
            "business_scenario": "A Data Operations manager requires a dashboard tracking pipeline success rates, average runtime trends, and identifying recurring failure modes across 100+ production jobs.",
            "problem_statement": "Query Unity Catalog System Tables to audit job execution history, measure duration percentiles ($P50, P90, P99$), and detect pipeline regressions.",
            "architectural_notes": "Databricks exposes job execution metrics via `system.lakeflow.jobs` and related compute telemetry tables, enabling enterprise-wide pipeline observability without third-party monitoring agents.",
            "sections": [
                {
                    "title": "1. SQL Query for Pipeline SLA & Failure Analytics",
                    "explanation": "Construct analytical queries over system tables to track pipeline health.",
                    "code": """sql_job_monitoring = \"\"\"
-- Query job run history to audit durations and failure rates
SELECT 
    job_name,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_runs,
    ROUND(SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
    ROUND(AVG(execution_duration_ms) / 1000, 2) AS avg_duration_sec,
    ROUND(PERCENTILE(execution_duration_ms, 0.95) / 1000, 2) AS p95_duration_sec
FROM system.lakeflow.job_run_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY job_name
ORDER BY total_runs DESC;
\"\"\"

print("Job orchestration monitoring query verified.")
assert "system.lakeflow.job_run_history" in sql_job_monitoring
"""
                }
            ],
            "key_takeaways": [
                "Automated Observability: Monitor job SLAs without third-party agents using built-in system tables.",
                "Duration Percentiles: Track P95 and P99 execution times to identify pipeline slowdowns before SLAs breach.",
                "Audit Ready: Maintain long-term compliance records of every production execution."
            ],
            "interview_questions": [
                "Which system tables provide metadata regarding Databricks Jobs and task run histories?",
                "How can you automate alerts when a critical production job exceeds its historical average runtime by 50%?"
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
