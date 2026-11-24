"""
Module 01: Platform Architecture, Workspaces & Control Plane (Notebooks 001 - 010)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "01_platform_architecture_and_security"
MODULE_NAME = "Module 01: Platform Architecture, Workspaces & Control Plane"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "001",
            "title": "Split-Plane Cloud Architecture: Control Plane, Classic Compute & Serverless Networking",
            "filename": "001_split_plane_cloud_architecture_control_plane_classic_compute_and_serverless_networking.py",
            "difficulty": "Foundational",
            "business_scenario": "A financial services institution requires a multi-region Databricks deployment adhering to PCI-DSS standards. Enterprise data cannot transit the public internet or reside on vendor infrastructure outside the customer cloud perimeter.",
            "problem_statement": "Demonstrate the operational configuration and security boundary verification of Databricks Split-Plane architecture. Inspect cluster environment variables, verify private connectivity endpoints, and validate storage credential authentication.",
            "architectural_notes": "Databricks decouples the Control Plane (web UI, notebook orchestration, Unity Catalog metastore) from the Compute Plane. In Classic compute, Spark driver and worker VMs run in customer VNets/VPCs. In Serverless compute, hardened container micro-VMs run in a Databricks-managed cloud tenant connecting to storage via private endpoints.",
            "sections": [
                {
                    "title": "1. Inspect Cluster Runtime & Compute Plane Topology",
                    "explanation": "Verify the active Databricks Runtime (DBR) version, cluster ID, and driver IP configuration to ensure private network injection.",
                    "code": """# Inspect environment topology and Spark runtime
cluster_id = spark.conf.get("spark.databricks.clusterUsageTags.clusterId", "local-simulated-cluster")
spark_version = spark.version
dbr_version = spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "15.4.x-scala2.12")

print(f"Active Cluster ID: {cluster_id}")
print(f"Apache Spark Engine: {spark_version}")
print(f"Databricks Runtime (DBR): {dbr_version}")

# Assert DBR 15.4+ baseline compatibility
assert float(spark_version.rsplit(".", 1)[0]) >= 3.5, f"Expected Spark 3.5+, found {spark_version}"
"""
                },
                {
                    "title": "2. Verify Secure Cluster Connectivity (No Public IPs)",
                    "explanation": "Ensure worker nodes establish outbound-only secure reverse tunnels (SCC Relay) without requiring ingress public IP addresses.",
                    "code": """# Simulate cluster network isolation inspection
network_conf = {
    "enableNoPublicIp": True,
    "vnetInjection": "custom-vnet-isolated",
    "privateSubnet": "10.240.1.0/24",
    "publicNetworkAccess": "Disabled"
}

print(f"Secure Cluster Connectivity (No Public IPs): {network_conf['enableNoPublicIp']}")
print(f"Subnet Isolation: {network_conf['privateSubnet']}")
assert network_conf["enableNoPublicIp"] is True, "Security Invariant Violated: Public IPs detected on compute nodes!"
"""
                }
            ],
            "key_takeaways": [
                "Split-Plane Isolation: Customer data resides exclusively in customer storage accounts and compute memory.",
                "Secure Cluster Connectivity: Worker VMs require zero ingress ports or public IPs; they communicate via outbound secure relays.",
                "Serverless Transition: Serverless compute eliminates VM provisioning lag (2-4 seconds startup vs. 4-7 minutes on classic VMs)."
            ],
            "interview_questions": [
                "How does Databricks ensure customer data privacy across the Control Plane and Compute Plane boundary?",
                "What is the function of the Secure Cluster Connectivity (SCC) relay in a customer VNet injection architecture?"
            ]
        },
        {
            "nb_id": "002",
            "title": "Databricks Workspace Topologies: Multi-Workspace Hub-and-Spoke & Private Link",
            "filename": "002_databricks_workspace_topologies_multi_workspace_hub_and_spoke_and_private_link.py",
            "difficulty": "Architect",
            "business_scenario": "A multinational enterprise operates four business units across Dev, Staging, and Prod. Architects must design a multi-workspace hub-and-spoke topology preventing cross-environment data leakage while sharing central Unity Catalog metadata.",
            "problem_statement": "Define the programmatic catalog and workspace binding rules that enforce environment boundaries across dev and prod workspaces while isolating networking via Private Link.",
            "architectural_notes": "A single Unity Catalog Metastore per region binds to multiple workspaces. Workspace binding (`CATALOG BINDING`) allows administrators to restrict production catalogs strictly to production workspaces.",
            "sections": [
                {
                    "title": "1. Define Workspace Catalog Binding Hierarchy",
                    "explanation": "Simulate and validate workspace catalog bindings using Unity Catalog information schema and metadata commands.",
                    "code": """# Establish catalog binding rules across workspaces
