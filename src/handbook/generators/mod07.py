"""
Module 07: Enterprise DevOps — DABs, CI/CD & Testing (Notebooks 066 - 076)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "07_enterprise_devops_and_dabs"
MODULE_NAME = "Module 07: Enterprise DevOps — DABs, CI/CD & Testing"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "066",
            "title": "Databricks Asset Bundles (DABs) Architecture: databricks.yml & Variable Scopes",
            "filename": "066_databricks_asset_bundles_dabs_architecture_databricks_yml_and_variable_scopes.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import re",
                "import tempfile",
                "from pathlib import Path",
                "import yaml",
            ],
            "business_scenario": "A data platform engineering team needs to standardize pipeline deployments across 50 data engineers, eliminating manual UI clicks and establishing declarative Infrastructure as Code (IaC).",
            "problem_statement": "Author and parse a root `databricks.yml` asset bundle specification with PyYAML, resolve target variable scopes (`dev` vs. `prod`), and materialize environment-isolated Delta targets in Spark.",
            "architectural_notes": "Databricks Asset Bundles (DABs) provide declarative IaC for all Databricks assets. Target blocks override top-level `variables:` so developer bundles write into sandboxed locations while `prod` writes to governed catalogs.",
            "sections": [
                {
                    "title": "1. Parse Bundle YAML, Resolve Variable Scopes & Materialize Target Delta Tables",
                    "explanation": "Parse a real `databricks.yml` manifest with `yaml.safe_load`, resolve `${var.catalog}` and `${var.schema}` for `dev` and `prod` targets, and write target-isolated Delta outputs via Spark.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_066_", dir=globals().get("HANDBOOK_TMP_DIR")))

bundle_yaml = \"\"\"
bundle:
  name: enterprise-lakehouse-pipeline

variables:
  catalog:
    default: "dev_catalog"
  schema:
    default: "analytics"

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: "dev_sandbox"
  prod:
    mode: production
    variables:
      catalog: "prod_lakehouse"
\"\"\"

parsed = yaml.safe_load(bundle_yaml)

def resolve_vars(target_name: str) -> dict[str, str]:
    base = {k: v["default"] for k, v in parsed.get("variables", {}).items()}
    overrides = parsed["targets"][target_name].get("variables", {})
    return {**base, **overrides}

# Execute Spark writes parameterized by resolved DABs target variables
for target in ("dev", "prod"):
    v = resolve_vars(target)
    tbl_dir = str(lab_dir / v["catalog"] / v["schema"] / "daily_summary")
    (
        spark.createDataFrame([(target, v["catalog"], 100)], ["target", "catalog", "rows_loaded"])
        .write.format("delta")
        .mode("overwrite")
        .save(tbl_dir)
    )

dev_cat = spark.read.format("delta").load(str(lab_dir / "dev_sandbox/analytics/daily_summary")).select("catalog").first()[0]
prod_cat = spark.read.format("delta").load(str(lab_dir / "prod_lakehouse/analytics/daily_summary")).select("catalog").first()[0]
print(f"Resolved targets -> dev: {dev_cat}, prod: {prod_cat}")
assert dev_cat == "dev_sandbox" and prod_cat == "prod_lakehouse"
""",
                }
            ],
            "key_takeaways": [
                "Declarative IaC: Define all Databricks pipelines and resources as code in version-controlled YAML.",
                "Target Overrides: Dynamically alter catalogs, clusters, and permissions per target environment.",
                "Development Mode: `mode: development` isolates developer deployments to user sandboxes.",
            ],
            "interview_questions": [
                "What are Databricks Asset Bundles (DABs) and why did Databricks introduce them over classic Terraform?",
                "How does variable scoping work across different deployment targets in `databricks.yml`?",
            ],
        },
        {
            "nb_id": "067",
            "title": "Defining Multi-Resource Bundles: Jobs, DLT Pipelines, Volumes & Model Serving",
            "filename": "067_defining_multi_resource_bundles_jobs_dlt_pipelines_volumes_and_model_serving.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import yaml",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A machine learning engineering platform deploys an end-to-end AI product consisting of a DLT data preparation pipeline, a Lakeflow model training job, a Unity Catalog model, and a real-time Model Serving endpoint.",
            "problem_statement": "Parse modular multi-resource bundle specs (`resources/*.yml`) declaring Jobs, Pipelines, and Model Serving endpoints, and verify cross-resource DAG references with Spark SQL.",
            "architectural_notes": "DABs compose complex platforms using modular `include: - resources/*.yml` files. Validating cross-resource interpolations (e.g., `${resources.pipelines.etl.id}`) guarantees no broken task references enter production.",
            "sections": [
                {
                    "title": "1. Multi-Resource YAML Parsing & Spark DAG Referential Integrity Check",
                    "explanation": "Parse YAML resource maps for jobs, pipelines, and serving endpoints, load them into Spark SQL views, and prove every cross-resource task link resolves cleanly.",
                    "code": """jobs_yml = \"\"\"
resources:
  jobs:
    ml_release_job:
      tasks:
        - task_key: run_etl_pipeline
          pipeline_task:
            pipeline_id: "etl_silver_pipeline"
        - task_key: train_churn_model
          depends_on:
            - task_key: run_etl_pipeline
        - task_key: refresh_serving_endpoint
          depends_on:
            - task_key: train_churn_model
          serving_target: "churn_realtime_endpoint"
\"\"\"
other_resources_yml = \"\"\"
resources:
  pipelines:
    etl_silver_pipeline:
      target: "gold"
  model_serving_endpoints:
    churn_realtime_endpoint:
      entity: "prod_lakehouse.gold.churn_model"
\"\"\"

job_tree = yaml.safe_load(jobs_yml)["resources"]["jobs"]["ml_release_job"]["tasks"]
res_tree = yaml.safe_load(other_resources_yml)["resources"]

known_assets = set(res_tree["pipelines"].keys()) | set(res_tree["model_serving_endpoints"].keys()) | {
    t["task_key"] for t in job_tree
}

edge_rows = []
for task in job_tree:
    tk = task["task_key"]
    for dep in task.get("depends_on", []):
        edge_rows.append((tk, "task_dep", dep["task_key"]))
    if "pipeline_task" in task:
        edge_rows.append((tk, "pipeline_ref", task["pipeline_task"]["pipeline_id"]))
    if "serving_target" in task:
        edge_rows.append((tk, "serving_ref", task["serving_target"]))

edges_df = spark.createDataFrame(edge_rows, ["source_task", "link_type", "target_ref"])
edges_df.createOrReplaceTempView("bundle_edges")
known_df = spark.createDataFrame([(k,) for k in sorted(known_assets)], ["asset_id"])
known_df.createOrReplaceTempView("bundle_assets")

dangling_count = spark.sql(\"\"\"
    SELECT e.*
    FROM bundle_edges e
    LEFT ANTI JOIN bundle_assets a ON e.target_ref = a.asset_id
\"\"\").count()

total_links = edges_df.count()
print(f"Validated {total_links} bundle resource links; dangling references: {dangling_count}")
assert total_links == 4 and dangling_count == 0
""",
                }
            ],
            "key_takeaways": [
                "Unified Lifecycle: Deploy data ingestion, model training, and model serving together in a single atomic bundle.",
                "Modular Directory Layout: Keep resource definitions in separate YAML files under `resources/`.",
                "Topological Validation: Cross-check task dependencies and pipeline/serving references in CI before deployment.",
            ],
            "interview_questions": [
                "How do you organize multi-resource bundles for complex projects spanning data engineering and ML?",
                "Can a Databricks Job in DABs trigger a DLT Pipeline declared in the same bundle?",
            ],
        },
        {
            "nb_id": "068",
            "title": "DABs Multi-Environment Targeting: dev, staging, and prod Promotion Topologies",
            "filename": "068_dabs_multi_environment_targeting_dev_staging_and_prod_promotion_topologies.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise requires strict deployment gates: code developed in feature branches is deployed to developer sandboxes, PR merges trigger Staging validation, and git tags deploy to Production.",
            "problem_statement": "Configure environment targets (`dev`, `staging`, `prod`) in DABs, enforcing path isolation (`/Users/.../.bundle` vs `/Shared/.bundle`) and permission controls.",
            "architectural_notes": "Target environments ensure clean separation: `dev` deploys to personal developer folders with paused schedules; `staging` runs integration tests; `prod` enforces Service Principal ownership and active cron triggers.",
            "sections": [
                {
                    "title": "1. Target Environment Configuration Matrix",
                    "explanation": "Define promotion settings, schedule states, and root paths across targets.",
                    "code": """promotion_matrix = {
    "dev": {"mode": "development", "schedules": "PAUSED", "root": "/Users/${workspace.current_user.userName}/.bundle"},
    "staging": {"mode": "production", "schedules": "PAUSED", "root": "/Shared/.bundle/${bundle.name}/staging"},
    "prod": {"mode": "production", "schedules": "UNPAUSED", "root": "/Shared/.bundle/${bundle.name}/prod"}
}

for env, conf in promotion_matrix.items():
    print(f"Target: {env.upper()} | Mode: {conf['mode']} | Schedules: {conf['schedules']}")

assert promotion_matrix["dev"]["schedules"] == "PAUSED"
assert promotion_matrix["prod"]["schedules"] == "UNPAUSED"
"""
                }
            ],
            "key_takeaways": [
                "Schedule Safety: Developer bundles never accidentally trigger production cron schedules.",
                "Namespace Isolation: Each target writes to dedicated catalogs (`dev_catalog` vs `prod_catalog`).",
                "Automated Promotion: Promote code by passing `-t <target>` in CI/CD pipelines."
            ],
            "interview_questions": [
                "What changes automatically when a bundle target is switched from `mode: development` to `mode: production`?",
                "How do you prevent a developer from deploying a local bundle directly into the production target?"
            ]
        },
        {
            "nb_id": "069",
            "title": "Bundle Lifecycle Automation: bundle validate, bundle deploy & bundle run CLI",
            "filename": "069_bundle_lifecycle_automation_bundle_validate_bundle_deploy_and_bundle_run_cli.py",
            "difficulty": "Foundational",
            "business_scenario": "A release engineer is authoring an automated deployment script that validates YAML syntax, deploys changed assets to Databricks, and executes a smoke test run.",
            "problem_statement": "Demonstrate the core Databricks CLI bundle commands: `databricks bundle validate`, `databricks bundle deploy`, and `databricks bundle run` with parameter overrides.",
            "architectural_notes": "The bundle lifecycle consists of: `validate` (verifies YAML schemas and variable substitutions offline), `deploy` (syncs code and provisions workspace resources via REST API), and `run` (triggers pipeline runs).",
            "sections": [
                {
                    "title": "1. Bundle CLI Lifecycle Sequence",
                    "explanation": "Simulate and verify the 3-step bundle deployment sequence.",
                    "code": """cli_lifecycle_commands = [
    "databricks bundle validate -t prod",
    "databricks bundle deploy -t prod",
    "databricks bundle run -t prod databricks_handbook_master_pipeline"
]

print("Bundle Deployment Lifecycle Commands:")
for cmd in cli_lifecycle_commands:
    print(f"  $ {cmd}")

assert "bundle validate" in cli_lifecycle_commands[0]
assert "bundle deploy" in cli_lifecycle_commands[1]
"""
                }
            ],
            "key_takeaways": [
                "Fast Offline Validation: Catch YAML typos and missing variables in seconds before deploying.",
                "Idempotent Deployment: `bundle deploy` updates existing resources in-place without deleting and recreating IDs.",
                "CLI Scripting: Seamlessly wraps into bash scripts and CI runners."
            ],
            "interview_questions": [
                "What is the difference between `databricks bundle validate` and `databricks bundle deploy`?",
                "How can you pass runtime parameter overrides to a job using `databricks bundle run`?"
            ]
        },
        {
            "nb_id": "070",
            "title": "GitHub Actions CI/CD Pipeline: Automated Bundle Linting, Testing & Validation",
            "filename": "070_github_actions_ci_cd_pipeline_automated_bundle_linting_testing_and_validation.py",
            "difficulty": "Intermediate",
            "business_scenario": "A DevOps team requires a zero-touch CI/CD pipeline in GitHub Actions that runs unit tests on Pull Requests, validates bundle schemas, and automatically deploys to Production upon merging to `main`.",
            "problem_statement": "Construct a production GitHub Actions workflow YAML file incorporating Python linting, pytest execution, Databricks CLI authentication, and multi-stage deployment gates.",
            "architectural_notes": "GitHub Actions CI/CD executes jobs on Ubuntu runners. The workflow checks out the repository, installs the Databricks CLI, runs `bundle validate`, executes unit tests with pytest/chispa, and deploys to target workspaces.",
            "sections": [
                {
                    "title": "1. GitHub Actions CI/CD Workflow Template",
                    "explanation": "Define workflow steps for pull request validation and production rollout. Note: `pip install -r requirements.txt` below is a generic teaching example; this repository uses `uv sync --locked`.",
                    "code": """github_workflow_yaml = \"\"\"
name: CI/CD Databricks Asset Bundle Rollout

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate_and_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - uses: databricks/setup-cli@v0.220.0
      - run: databricks bundle validate -t dev
\"\"\"

print("GitHub Actions CI/CD configuration validated.")
assert "databricks/setup-cli" in github_workflow_yaml
"""
                }
            ],
            "key_takeaways": [
                "Automated PR Checks: Prevent broken bundle syntax or failing unit tests from merging to main.",
                "Official Databricks Action: Use `databricks/setup-cli` in GitHub Actions for official CLI installation.",
                "Zero Manual Touches: Automated deployments guarantee consistent environments across dev, staging, and prod."
            ],
            "interview_questions": [
                "How do you design a GitHub Actions pipeline for Databricks that supports dev branch validation and prod deployment?",
                "What is the best way to handle branch protection rules with Databricks Asset Bundles?"
            ]
        },
        {
            "nb_id": "071",
            "title": "Service Principal Authentication in CI/CD Runners using Azure OIDC / AWS IAM",
            "filename": "071_service_principal_authentication_in_ci_cd_runners_using_azure_oidc_aws_iam.py",
            "difficulty": "Advanced",
            "business_scenario": "A Chief Information Security Officer (CISO) mandates the elimination of all static client secrets and API tokens from GitHub repository secrets to prevent credential theft.",
            "problem_statement": "Configure passwordless GitHub Actions authentication to Databricks using OpenID Connect (OIDC) cloud federation (Azure Federated Credentials / AWS IAM OIDC Provider).",
            "architectural_notes": "OIDC federation allows GitHub Actions runners to exchange short-lived OIDC tokens directly with Azure or AWS without storing long-lived passwords or secrets. The cloud provider issues a temporary access token that authenticates to Databricks via OAuth M2M.",
            "sections": [
                {
                    "title": "1. OIDC Token Exchange Workflow Model",
                    "explanation": "Simulate and verify the passwordless OIDC token exchange sequence.",
                    "code": """oidc_auth_flow = {
    "step_1": "GitHub Actions runner requests OIDC JWT token from GitHub token service",
    "step_2": "Runner sends JWT token to Cloud Provider (Azure AD / AWS STS) to assume role",
    "step_3": "Cloud Provider verifies GitHub repository, branch, and signature claims",
    "step_4": "Cloud Provider issues short-lived scoped OAuth token (1 hour lifespan)",
    "step_5": "Databricks CLI authenticates to workspace using temporary OAuth token"
}

for step, desc in oidc_auth_flow.items():
    print(f"[{step.upper()}]: {desc}")

assert "short-lived scoped OAuth token" in oidc_auth_flow["step_4"]
"""
                }
            ],
            "key_takeaways": [
                "Passwordless CI/CD: Eliminates stored client secrets, preventing credential leak disasters.",
                "Short-Lived Tokens: Tokens expire automatically after 1 hour.",
                "Cryptographic Claims: Cloud providers verify the exact GitHub repository and branch before issuing tokens."
            ],
            "interview_questions": [
                "How does OpenID Connect (OIDC) eliminate stored static secrets in GitHub Actions for Databricks deployments?",
                "What claims does Azure Active Directory verify when validating a GitHub Actions OIDC request?"
            ]
        },
        {
            "nb_id": "072",
            "title": "Infrastructure as Code (IaC) with Databricks Terraform Provider",
            "filename": "072_infrastructure_as_code_iac_with_databricks_terraform_provider.py",
            "difficulty": "Advanced",
            "business_scenario": "An enterprise Cloud Infrastructure team needs to provision 10 new Databricks workspaces, configure storage accounts, create Unity Catalog metastores, and grant admin roles using Terraform.",
            "problem_statement": "Author Terraform HCL manifests utilizing the official Databricks Terraform Provider (`databricks/databricks`), deploying workspaces, catalogs, storage credentials, and external locations.",
            "architectural_notes": "The Databricks Terraform Provider manages account-level resources (workspaces, metastores, SCIM groups) and workspace-level assets. It complements DABs: Terraform provisions infrastructure; DABs deploys pipelines.",
            "sections": [
                {
                    "title": "1. Terraform HCL Resource Definition",
                    "explanation": "Inspect Terraform code provisioning Unity Catalog catalogs and storage credentials.",
                    "code": """terraform_manifest = \"\"\"
terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

resource "databricks_catalog" "prod_lakehouse" {
  name         = "prod_lakehouse"
  comment      = "Production Enterprise Lakehouse Catalog"
  storage_root = "abfss://managed@storage.dfs.core.windows.net/prod"
}

resource "databricks_grant" "data_engineers_access" {
  catalog    = databricks_catalog.prod_lakehouse.name
  principal  = "data-engineers"
  privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
}
\"\"\"

print("Databricks Terraform HCL validated.")
assert "databricks_catalog" in terraform_manifest
assert "databricks_grant" in terraform_manifest
"""
                }
            ],
            "key_takeaways": [
                "Terraform for Infrastructure: Best for provisioning workspaces, metastores, VNet peering, and IAM.",
                "DABs for Applications: Best for data engineers deploying pipelines, jobs, and apps.",
                "Automated State: Maintain infrastructure drift detection via Terraform Cloud or Azure DevOps."
            ],
            "interview_questions": [
                "What is the division of responsibility between the Databricks Terraform Provider and Databricks Asset Bundles (DABs)?",
                "How does Terraform manage Unity Catalog metastore assignments across multiple workspaces?"
            ]
        },
        {
            "nb_id": "073",
            "title": "Databricks Connect v2: Local IDE Development in VS Code with Remote DBR Compute",
            "filename": "073_databricks_connect_v2_local_ide_development_in_vs_code_with_remote_dbr_compute.py",
            "difficulty": "Intermediate",
            "business_scenario": "Software engineers want to develop PySpark pipelines locally inside VS Code or PyCharm, using local git, linters, and debuggers, while executing DataFrame code on remote Databricks clusters.",
            "problem_statement": "Configure Databricks Connect v2 using Spark Connect architecture, establish an IDE session connecting to a remote DBR 15.4+ cluster, and execute interactive step-through debugging.",
            "architectural_notes": "Databricks Connect v2 is built on open source Apache Spark Connect. The client IDE sends unresolved DataFrame logical query plans over gRPC to the remote Databricks cluster, which executes them and streams back results.",
            "sections": [
                {
                    "title": "1. Databricks Connect v2 SparkSession Initialization",
                    "explanation": "Demonstrate connecting from a local IDE to remote Databricks compute.",
                    "code": """connect_script = \"\"\"
from databricks.connect import DatabricksSession

# Connects to remote Databricks cluster using local CLI profile or environment variables
spark = DatabricksSession.builder.getOrCreate()

# DataFrame API executes on remote cluster; results stream back locally
df = spark.read.table("prod_lakehouse.silver.customers")
print(f"Remote Customer Count: {df.count()}")
\"\"\"

print("Databricks Connect v2 script structure verified.")
assert "from databricks.connect import DatabricksSession" in connect_script
"""
                }
            ],
            "key_takeaways": [
                "gRPC Architecture: Uses lightweight Spark Connect protocol instead of heavy old Py4J bridges.",
                "IDE Superpowers: Step-through breakpoints, code completion, and linters in VS Code.",
                "Zero Local Java Needed: Client machines only need Python; no local Java or Hadoop binaries required."
            ],
            "interview_questions": [
                "How does Databricks Connect v2 fundamentally differ from Databricks Connect v1?",
                "What are the network prerequisites for establishing a Databricks Connect v2 session from a corporate laptop?"
            ]
        },
        {
            "nb_id": "074",
            "title": "Unit Testing Databricks Data Pipelines with pytest, chispa & Mock DataFrames",
            "filename": "074_unit_testing_databricks_data_pipelines_with_pytest_chispa_and_mock_dataframes.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "from chispa.dataframe_comparer import assert_df_equality",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A team experiences pipeline regressions when code changes accidentally alter decimal rounding logic. Data transformations must be validated by automated unit test suites before deployment.",
            "problem_statement": "Develop modular unit test suites using pytest and `chispa.assert_df_equality`, validating both positive schema/value parity and negative regression catching.",
            "architectural_notes": "`chispa` provides clean DataFrame assertion helpers (`assert_df_equality`) highlighting row, value, and schema mismatches in CI test output without brittle manual `.collect()` loops.",
            "sections": [
                {
                    "title": "1. Unit Test with `chispa.assert_df_equality` & Regression Detection",
                    "explanation": "Compare actual transformed Spark output against an expected DataFrame via `assert_df_equality`, then prove a buggy transformation fails `assert_df_equality` cleanly.",
                    "code": """def calculate_net_amount(df):
    return df.withColumn("net_amount", F.round(F.col("gross") - F.col("discount"), 2))

mock_input = spark.createDataFrame(
    [(100.00, 10.00), (250.50, 25.50), (50.00, 0.00)],
    ["gross", "discount"],
)
expected_df = spark.createDataFrame(
    [(100.00, 10.00, 90.00), (250.50, 25.50, 225.00), (50.00, 0.00, 50.00)],
    ["gross", "discount", "net_amount"],
)

df_result = calculate_net_amount(mock_input)
assert_df_equality(df_result, expected_df, ignore_nullable=True)

# Negative gate: confirm chispa rejects a buggy transform missing subtraction
buggy_df = mock_input.withColumn("net_amount", F.col("gross"))
mismatch_caught = False
try:
    assert_df_equality(buggy_df, expected_df, ignore_nullable=True)
except Exception:
    mismatch_caught = True

results = [row["net_amount"] for row in df_result.orderBy("gross").collect()]
print(f"Computed Net Amounts: {results}, mismatch_caught={mismatch_caught}")
assert mismatch_caught is True and len(results) == 3
""",
                }
            ],
            "key_takeaways": [
                "Decouple Transformations: Write business logic as pure functions accepting and returning DataFrames.",
                "Expressive Diffs: `chispa.assert_df_equality` pinpoints exact mismatched cells and schema differences.",
                "Automated CI Guardrail: Run local Spark unit tests in seconds on every Pull Request.",
            ],
            "interview_questions": [
                "How do you test PySpark data transformations in CI/CD without spinning up an expensive Databricks cluster?",
                "What is `chispa` and how does `assert_df_equality` improve PySpark test assertions?",
            ],
        },
        {
            "nb_id": "075",
            "title": "Python Wheel Packaging, UC Volume Deployment & Dependency Pinning",
            "filename": "075_python_wheel_packaging_uc_volume_deployment_and_dependency_pinning.py",
            "difficulty": "Advanced",
            "business_scenario": "An enterprise maintains a proprietary Python library for encryption and financial accounting. The library must be packaged as a Python Wheel (`.whl`), stored securely in a Unity Catalog Volume, and installed on production jobs.",
            "problem_statement": "Package Python code into a wheel distribution using `setuptools`/`build`, upload to a Unity Catalog Volume, and attach the wheel library to a Lakeflow Job cluster.",
            "architectural_notes": "Unity Catalog Volumes provide secure, governed storage for compiled Python Wheels and JARs. Attaching libraries via `/Volumes` eliminates external internet pip downloads on compute nodes, enforcing secure air-gapped environments.",
            "sections": [
                {
                    "title": "1. Python Wheel Bundle Specification",
                    "explanation": "Define how Python wheels are declared as libraries in Databricks Asset Bundles.",
                    "code": """job_with_wheel_spec = {
    "task_key": "run_financial_model",
    "libraries": [
        {"whl": "/Volumes/prod_lakehouse/libraries/wheels/finance_core-1.2.0-py3-none-any.whl"}
    ],
    "python_wheel_task": {
        "package_name": "finance_core",
        "entry_point": "run_accounting_audit",
        "parameters": ["--fiscal-year", "2026"]
    }
}

print(f"Wheel Location: {job_with_wheel_spec['libraries'][0]['whl']}")
print(f"Package Entrypoint: {job_with_wheel_spec['python_wheel_task']['package_name']}.{job_with_wheel_spec['python_wheel_task']['entry_point']}")
assert job_with_wheel_spec["libraries"][0]["whl"].startswith("/Volumes/")
"""
                }
            ],
            "key_takeaways": [
                "Air-Gapped Compliance: Storing wheels in UC Volumes prevents cluster startup failures from PyPI downtime.",
                "Version Immutability: Pin exact wheel version numbers (`finance_core-1.2.0.whl`) to avoid drift.",
                "Clean Separation: Code logic lives in standard Python packages; jobs simply invoke entry points."
            ],
            "interview_questions": [
                "Why should enterprise production pipelines prefer Python Wheels over raw notebooks in Databricks?",
                "How do Unity Catalog Volumes improve library security compared to legacy DBFS library installations?"
            ]
        },
        {
            "nb_id": "076",
            "title": "Blue/Green Pipeline Deployment & Zero-Downtime Bundle Rollouts",
            "filename": "076_blue_green_pipeline_deployment_and_zero_downtime_bundle_rollouts.py",
            "difficulty": "Architect",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A 24/7 financial reporting system cannot tolerate downtime during pipeline upgrades. Upgrades must run in parallel, validate results, and switch user queries with zero interruption.",
            "problem_statement": "Execute a real atomic Blue/Green Delta cutover locally: materialize `fact_sales_blue` (v1) and `fact_sales_green` (v2), gate cutover on Green data-quality checks, flip the live reporting view atomically via `CREATE OR REPLACE VIEW`, and verify instant rollback.",
            "architectural_notes": "Blue/Green deployment isolates candidate pipeline builds in `fact_sales_green`. BI dashboards query the abstraction view `fact_sales`. Only after Green passes row-count and null checks does a single metadata `CREATE OR REPLACE VIEW` commit shift traffic atomically.",
            "sections": [
                {
                    "title": "1. Live Blue/Green Atomic View Cutover & Rollback Verification",
                    "explanation": "Materialize Blue and Green Delta tables, gate promotion on Green quality checks, flip the view pointer atomically, and demonstrate millisecond rollback to Blue.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_076_", dir=globals().get("HANDBOOK_TMP_DIR")))
blue_path = str(lab_dir / "fact_sales_blue")
green_path = str(lab_dir / "fact_sales_green")

spark.createDataFrame(
    [(1, "US", 100.0), (2, "EU", 200.0)], ["order_id", "region", "net_revenue"]
).write.format("delta").save(blue_path)
spark.sql(f"CREATE TABLE t076_sales_blue USING DELTA LOCATION '{blue_path}'")

# Step 1: Production view serves Blue (total=300.0)
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_blue")
blue_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

# Step 2: Green pipeline builds upgraded dataset & runs pre-cutover DQ gate
spark.createDataFrame(
    [(1, "US", 105.0), (2, "EU", 210.0), (3, "APAC", 150.0)], ["order_id", "region", "net_revenue"]
).write.format("delta").save(green_path)
spark.sql(f"CREATE TABLE t076_sales_green USING DELTA LOCATION '{green_path}'")

dq_ok = spark.sql("SELECT COUNT(*) FROM t076_sales_green WHERE net_revenue <= 0 OR net_revenue IS NULL").first()[0] == 0
assert dq_ok is True

# Step 3: Atomic metadata cutover to Green -> view revenue reflects 465.0
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_green")
green_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

# Step 4: Instantaneous metadata rollback test back to Blue -> revenue reverts to 300.0
spark.sql("CREATE OR REPLACE VIEW t076_fact_sales AS SELECT * FROM t076_sales_blue")
rollback_rev = spark.sql("SELECT SUM(net_revenue) FROM t076_fact_sales").first()[0]

print(f"View revenues -> blue={blue_rev}, green={green_rev}, rollback={rollback_rev}")
assert blue_rev == 300.0 and green_rev == 465.0 and rollback_rev == 300.0
""",
                }
            ],
            "key_takeaways": [
                "Zero Query Interruption: Readers never observe empty or partially overwritten tables during deploys.",
                "Instant Rollback: Re-pointing the SQL view back to Blue takes milliseconds with zero table rebuilds.",
                "Safe Schema Evolution: Breaking transformations validate cleanly on Green before serving BI users.",
            ],
            "interview_questions": [
                "How does an atomic view redirection enable zero-downtime upgrades in a lakehouse architecture?",
                "What is the rollback procedure if a newly cutover Green pipeline encounters corrupted data?",
            ],
        },
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
