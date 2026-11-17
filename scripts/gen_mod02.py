"""
Module 02: Unity Catalog — Governance, Security & Federation (Notebooks 011 - 021)
"""

from pathlib import Path
from notebook_builder import build_notebook, write_notebook

MODULE_FOLDER = "02_unity_catalog_and_governance"
MODULE_NAME = "Module 02: Unity Catalog — Governance, Security & Federation"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "011",
            "title": "Unity Catalog 3-Level Namespace: Catalogs, Schemas, Tables & Volumes Architecture",
            "filename": "011_unity_catalog_3_level_namespace_catalogs_schemas_tables_and_volumes_architecture.py",
            "difficulty": "Foundational",
            "business_scenario": "A legacy Databricks deployment using the 2-level Hive metastore (`default.table_name`) is undergoing migration to Unity Catalog. Enterprise data must be organized into logical business domains with dedicated dev, test, and prod catalogs.",
            "problem_statement": "Define and deploy the 3-level namespace hierarchy (`catalog.schema.table_or_volume`) using SQL DDL, verify namespace resolution, and assert catalog permissions.",
            "architectural_notes": "Unity Catalog introduces a 3-tier namespace: Catalog (logical container or environment) -> Schema (database or domain) -> Table/View/Volume/Model (physical or virtual asset). It eliminates table collisions and provides cross-workspace data access from a central metastore.",
            "sections": [
                {
                    "title": "1. Deploy 3-Level Namespace DDL Structure",
                    "explanation": "Create catalogs and schemas with explicit comments and properties.",
                    "code": """# Simulate 3-level namespace metadata verification
catalog_structure = {
    "prod_lakehouse": {
        "bronze": ["orders_raw", "events_stream", "raw_files_volume"],
        "silver": ["orders_cleaned", "customers_conformed"],
        "gold": ["fact_sales", "dim_customer_360"]
    }
}

# Verify 3-level addressing path
full_table_path = "prod_lakehouse.gold.fact_sales"
parts = full_table_path.split(".")
assert len(parts) == 3, f"Expected 3 parts in UC namespace, got {parts}"
catalog, schema, table = parts
print(f"Catalog: {catalog} | Schema: {schema} | Table: {table}")
"""
                }
            ],
            "key_takeaways": [
                "3-Level Standard: Always use `catalog.schema.table` in production code.",
                "Metastore Scope: One metastore per cloud region binds across multiple workspaces.",
                "Namespace Resolution: Set session context via `USE CATALOG` and `USE SCHEMA` for interactive convenience."
            ],
            "interview_questions": [
                "How does Unity Catalog's 3-level namespace improve multi-tenant data governance over the legacy Hive metastore?",
                "Can a table in Catalog A join a table in Catalog B in a single query?"
            ]
        },
        {
            "nb_id": "012",
            "title": "Managed Tables vs. External Tables: Storage Credentials & External Locations",
            "filename": "012_managed_tables_vs_external_tables_storage_credentials_and_external_locations.py",
            "difficulty": "Intermediate",
            "business_scenario": "A data architecture team must decide which enterprise datasets should be Managed Tables in Unity Catalog vs. External Tables pointing to existing cloud data lake locations.",
            "problem_statement": "Implement and compare Managed and External table creation, verify underlying cloud storage paths, and demonstrate table drop lifecycle differences.",
            "architectural_notes": "Managed tables have their file lifecycle controlled by Unity Catalog; dropping a managed table deletes both metadata and Parquet data. External tables use an External Location and Storage Credential; dropping an external table removes only catalog metadata, leaving underlying cloud files intact.",
            "sections": [
                {
                    "title": "1. Compare Managed vs. External Lifecycle & DDL",
                    "explanation": "Inspect the DDL and lifecycle behavior of Managed and External assets.",
                    "code": """table_specs = {
    "managed_table": {
        "ddl": "CREATE TABLE prod.silver.orders (id BIGINT, amount DOUBLE);",
        "storage": "Managed by UC in schema root path",
        "drop_behavior": "DELETES metadata AND underlying Parquet files from cloud storage",
        "predictive_optimization": "Fully automated serverless OPTIMIZE & VACUUM"
    },
    "external_table": {
        "ddl": "CREATE TABLE prod.silver.legacy_orders (id BIGINT, amount DOUBLE) LOCATION 'abfss://data@datalake.dfs.core.windows.net/orders';",
        "storage": "Customer-managed external cloud storage path",
        "drop_behavior": "DELETES metadata ONLY; Parquet files remain preserved in cloud storage",
        "predictive_optimization": "Manual or requires explicit storage credential enablement"
    }
}

for name, spec in table_specs.items():
    print(f"[{name.upper()}]\\n  DDL: {spec['ddl']}\\n  Drop Semantics: {spec['drop_behavior']}\\n")

assert "DELETES metadata AND underlying Parquet" in table_specs["managed_table"]["drop_behavior"]
"""
                }
            ],
            "key_takeaways": [
                "Managed Table Default: Use Managed Tables for new lakehouse assets to leverage automated Predictive Optimization.",
                "External Table Use Case: Use External Tables when existing third-party applications write directly to cloud storage.",
                "Storage Credentials: Both use cloud IAM (Managed Identity / IAM Role) without static access keys."
            ],
            "interview_questions": [
                "What happens to the physical data on cloud object storage when a user drops an External Table versus a Managed Table?",
                "How does Unity Catalog authenticate to cloud storage for External Tables?"
            ]
        },
        {
            "nb_id": "013",
            "title": "Unity Catalog Volumes: Governance for PDFs, Images, Audio & Semi-Structured Data",
            "filename": "013_unity_catalog_volumes_governance_for_pdfs_images_audio_and_semi_structured_data.py",
            "difficulty": "Intermediate",
            "business_scenario": "An insurance company processes scanned claim documents (PDFs and JPEG damage photos). Compliance requires auditing who accesses which claim file and restricting access based on adjusters' group membership.",
            "problem_statement": "Create and manage Unity Catalog Volumes (`/Volumes/catalog/schema/volume`), upload unstructured files, query file metadata with SQL, and enforce access privileges.",
            "architectural_notes": "Volumes represent governed storage objects in Unity Catalog that provide POSIX-compatible filesystem access to unstructured files, machine learning models, and raw data files. Managed Volumes reside in schema storage; External Volumes point to customer cloud buckets.",
            "sections": [
                {
                    "title": "1. Volume Creation and File Operation Simulation",
                    "explanation": "Create a volume and demonstrate reading files via standard Python file I/O.",
                    "code": """# Simulate Unity Catalog volume path resolution
volume_path = "/Volumes/prod_lakehouse/claims/raw_documents"
sample_file = f"{volume_path}/claim_1001_damage_report.pdf"

print(f"Target Volume Path: {volume_path}")
print(f"Sample POSIX File Access: {sample_file}")

# Standard Python POSIX path compatibility test
assert sample_file.startswith("/Volumes/"), "Volume path must conform to /Volumes/<catalog>/<schema>/<volume>"
"""
                }
            ],
            "key_takeaways": [
                "POSIX Compatibility: Volumes can be read using standard Python libraries (`open()`, `PIL`, `pypdf`, `torch`).",
                "Fine-Grained Auditing: Every file read or write via Volumes is recorded in `system.access.audit`.",
                "Governance Standard: Volumes replace legacy DBFS mounts for unstructured data."
            ],
            "interview_questions": [
                "How do Unity Catalog Volumes differ from traditional relational tables in Databricks?",
                "Can machine learning libraries like PyTorch or HuggingFace load model checkpoints directly from Volumes?"
            ]
        },
        {
            "nb_id": "014",
            "title": "Fine-Grained Row-Level Security (RLS) using Dynamic Row Filter Functions",
            "filename": "014_fine_grained_row_level_security_rls_using_dynamic_row_filter_functions.py",
            "difficulty": "Advanced",
            "business_scenario": "A global healthcare provider must restrict patient records so doctors can only view patients within their assigned hospital region, while compliance officers can view all records.",
            "problem_statement": "Author and attach a dynamic SQL Row Filter function to a Delta table, testing that the filter transparently prunes rows based on caller session identity.",
            "architectural_notes": "Dynamic Row Filters attach directly to physical tables in Unity Catalog. When a query executes, Catalyst injects the boolean filter function into the logical plan, executing security filtering without data duplication.",
            "sections": [
                {
                    "title": "1. Define & Attach Dynamic Row Filter Function",
                    "explanation": "Write the SQL DDL for dynamic row filtering using `IS_ACCOUNT_GROUP_MEMBER()`.",
                    "code": """# Simulate row filter logic in PySpark
def evaluate_row_access(user_groups: list, row_region: str) -> bool:
    if "compliance_admins" in user_groups:
        return True
    if "emea_doctors" in user_groups and row_region == "EMEA":
        return True
    if "us_doctors" in user_groups and row_region == "US":
        return True
    return False

# Test scenarios
assert evaluate_row_access(["compliance_admins"], "EMEA") is True
assert evaluate_row_access(["us_doctors"], "EMEA") is False
assert evaluate_row_access(["us_doctors"], "US") is True
print("Dynamic Row Filter evaluation validated across all user personas.")
"""
                }
            ],
            "key_takeaways": [
                "Zero Data Duplication: A single physical table serves all user tiers safely.",
                "Optimizer Integration: Catalyst pushes row filter predicates down into storage scans for maximum performance.",
                "Metastore Administration: Only table owners or metastore admins can attach or remove row filters."
            ],
            "interview_questions": [
                "How do Dynamic Row Filters differ from creating separate secure views for each region?",
                "What built-in Unity Catalog functions are used to inspect the current user's session in row filter functions?"
            ]
        },
        {
            "nb_id": "015",
            "title": "Dynamic Column Masking for PII Protection and Compliance",
            "filename": "015_dynamic_column_masking_for_pii_protection_and_compliance.py",
            "difficulty": "Advanced",
            "business_scenario": "A retail bank must protect customer Personally Identifiable Information (PII) such as Social Security Numbers (SSN) and credit card numbers. Non-privileged analysts should see only the last four digits.",
            "problem_statement": "Define a dynamic column masking function in SQL, bind it to a table column, and verify that non-privileged queries receive redacted values while authorized payroll managers see plaintext.",
            "architectural_notes": "Dynamic Column Masking functions evaluate at query runtime. Non-privileged users receive masked strings (e.g., `XXX-XX-1234` or cryptographic hashes), while privileged roles see the original raw values.",
            "sections": [
                {
                    "title": "1. Implement Dynamic Column Masking Function",
                    "explanation": "Create masking logic redacting sensitive strings based on caller privileges.",
                    "code": """def mask_national_id(raw_id: str, is_privileged: bool) -> str:
    if is_privileged:
        return raw_id
    if not raw_id or len(raw_id) < 4:
        return "REDACTED"
    return f"XXX-XX-{raw_id[-4:]}"

# Test masking logic
raw_ssn = "123-45-6789"
assert mask_national_id(raw_ssn, is_privileged=True) == "123-45-6789"
assert mask_national_id(raw_ssn, is_privileged=False) == "XXX-XX-6789"
print(f"Privileged View: {mask_national_id(raw_ssn, True)}")
print(f"Masked Analyst View: {mask_national_id(raw_ssn, False)}")
"""
                }
            ],
            "key_takeaways": [
                "In-Place Protection: Column masking protects data in-place without altering the underlying Parquet files.",
                "Role Redaction: Combine with `IS_ACCOUNT_GROUP_MEMBER()` for fine-grained role-based unmasking.",
                "Compliance Ready: Satisfies GDPR, HIPAA, and CCPA data privacy and pseudonymization standards."
            ],
            "interview_questions": [
                "Can a dynamic column mask be applied to non-string columns (e.g., decimal salaries or date of birth)?",
                "What happens if an unauthorized user attempts to filter on a masked column (`WHERE ssn = '123-45-6789'`)?"
            ]
        },
        {
            "nb_id": "016",
            "title": "Lakehouse Federation: Querying PostgreSQL, MySQL, and SQL Server without ETL",
            "filename": "016_lakehouse_federation_querying_postgresql_mysql_and_sql_server_without_etl.py",
            "difficulty": "Intermediate",
            "business_scenario": "A retail company needs to join real-time inventory stored in an on-premises PostgreSQL database with historical sales stored in Delta Lake without building slow and fragile ETL pipelines.",
            "problem_statement": "Configure a Unity Catalog Foreign Connection and Foreign Catalog pointing to a relational database, and demonstrate query federation with predicate pushdown.",
            "architectural_notes": "Lakehouse Federation creates a foreign catalog mapped to an external relational database. Unity Catalog translates ANSI SQL queries and pushes filters (`WHERE`), projections (`SELECT`), and aggregations down to the remote database engine.",
            "sections": [
                {
                    "title": "1. Foreign Catalog Architecture & Pushdown Simulation",
                    "explanation": "Verify how Catalyst translates federated joins and pushes predicates to external databases.",
                    "code": """# Simulate query plan pushdown inspection
query_plan_info = {
    "source_query": "SELECT o.order_id, p.inventory_count FROM delta_sales o JOIN pg_catalog.inventory p ON o.sku = p.sku WHERE p.warehouse = 'US-EAST'",
    "pushed_to_remote_postgres": "SELECT sku, inventory_count FROM inventory WHERE warehouse = 'US-EAST'",
    "executed_in_spark": "HashJoin on sku between Delta Scan and Postgres Result Stream"
}

print("Original Federated SQL:")
print(f"  {query_plan_info['source_query']}")
print("\\nPushed Predicate to PostgreSQL:")
print(f"  {query_plan_info['pushed_to_remote_postgres']}")
assert "WHERE warehouse = 'US-EAST'" in query_plan_info["pushed_to_remote_postgres"]
"""
                }
            ],
            "key_takeaways": [
                "Zero ETL: Query external transactional databases immediately through the 3-level namespace.",
                "Predicate Pushdown: Catalyst pushes filters down to the source database to avoid transferring raw table dumps.",
                "Unified Permissions: Manage access to remote tables using standard Unity Catalog `GRANT` commands."
            ],
            "interview_questions": [
                "How does Lakehouse Federation differ from classic JDBC Spark connections?",
                "What query operations can and cannot be pushed down to a remote database in Lakehouse Federation?"
            ]
        },
        {
            "nb_id": "017",
            "title": "Lakehouse Federation: Querying Snowflake and Google BigQuery via Unity Catalog",
            "filename": "017_lakehouse_federation_querying_snowflake_and_google_bigquery_via_unity_catalog.py",
            "difficulty": "Advanced",
            "business_scenario": "Following an enterprise acquisition, the analytics team must query financial ledgers in Snowflake and web telemetry in Google BigQuery alongside the core Databricks Lakehouse.",
            "problem_statement": "Deploy foreign catalogs for Snowflake and BigQuery, analyze execution plans to ensure partition pruning, and optimize federated join performance.",
            "architectural_notes": "Unity Catalog supports native connectors for cloud data warehouses (Snowflake, BigQuery, Redshift, Synapse). It leverages cloud IAM and OAuth for secure, credential-less cross-cloud federation.",
            "sections": [
                {
                    "title": "1. Cross-Cloud Federation Configuration Specification",
                    "explanation": "Define foreign connection parameters for Snowflake and BigQuery.",
                    "code": """federated_connections = {
    "snowflake_prod": {
        "type": "SNOWFLAKE",
        "options": {"host": "xy12345.snowflakecomputing.com", "warehouse": "ANALYTICS_WH"},
        "auth": "OAuth / Key-Pair"
    },
    "bigquery_analytics": {
        "type": "BIGQUERY",
        "options": {"projectId": "enterprise-data-warehouse-prod"},
        "auth": "Google Service Account via Unity Catalog Storage Credential"
    }
}

for conn_name, cfg in federated_connections.items():
    print(f"Connection: {conn_name} | Type: {cfg['type']} | Auth: {cfg['auth']}")
assert len(federated_connections) == 2
"""
                }
            ],
            "key_takeaways": [
                "Multi-Warehouse Unification: Query Snowflake, BigQuery, and Databricks in a single unified SQL statement.",
                "Egress Cost Awareness: Be cautious of cross-cloud data transfer egress fees when joining massive tables.",
                "Governance Centralization: Control who can access Snowflake tables via Databricks Unity Catalog permissions."
            ],
            "interview_questions": [
                "What are the network latency and egress cost trade-offs when executing cross-cloud queries via Lakehouse Federation?",
                "How does Unity Catalog handle schema changes in remote Snowflake or BigQuery tables?"
            ]
        },
        {
            "nb_id": "018",
            "title": "Delta Sharing: Zero-Copy Open Protocol Data Sharing with External Consumers",
            "filename": "018_delta_sharing_zero_copy_open_protocol_data_sharing_with_external_consumers.py",
            "difficulty": "Intermediate",
            "business_scenario": "A financial data vendor sells daily market pricing feeds to external hedge funds and academic institutions that do not use Databricks. Data must be shared securely without copying or FTP exports.",
            "problem_statement": "Configure an open Delta Sharing Share, create recipient profiles, generate secure credential activation tokens, and read shared tables using Python and Pandas.",
            "architectural_notes": "Delta Sharing is the industry's first open source protocol for secure, real-time data exchange across platforms. External recipients query data directly using Python, Pandas, Power BI, Apache Spark, or DuckDB without running Databricks compute.",
            "sections": [
                {
                    "title": "1. Delta Sharing Protocol Flow & Token Activation",
                    "explanation": "Model the recipient credential activation and secure file URL generation flow.",
                    "code": """# Simulate Delta Sharing protocol metadata
share_spec = {
    "share_name": "market_daily_pricing_share",
    "tables": ["prod_catalog.gold.eod_stock_prices"],
    "recipient_name": "hedge_fund_alpha",
    "token_expiration": "2027-01-01T00:00:00Z"
}

print(f"Share: {share_spec['share_name']}")
print(f"Recipient: {share_spec['recipient_name']}")
print(f"Shared Tables: {share_spec['tables']}")
assert len(share_spec["tables"]) == 1
"""
                }
            ],
            "key_takeaways": [
                "Open Protocol: Recipients can use Python, DuckDB, Power BI, or Excel without a Databricks account.",
                "Zero Data Copying: Data remains in the provider's cloud storage; recipients receive pre-signed short-lived URLs.",
                "Audited Access: Every external query is logged with recipient ID and IP address."
            ],
            "interview_questions": [
                "How does Delta Sharing differ from cloud-specific data sharing solutions like Snowflake Data Sharing?",
                "How does the Delta Sharing protocol ensure security when returning cloud storage pre-signed URLs to recipients?"
            ]
        },
        {
            "nb_id": "019",
            "title": "Delta Sharing Databricks-to-Databricks: Managed Cross-Account Data Virtualization",
            "filename": "019_delta_sharing_databricks_to_databricks_managed_cross_account_data_virtualization.py",
            "difficulty": "Advanced",
            "business_scenario": "A global conglomerate operates independent Databricks accounts for subsidiaries in Europe and North America. They need to share supplier and inventory tables with zero credential management.",
            "problem_statement": "Establish a Databricks-to-Databricks managed sharing topology using metastore sharing identifiers, creating provider and recipient catalogs without bearer token files.",
            "architectural_notes": "When both provider and recipient use Databricks with Unity Catalog, Delta Sharing is fully managed. The provider shares data directly using the recipient's global metastore ID (`cloud:region:metastore-id`), completely eliminating manual credential files and token rotation.",
            "sections": [
                {
                    "title": "1. Managed Databricks-to-Databricks Sharing Architecture",
                    "explanation": "Verify metastore sharing identifiers and cross-account catalog binding.",
                    "code": """metastore_id = "azure:eastus2:99a8b7c6-1234-5678-abcd-ef0123456789"
recipient_spec = {
    "name": "emea_subsidiary",
    "sharing_type": "DATABRICKS_TO_DATABRICKS",
    "metastore_id": metastore_id,
    "automatic_lineage": True
}

print(f"Recipient Metastore ID: {recipient_spec['metastore_id']}")
assert recipient_spec["sharing_type"] == "DATABRICKS_TO_DATABRICKS"
assert recipient_spec["automatic_lineage"] is True
"""
                }
            ],
            "key_takeaways": [
                "Token-Less Security: No manual credential JSON files to manage or rotate.",
                "Unified Lineage: Lineage tracks seamlessly across provider and recipient workspaces.",
                "Multi-Cloud Sharing: Shares data across Azure, AWS, and GCP transparently."
            ],
            "interview_questions": [
                "What is the difference between Open Delta Sharing and Databricks-to-Databricks Delta Sharing?",
                "How is data lineage maintained across two separate Databricks accounts in managed Delta Sharing?"
            ]
        },
        {
            "nb_id": "020",
            "title": "Attribute-Based Access Control (ABAC) & Automated PII Tagging via Information Schema",
            "filename": "020_attribute_based_access_control_abac_and_automated_pii_tagging_via_information_schema.py",
            "difficulty": "Advanced",
            "business_scenario": "A compliance team must enforce data policies across 5,000 tables. Managing table grants manually is impossible; policies must automatically apply based on metadata tags like `classification:pii`.",
            "problem_statement": "Deploy Attribute-Based Access Control (ABAC) in Unity Catalog, tag columns automatically using Python and Information Schema queries, and enforce tag-based column masking.",
            "architectural_notes": "ABAC evaluates access based on user attributes, asset tags, and environment context rather than hardcoded role grants. Unity Catalog allows binding masking policies directly to tags (`TAG classification = 'pii'`).",
            "sections": [
                {
                    "title": "1. Automated PII Tagging via Information Schema Discovery",
                    "explanation": "Identify columns matching sensitive patterns and apply governance tags programmatically.",
                    "code": """# Simulate discovering columns that require PII classification
columns_to_audit = [
    {"table": "customers", "column": "email_address", "type": "STRING"},
    {"table": "customers", "column": "home_phone", "type": "STRING"},
    {"table": "orders", "column": "order_total", "type": "DECIMAL"}
]

pii_keywords = ["email", "phone", "ssn", "national_id", "credit_card"]
tagged_columns = []

for col in columns_to_audit:
    is_pii = any(k in col["column"].lower() for k in pii_keywords)
    tag = "classification=pii" if is_pii else "classification=internal"
    tagged_columns.append({**col, "tag": tag})

print("Automated Governance Tagging Results:")
for t in tagged_columns:
    print(f"  {t['table']}.{t['column']} -> {t['tag']}")

assert tagged_columns[0]["tag"] == "classification=pii"
assert tagged_columns[2]["tag"] == "classification=internal"
"""
                }
            ],
            "key_takeaways": [
                "Scalable Governance: Manage policies across thousands of tables using metadata tags instead of individual table grants.",
                "Tag-Based Masking: Bind a dynamic column mask once to a tag; every tagged column across all catalogs is masked automatically.",
                "Information Schema: Automate compliance scanning via `system.information_schema`."
            ],
            "interview_questions": [
                "How does Attribute-Based Access Control (ABAC) differ from Role-Based Access Control (RBAC)?",
                "How can you automatically discover and tag PII columns across an entire catalog in Unity Catalog?"
            ]
        },
        {
            "nb_id": "021",
            "title": "Clean Rooms: Privacy-Preserving Collaborative Analytics Across Enterprise Boundaries",
            "filename": "021_clean_rooms_privacy_preserving_collaborative_analytics_across_enterprise_boundaries.py",
            "difficulty": "Architect",
            "business_scenario": "A credit card network and an airline partner want to measure cross-brand customer advertising conversion without sharing raw card numbers, passenger names, or personal identities.",
            "problem_statement": "Design and configure a Databricks Clean Room specification that enforces differential privacy, aggregation thresholds, and query restrictions across collaborative parties.",
            "architectural_notes": "Databricks Clean Rooms provide a secure environment where two or more parties share and analyze data without exposing raw underlying records. Participants write queries that can return only approved aggregations.",
            "sections": [
                {
                    "title": "1. Clean Room Specification & Query Governance",
                    "explanation": "Define clean room privacy constraints and approved query templates.",
                    "code": """clean_room_contract = {
    "name": "airline_credit_card_conversion",
    "participants": ["airline_corp", "bank_network"],
    "privacy_rules": {
        "allow_raw_row_export": False,
        "minimum_aggregation_threshold": 100, # Differential privacy threshold
        "disallow_user_identifiers": True
    },
    "approved_query_patterns": [
        "SELECT campaign_id, COUNT(DISTINCT customer_hash) AS conversions, SUM(spend_bucket) FROM joined_data GROUP BY campaign_id"
    ]
}

print(f"Clean Room: {clean_room_contract['name']}")
print(f"Raw Export Allowed: {clean_room_contract['privacy_rules']['allow_raw_row_export']}")
print(f"Min Aggregation Threshold: {clean_room_contract['privacy_rules']['minimum_aggregation_threshold']} rows")
assert not clean_room_contract["privacy_rules"]["allow_raw_row_export"]
"""
                }
            ],
            "key_takeaways": [
                "Zero Raw Data Sharing: Neither party can see the other party's raw records.",
                "Differential Privacy: Clean Rooms enforce noise injection and minimum group thresholds to prevent re-identification.",
                "Cloud Agnostic: Collaborators can be on different clouds (e.g., Azure Bank and AWS Airline)."
            ],
            "interview_questions": [
                "How do Databricks Clean Rooms prevent collaborative participants from reconstructing private individual records?",
                "What is the underlying technology that powers Clean Rooms in Unity Catalog?"
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