workspace_registry = [
    {"workspace_id": "1001", "name": "workspace-dev", "allowed_catalogs": ["dev_lakehouse", "sandbox"]},
    {"workspace_id": "1002", "name": "workspace-staging", "allowed_catalogs": ["staging_lakehouse", "dev_lakehouse"]},
    {"workspace_id": "1003", "name": "workspace-prod", "allowed_catalogs": ["prod_lakehouse"]}
]

def validate_workspace_access(workspace_id: str, target_catalog: str) -> bool:
    for ws in workspace_registry:
        if ws["workspace_id"] == workspace_id:
            return target_catalog in ws["allowed_catalogs"]
    return False

# Assert dev workspace cannot read production catalog
assert not validate_workspace_access("1001", "prod_lakehouse"), "Access Breach: Dev accessed Prod Catalog!"
assert validate_workspace_access("1003", "prod_lakehouse"), "Prod catalog must be accessible in Prod Workspace!"
print("Workspace binding validation passed successfully.")
"""
                }
            ],
            "key_takeaways": [
                "Regional Metastore Binding: One Metastore per region connects to multiple workspaces.",
                "Catalog Isolation: Bind production catalogs exclusively to production workspaces to avoid dev accidental writes.",
                "Dual Private Link: Front-end Private Link for user access; Back-end Private Link for compute plane."
            ],
            "interview_questions": [
                "How do you design environment isolation (Dev/Test/Prod) in Unity Catalog?",
                "What is the difference between Front-end Private Link and Back-end Private Link in Databricks?"
            ]
        },
        {
            "nb_id": "003",
            "title": "Cluster Types & Workload Isolation: All-Purpose vs. Automated Job vs. SQL Warehouses",
            "filename": "003_cluster_types_and_workload_isolation_all_purpose_vs_automated_job_vs_sql_warehouses.py",
            "difficulty": "Foundational",
            "business_scenario": "An enterprise FinOps audit revealed that data engineering teams are running scheduled nightly batch ETL jobs on interactive All-Purpose clusters, causing a 2.5x cost inflation.",
            "problem_statement": "Implement automated checks and cluster configuration generators that enforce the correct compute type (Job Compute vs. All-Purpose vs. Serverless SQL) based on workload semantics.",
            "architectural_notes": "All-Purpose compute is priced higher for developer interactivity. Job compute runs automated ephemeral clusters that terminate immediately on job completion. SQL Warehouses feature Photon C++ engines and Intelligent Workload Management for BI.",
            "sections": [
                {
                    "title": "1. Compute Type Cost & Allocation Decision Matrix",
                    "explanation": "Evaluate workload attributes and return optimal cluster configuration specifications.",
                    "code": """def recommend_compute(workload_type: str, is_scheduled: bool, concurrency: int) -> dict:
    if is_scheduled and workload_type == "ETL":
        return {
            "type": "JOB_COMPUTE",
            "dbu_multiplier": 1.0,
            "lifecycle": "ephemeral",
            "photon": True,
            "description": "Ephemeral Job Cluster provisioned via Lakeflow Jobs"
        }
    elif workload_type == "BI_DASHBOARD":
        return {
            "type": "SERVERLESS_SQL_WAREHOUSE",
            "dbu_multiplier": 1.5,
            "lifecycle": "serverless_autostop_10min",
            "photon": True,
            "description": "Serverless Photon SQL Warehouse with instant spinup"
        }
    else:
        return {
            "type": "ALL_PURPOSE",
            "dbu_multiplier": 2.5,
            "lifecycle": "interactive_autostop_20min",
            "photon": False,
            "description": "Shared Interactive Cluster for exploratory notebook development"
        }

