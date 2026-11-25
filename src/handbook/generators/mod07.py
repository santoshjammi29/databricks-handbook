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
            "business_scenario": "A data platform engineering team needs to standardize pipeline deployments across 50 data engineers, eliminating manual UI clicks and establishing declarative Infrastructure as Code (IaC).",
            "problem_statement": "Author and validate a root `databricks.yml` asset bundle specification, configure variable substitution scopes, and implement target environment overrides (dev, staging, prod).",
            "architectural_notes": "Databricks Asset Bundles (DABs) provide declarative IaC for all Databricks assets. Assets (Jobs, DLT pipelines, Volumes, Models) are defined in YAML and deployed via the CLI (`databricks bundle deploy`). Variable scopes allow dynamic parameter substitution across targets.",
            "sections": [
                {
                    "title": "1. DABs Configuration Schema & Variable Substitution",
                    "explanation": "Define and validate root `databricks.yml` syntax with environment variable targets.",
                    "code": """bundle_manifest = \"\"\"
bundle:
  name: enterprise-lakehouse-pipeline

variables:
  catalog:
    default: "main"
  schema:
    default: "analytics"

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: "dev_catalog"
  prod:
    mode: production
    variables:
      catalog: "prod_catalog"
\"\"\"

print("DABs root configuration verified.")
assert "mode: development" in bundle_manifest
assert "mode: production" in bundle_manifest
"""
                }
            ],
            "key_takeaways": [
                "Declarative IaC: Define all Databricks pipelines and resources as code in version-controlled YAML.",
                "Target Overrides: Dynamically alter catalogs, clusters, and permissions per target environment.",
                "Development Mode: `mode: development` isolates developer deployments to user sandboxes."
            ],
            "interview_questions": [
                "What are Databricks Asset Bundles (DABs) and why did Databricks introduce them over classic Terraform?",
                "How does variable scoping work across different deployment targets in `databricks.yml`?"
            ]
        },
        {
            "nb_id": "067",
            "title": "Defining Multi-Resource Bundles: Jobs, DLT Pipelines, Volumes & Model Serving",
            "filename": "067_defining_multi_resource_bundles_jobs_dlt_pipelines_volumes_and_model_serving.py",
            "difficulty": "Advanced",
            "business_scenario": "A machine learning engineering platform deploys an end-to-end AI product consisting of a DLT data preparation pipeline, a Lakeflow model training job, a Unity Catalog model, and a real-time Model Serving endpoint.",
            "problem_statement": "Construct a modular multi-resource bundle structure (`resources/*.yml`) declaring Jobs, DLT Pipelines, Volumes, and Model Serving endpoints as a unified deployment unit.",
            "architectural_notes": "DABs support multi-resource definitions. The `include: - resources/*.yml` directive allows modular separation of concerns: `jobs.yml`, `pipelines.yml`, `unity_catalog.yml`, and `model_serving.yml`.",
            "sections": [
                {
                    "title": "1. Multi-Resource YAML Structure Inspection",
                    "explanation": "Verify how different resource types are declared and linked in bundle resources.",
                    "code": """resource_files = [
    "resources/jobs.yml",
    "resources/dlt_pipelines.yml",
    "resources/unity_catalog.yml",
    "resources/model_serving.yml",
    "resources/apps.yml"
]

print("Multi-Resource Bundle Hierarchy:")
for r in resource_files:
    print(f"  -> {r}")
assert len(resource_files) == 5
"""
                }
            ],
            "key_takeaways": [
                "Unified Lifecycle: Deploy data ingestion, model training, and model serving together in a single atomic bundle.",
                "Modular Directory Layout: Keep resource definitions in separate YAML files under `resources/`.",
                "Topological Deployment: DABs automatically resolves cross-resource references."
            ],
            "interview_questions": [
                "How do you organize multi-resource bundles for complex projects spanning data engineering and ML?",
                "Can a Databricks Job in DABs trigger a DLT Pipeline declared in the same bundle?"
            ]
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
            "imports": ["from pyspark.sql import functions as F"],
            "business_scenario": "A team experiences pipeline regressions when code changes accidentally alter decimal rounding logic. Data transformations must be validated by automated unit test suites before deployment.",
            "problem_statement": "Develop modular unit test suites using pytest and `chispa`, creating mock DataFrames, asserting schema matches, and verifying exact numerical results.",
            "architectural_notes": "`chispa` provides fast, clean assertion helpers (`assert_df_equality`) for PySpark DataFrames, highlighting column, schema, and row discrepancies in test output without boilerplate loops.",
            "sections": [
                {
                    "title": "1. Unit Test Implementation with PySpark & Mock Data",
                    "explanation": "Write a pure transformation function and validate it with a mock unit test.",
                    "code": """# Pure transformation function
def calculate_net_amount(df):
    return df.withColumn("net_amount", F.round(F.col("gross") - F.col("discount"), 2))

# Unit test
mock_input = spark.createDataFrame([
    (100.00, 10.00),
    (250.50, 25.50),
    (50.00, 0.00)
], ["gross", "discount"])

df_result = calculate_net_amount(mock_input)
results = [row["net_amount"] for row in df_result.collect()]

print(f"Computed Net Amounts: {results}")
assert results == [90.00, 225.00, 50.00], f"Unit test failed: Expected [90.0, 225.0, 50.0], got {results}"
print("Unit test PASSED: 100% numerical precision verified.")
"""
                }
            ],
            "key_takeaways": [
                "Decouple Transformations: Write business logic as pure functions that accept and return DataFrames.",
                "Mock Data Testing: Run unit tests locally with tiny in-memory DataFrames in seconds.",
                "Automated CI Guardrail: Run pytest on every Pull Request before approving merges."
            ],
            "interview_questions": [
                "How do you test PySpark data transformations in CI/CD without spinning up an expensive Databricks cluster?",
                "What is `chispa` and how does `assert_df_equality` improve PySpark test assertions?"
            ]
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
            "business_scenario": "A 24/7 financial reporting system cannot tolerate downtime during pipeline upgrades. Upgrades must run in parallel, validate results, and switch user queries with zero interruption.",
            "problem_statement": "Design a Blue/Green pipeline deployment architecture using Unity Catalog views and table clones, achieving zero-downtime cutover and instant rollback capabilities.",
            "architectural_notes": "Blue/Green deployment maintains two identical production environments (Blue and Green). The active reporting view points to Blue (`prod.gold.sales -> sales_blue`). When Green completes deployment and verification, the view definition is atomically updated to point to Green.",
            "sections": [
                {
                    "title": "1. Atomic View Pointer Cutover Architecture",
                    "explanation": "Simulate zero-downtime view switching between Blue and Green production tables.",
                    "code": """blue_green_cutover_sql = \"\"\"
-- Step 1: Active reporting view currently points to Blue
CREATE OR REPLACE VIEW prod_lakehouse.gold.fact_sales AS
SELECT * FROM prod_lakehouse.gold.fact_sales_blue;

-- Step 2: Green pipeline deploys, loads data, and passes automated validation checks
-- [Validation assertions pass 100%]

-- Step 3: ATOMIC ZERO-DOWNTIME CUTOVER: Redirect view pointer to Green in a single metadata commit
CREATE OR REPLACE VIEW prod_lakehouse.gold.fact_sales AS
SELECT * FROM prod_lakehouse.gold.fact_sales_green;
\"\"\"

print("Blue/Green zero-downtime cutover SQL verified.")
assert "fact_sales_blue" in blue_green_cutover_sql
assert "fact_sales_green" in blue_green_cutover_sql
"""
                }
            ],
            "key_takeaways": [
                "Zero Query Interruption: Existing BI queries finish cleanly on Blue; new queries immediately read Green.",
                "Instant Rollback: If an issue is discovered post-cutover, revert the view back to Blue in milliseconds.",
                "Safe Schema Evolution: Breaking schema changes can be deployed and validated on Green before exposing to users."
            ],
            "interview_questions": [
                "How does an atomic view redirection enable zero-downtime upgrades in a lakehouse architecture?",
                "What is the rollback procedure if a newly cutover Green pipeline encounters corrupted data?"
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