rec = recommend_compute("ETL", is_scheduled=True, concurrency=1)
assert rec["type"] == "JOB_COMPUTE", "Scheduled batch jobs must use Job Compute!"
print(f"Recommended Compute: {rec['type']} | Cost Factor: {rec['dbu_multiplier']}x")
"""
                }
            ],
            "key_takeaways": [
                "Job Compute Rule: Never schedule production workflows on All-Purpose clusters.",
                "Serverless SQL: Use for high-concurrency BI dashboards (Tableau, Power BI, Lakeview).",
                "Ephemeral Lifecycle: Job clusters spin up on task start and terminate on completion, preventing idle spend."
            ],
            "interview_questions": [
                "Why is Job Compute significantly cheaper than All-Purpose Compute?",
                "When should you choose a Serverless SQL Warehouse over an All-Purpose cluster for query workloads?"
            ]
        },
        {
            "nb_id": "004",
            "title": "Cluster Policies, T-Shirt Sizing & Fleet Autoscaling Mechanics",
            "filename": "004_cluster_policies_t_shirt_sizing_and_fleet_autoscaling_mechanics.py",
            "difficulty": "Intermediate",
            "business_scenario": "Developers frequently spin up oversized 64-core clusters for simple data exploration, wasting tens of thousands in cloud spend each month.",
            "problem_statement": "Define, validate, and enforce a Databricks Cluster Policy JSON specification that mandates T-shirt sizing (Small, Medium, Large), limits maximum worker nodes, and forces aggressive 15-minute auto-termination.",
            "architectural_notes": "Cluster policies enforce guardrails on cluster creation. They restrict allowable VM node types, mandate autoscale limits (`max_workers`), enforce tags (`CostCenter`, `Owner`), and lock idle auto-stop timeouts.",
            "sections": [
                {
                    "title": "1. Construct Production Cluster Policy Definition",
                    "explanation": "Create an immutable JSON policy definition restricting developers to cost-effective instances with auto-stop.",
                    "code": """import json

cluster_policy = {
    "autotermination_minutes": {
        "type": "range",
        "maxValue": 20,
        "defaultValue": 15,
        "isOptional": False
    },
    "autoscale.max_workers": {
        "type": "range",
        "maxValue": 8,
        "defaultValue": 4,
        "isOptional": False
    },
    "node_type_id": {
        "type": "allowlist",
        "values": ["Standard_D4ds_v5", "Standard_D8ds_v5"],
        "defaultValue": "Standard_D4ds_v5"
    },
    "custom_tags.CostCenter": {
        "type": "fixed",
        "value": "DataEngineering",
        "isOptional": False
    }
}

# Verify policy invariants
assert cluster_policy["autotermination_minutes"]["maxValue"] <= 20
assert "Standard_D4ds_v5" in cluster_policy["node_type_id"]["values"]
print("Cluster policy specification verified.")
print(json.dumps(cluster_policy, indent=2))
"""
                }
            ],
            "key_takeaways": [
                "Policy Enforcement: Restrict node types to prevent expensive GPU/high-memory instances on dev workloads.",
                "Auto-Stop Invariant: Set interactive timeouts to 15-20 minutes maximum.",
                "Mandatory Tags: Enforce CostCenter tags directly in policy for downstream FinOps attribution."
            ],
            "interview_questions": [
                "How do cluster policies prevent rogue cloud infrastructure spending in Databricks?",
                "Can a cluster policy override user-specified Spark configuration settings?"
            ]
        },
        {
            "nb_id": "005",
            "title": "Databricks CLI v0.200+ Automation, Authentication & OAuth M2M Profiles",
            "filename": "005_databricks_cli_v0_200_automation_authentication_and_oauth_m2m_profiles.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise DevOps team is replacing deprecated legacy Python CLI tools with the modern Go-based Databricks CLI v0.200+ across all Jenkins and GitHub Actions runners using OAuth Machine-to-Machine (M2M) authentication.",
            "problem_statement": "Demonstrate the programmatic setup of Databricks CLI authentication profiles, token generation, and command execution using Service Principal client credentials.",
            "architectural_notes": "Databricks CLI v0.200+ is rewritten in Go for high performance. It standardizes on OAuth M2M tokens generated from Azure Service Principals or AWS OIDC roles, eliminating insecure static personal access tokens (PATs).",
            "sections": [
                {
                    "title": "1. Configure OAuth M2M Profile Specification",
                    "explanation": "Define the `.databrickscfg` configuration block for zero-trust service principal execution.",
                    "code": """# Simulate databrickscfg profile structure
databrickscfg_template = \"\"\"
[DEFAULT]
host = https://adb-1234567890123456.7.azuredatabricks.net
auth_type = oauth-m2m
client_id = 4f63c679-0db8-40a2-b91a-7b3b7e7136f4
client_secret = {{secrets/sp_tokens/client_secret}}

[PROD_ACCOUNT]
host = https://accounts.azuredatabricks.net
account_id = a1b2c3d4-e5f6-7890-abcd-ef1234567890
auth_type = oauth-m2m
client_id = 4f63c679-0db8-40a2-b91a-7b3b7e7136f4
client_secret = {{secrets/sp_tokens/client_secret}}
\"\"\"

print("OAuth M2M profile specification configured.")
assert "auth_type = oauth-m2m" in databrickscfg_template
"""
                }
            ],
            "key_takeaways": [
                "Modern CLI Baseline: Use Go-based CLI v0.200+; legacy pip databricks-cli is deprecated.",
                "OAuth M2M Standard: Service Principals use short-lived OAuth tokens instead of static PATs.",
                "Account vs. Workspace: Separate CLI profiles for account-level operations (metastore, SCIM) and workspace operations."
            ],
            "interview_questions": [
                "Why are Personal Access Tokens (PATs) prohibited in enterprise production CI/CD?",
                "How does OAuth M2M authentication work between GitHub Actions and Databricks?"
            ]
        },
        {
            "nb_id": "006",
            "title": "Databricks REST API 2.1 Programmatic Workspace & Compute Lifecycle Management",
            "filename": "006_databricks_rest_api_2_1_programmatic_workspace_and_compute_lifecycle_management.py",
            "difficulty": "Intermediate",
            "business_scenario": "A platform engineering team requires an automated REST API daemon that audits all running clusters, restarts stalled worker nodes, and purges empty workspace directories.",
            "problem_statement": "Develop modular Python client code interacting with Databricks REST API 2.1 endpoints (`/api/2.1/clusters/list`, `/api/2.1/jobs/runs/cancel`, `/api/2.0/workspace/list`) with retry backoff and error handling.",
            "architectural_notes": "The REST API 2.1 exposes granular control plane endpoints. The official Databricks SDK for Python (`databricks-sdk`) wraps these endpoints with type safety and automatic pagination.",
            "sections": [
                {
                    "title": "1. Programmatic Cluster Auditing with REST API Payload Simulation",
                    "explanation": "Query cluster endpoints and inspect state transitions (RUNNING, TERMINATED, RESIZING).",
                    "code": """import datetime

# Mock cluster response payload matching REST API 2.1
mock_api_clusters = {
    "clusters": [
        {"cluster_id": "0101-120000-abc123", "cluster_name": "prod-etl-01", "state": "RUNNING", "num_workers": 4},
        {"cluster_id": "0101-120001-xyz789", "cluster_name": "adhoc-analyst", "state": "TERMINATED", "num_workers": 0},
        {"cluster_id": "0101-120002-def456", "cluster_name": "zombie-dev", "state": "RUNNING", "num_workers": 8}
    ]
}

# Filter running clusters
running = [c for c in mock_api_clusters["clusters"] if c["state"] == "RUNNING"]
total_active_workers = sum(c["num_workers"] for c in running)

print(f"Active Running Clusters: {len(running)}")
print(f"Total Dedicated Workers: {total_active_workers}")
assert len(running) == 2, "Expected 2 active running clusters!"
"""
                }
            ],
            "key_takeaways": [
                "API Versioning: Use REST API 2.1 for Unity Catalog and modern workspace operations.",
                "Databricks SDK: Prefer `WorkspaceClient` from `databricks-sdk` over raw `requests` calls for built-in retries.",
                "Rate Limiting: Handle HTTP 429 Too Many Requests with exponential jitter backoff."
            ],
            "interview_questions": [
                "How do you handle API rate limits (HTTP 429) when polling Databricks job run statuses?",
                "What is the difference between `/api/2.0/jobs` and `/api/2.1/jobs`?"
            ]
        },
        {
            "nb_id": "007",
            "title": "Databricks Secrets & Cloud KMS Scopes: dbutils.secrets & Zero-Trust Ingestion",
            "filename": "007_databricks_secrets_and_cloud_kms_scopes_dbutils_secrets_and_zero_trust_ingestion.py",
            "difficulty": "Intermediate",
            "business_scenario": "A payment processing pipeline must authenticate to third-party merchant APIs and external databases without leaking API keys, passwords, or connection strings in code or execution logs.",
            "problem_statement": "Demonstrate the creation and consumption of Databricks Secret Scopes backed by Azure Key Vault / AWS KMS, and prove that `dbutils.secrets.get()` automatically redacts values in stdout.",
            "architectural_notes": "Databricks Secret Scopes store encrypted key-value pairs. They can be Databricks-backed (encrypted in Control Plane) or Cloud-KMS-backed (Azure Key Vault / AWS Secrets Manager). The Spark engine automatically intercepts secret strings and replaces them with `[REDACTED]` in notebook logs.",
            "sections": [
                {
                    "title": "1. Secure Credential Retrieval & Output Masking",
                    "explanation": "Retrieve simulated credentials and verify redaction behavior in execution outputs.",
                    "code": """# Simulate dbutils.secrets module locally
class MockSecrets:
    def __init__(self):
        self._vault = {
            ("payment_gateway", "api_key"): "sk_live_998877665544332211",
            ("payment_gateway", "client_secret"): "super_secret_pci_token"
        }
    def get(self, scope: str, key: str) -> str:
        return self._vault.get((scope, key), "")

mock_secrets = MockSecrets()
retrieved_key = mock_secrets.get("payment_gateway", "api_key")

# Verification: Secret is accessible in code but should never be printed raw
assert len(retrieved_key) > 0
print(f"Retrieved Secret Key Length: {len(retrieved_key)}")
print("Masked in production logs: [REDACTED]")
"""
                }
            ],
            "key_takeaways": [
                "Zero Hardcoded Credentials: Never embed passwords, tokens, or connection strings in notebooks or git.",
                "Cloud KMS Backing: Back secret scopes directly with Azure Key Vault or AWS Secrets Manager for central rotation.",
                "Log Masking: Databricks automatically redacts values retrieved via `dbutils.secrets.get()` in driver outputs."
            ],
            "interview_questions": [
                "How does Databricks prevent secrets from being printed in notebook outputs?",
                "What is the difference between an Azure Key Vault-backed secret scope and a Databricks-backed secret scope?"
            ]
        },
        {
            "nb_id": "008",
            "title": "Workspace Filesystem (/Workspace) vs. Volumes (/Volumes) vs. Legacy DBFS Mounts",
            "filename": "008_workspace_filesystem_vs_volumes_vs_legacy_dbfs_mounts.py",
            "difficulty": "Intermediate",
            "business_scenario": "A lakehouse migration project must eliminate legacy DBFS mounts (`/mnt/raw_data`) and transition all data pipelines to Unity Catalog Volumes (`/Volumes`) and Workspace Files (`/Workspace`).",
            "problem_statement": "Provide a complete migration mapping and operational script comparing file access semantics across `/Workspace`, `/Volumes`, and DBFS root.",
            "architectural_notes": "Legacy DBFS mounts (`/mnt/`) expose security holes because all users on a shared cluster share the mount's credentials. Unity Catalog Volumes (`/Volumes/catalog/schema/volume`) enforce fine-grained governance for unstructured and semi-structured files. `/Workspace` stores code, repos, and lightweight configs.",
            "sections": [
                {
                    "title": "1. Path Resolution & Storage Routing Matrix",
                    "explanation": "Map file path semantics to their underlying storage boundaries.",
                    "code": """storage_mapping = {
    "/Workspace/Users/user@company.com/project/config.json": {
        "tier": "Workspace Filesystem",
        "purpose": "Source code, repo files, small JSON configs (< 500 MB)",
        "governed_by": "Workspace Access Control Lists (ACLs)"
    },
    "/Volumes/prod_lakehouse/raw_landing/invoices/2026_01.pdf": {
        "tier": "Unity Catalog Volume",
        "purpose": "Unstructured enterprise files (PDFs, images, CSVs, audio)",
        "governed_by": "Unity Catalog Grants (READ/WRITE VOLUME)"
    },
    "/mnt/legacy_adls/orders/": {
        "tier": "Legacy DBFS Mount",
        "purpose": "DEPRECATED: Security risk; bypasses Unity Catalog governance",
        "governed_by": "Static mount tokens / SPN"
    }
}

for path, meta in storage_mapping.items():
    print(f"Path: {path}\\n  -> Tier: {meta['tier']}\\n  -> Governance: {meta['governed_by']}\\n")

assert "DEPRECATED" in storage_mapping["/mnt/legacy_adls/orders/"]["purpose"]
"""
                }
            ],
            "key_takeaways": [
                "Deprecate `/mnt/`: Legacy mounts lack Unity Catalog audit trails and fine-grained access control.",
                "Use `/Volumes/`: For raw files, PDFs, model weights, and semi-structured data.",
                "Use `/Workspace/`: For project scripts, requirements.txt, and local Python modules."
            ],
            "interview_questions": [
                "Why are DBFS root mounts (`/mnt/`) deprecated in modern Databricks environments?",
                "How do POSIX file operations (`open()`, `os.listdir()`) work on Unity Catalog Volumes?"
            ]
        },
        {
            "nb_id": "009",
            "title": "Service Principals, SCIM Provisioning & Enterprise Identity Federation",
            "filename": "009_service_principals_scim_provisioning_and_enterprise_identity_federation.py",
            "difficulty": "Intermediate",
            "business_scenario": "An enterprise identity architect must automate user provisioning from Microsoft Entra ID (Azure AD) and Okta into Databricks using SCIM (System for Cross-domain Identity Management).",
            "problem_statement": "Define the identity architecture, group mapping model, and Service Principal assignment rules for automated enterprise identity lifecycle management.",
            "architectural_notes": "Account-level SCIM synchronizes enterprise users and groups from the Identity Provider (IdP) to the Databricks Account Console. Groups are then assigned to specific workspaces, preventing manual user administration in individual workspaces.",
            "sections": [
                {
                    "title": "1. SCIM Group-to-Workspace Synchronization Model",
                    "explanation": "Simulate identity mapping from Okta/Entra ID to Databricks Account and Workspaces.",
                    "code": """# Identity mapping schema
idp_groups = [
    {"group_name": "data_engineers", "members": 45, "workspaces": ["dev", "staging", "prod"]},
    {"group_name": "bi_analysts", "members": 120, "workspaces": ["staging", "prod"]},
    {"group_name": "data_scientists", "members": 30, "workspaces": ["dev", "staging"]}
]

# Service Principal specification for CI/CD
cicd_sp = {
    "display_name": "sp-github-actions-prod",
    "application_id": "4f63c679-0db8-40a2-b91a-7b3b7e7136f4",
    "roles": ["account_admin", "workspace_admin"],
    "token_type": "OAuth M2M"
}

print(f"Service Principal: {cicd_sp['display_name']} ({cicd_sp['application_id']})")
assert cicd_sp["token_type"] == "OAuth M2M"
"""
                }
            ],
            "key_takeaways": [
                "Account-Level SCIM: Provision users and groups centrally at the account level, not per workspace.",
                "Service Principals for Automation: Never run production CI/CD or jobs under human user accounts.",
                "Group-Based Access: Always grant catalog permissions to SCIM groups, never individual users."
            ],
            "interview_questions": [
                "How does SCIM integration streamline user onboarding and offboarding in Databricks?",
                "What happens to a scheduled production job if its owner leaves the company and their Entra ID account is disabled?"
            ]
        },
        {
            "nb_id": "010",
            "title": "Workspace Audit Logging & Security Event Ingestion via Diagnostic Settings",
            "filename": "010_workspace_audit_logging_and_security_event_ingestion_via_diagnostic_settings.py",
            "difficulty": "Advanced",
            "business_scenario": "A cyber-security operations center (SOC) requires real-time alerting on unauthorized notebook exports, permissions escalation, and unexpected secret reads across all Databricks workspaces.",
            "problem_statement": "Develop a PySpark pipeline ingesting raw cloud diagnostic audit logs (Azure Monitor / AWS CloudWatch) into a Delta Lake security audit table with automated intrusion detection rules.",
            "architectural_notes": "Databricks generates comprehensive JSON audit logs for every workspace action (notebook commands, login attempts, secret reads, cluster changes). These stream to cloud storage and can be queried directly via `system.access.audit` or custom Bronze audit tables.",
            "sections": [
                {
                    "title": "1. Ingest & Parse Diagnostic Security Audit Logs",
                    "explanation": "Parse raw audit JSON records and flag suspicious privilege escalations.",
                    "code": """raw_audit_records = [
    {"timestamp": "2026-11-17T10:00:00Z", "action": "login", "user": "alice@company.com", "status": "SUCCESS", "ip": "10.0.1.5"},
    {"timestamp": "2026-11-17T10:05:00Z", "action": "secrets.getSecret", "user": "alice@company.com", "status": "SUCCESS", "ip": "10.0.1.5"},
    {"timestamp": "2026-11-17T10:12:00Z", "action": "grantPermissions", "user": "contractor@vendor.com", "status": "FAILURE", "ip": "198.51.100.44"},
    {"timestamp": "2026-11-17T10:13:00Z", "action": "notebook.export", "user": "contractor@vendor.com", "status": "SUCCESS", "ip": "198.51.100.44"}
]

df_audit = spark.createDataFrame(raw_audit_records)
df_suspicious = df_audit.filter((F.col("action") == "notebook.export") | (F.col("status") == "FAILURE"))
print("Security Alerts Flagged:")
df_suspicious.show(truncate=False)

assert df_suspicious.count() == 2, "Expected 2 flagged security events!"
"""
                }
            ],
            "key_takeaways": [
                "Diagnostic Settings: Stream workspace logs to Azure Log Analytics, S3, or GCS.",
                "System Audit Tables: Query `system.access.audit` for unified, zero-ETL access to account-level security events.",
                "Automated Intrusion Detection: Set up hourly SQL alerts on critical actions like `grantPermissions` and `notebook.export`."
            ],
            "interview_questions": [
                "What events are captured in Databricks audit logs?",
                "How can you detect data exfiltration attempts using Databricks audit telemetry?"
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
