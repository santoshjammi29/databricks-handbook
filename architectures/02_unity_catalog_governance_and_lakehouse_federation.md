# 🏛️ Architecture Deep Dive: Unity Catalog Governance & Lakehouse Federation

## 1. Executive Overview & The 3-Level Namespace

Unity Catalog (UC) provides centralized, unified governance across all data and AI assets (tables, views, volumes, ML models, dashboards, and connections) within the Databricks Lakehouse. It completely replaces workspace-scoped Hive metastores with an **account-level metastore** bound across cloud regions and workspaces.

```mermaid
flowchart TD
    Metastore["Account-Level Unity Catalog Metastore (Region: us-east-1)"]
    
    Metastore --> CatProd["Catalog: prod_lakehouse (Managed Storage: s3://prod-lakehouse/)"]
    Metastore --> CatDev["Catalog: dev_lakehouse (Managed Storage: s3://dev-lakehouse/)"]
    Metastore --> CatFed["Foreign Catalog: snowflake_dw (Federated Connection)"]
    
    CatProd --> SchSilver["Schema: silver (Cleaned Data)"]
    CatProd --> SchGold["Schema: gold (Marts & Models)"]
    
    SchSilver --> TblOrders["Table: orders (Liquid Clustered Delta Table)"]
    SchSilver --> VolLanding["Volume: raw_documents (Managed Unstructured PDF/Images)"]
    SchGold --> ViewRevenue["View: monthly_revenue (Dynamic RLS Row Filter)"]
    SchGold --> ModelProphet["Model: churn_predictor (MLflow Model)"]
```

### 📐 Visual Architectural Blueprint: Unity Catalog Unified Governance
![Unity Catalog Architecture](../assets/whiteboards/unity_catalog_architecture.webp)

---

## 2. Managed Tables vs. External Tables vs. Unity Catalog Volumes

| Asset Type | Storage Location | Drop Lifecycle Semantics | Performance & Optimizations |
| :--- | :--- | :--- | :--- |
| **Managed Table** | Default schema storage path managed by UC | Dropping table permanently deletes metadata **AND** underlying Parquet files | Full Predictive Optimization (auto-compaction, auto-VACUUM, liquid clustering) |
| **External Table** | Explicit external cloud path (`LOCATION 's3://...'`) | Dropping table removes **ONLY** metadata; underlying cloud files remain intact | User must manually orchestrate `OPTIMIZE` and `VACUUM` policies |
| **Managed Volume** | Default volume storage path managed by UC | Dropping volume purges all uploaded unstructured files | Governed file system access via `/Volumes/catalog/schema/volume` |
| **External Volume** | Explicit external cloud folder path | Dropping volume removes catalog pointer; external files remain intact | Zero-copy access to enterprise document and imagery lakes |

---

## 3. Dynamic Row-Level Security (RLS) & Column Masking

Unity Catalog enforces fine-grained data access controls declaratively using standard SQL functions without duplicating data into separate views:

### Dynamic Row Filter Pattern:
```sql
-- Define SQL function checking caller group membership
CREATE OR REPLACE FUNCTION prod_lakehouse.silver.region_row_filter(region_code STRING)
RETURNS BOOLEAN
RETURN 
  IS_ACCOUNT_GROUP_MEMBER('global_admins') OR 
  (IS_ACCOUNT_GROUP_MEMBER('emea_analysts') AND region_code = 'EMEA') OR
  (IS_ACCOUNT_GROUP_MEMBER('apac_analysts') AND region_code = 'APAC');

-- Bind the row filter to the physical table
ALTER TABLE prod_lakehouse.silver.sales_transactions
SET ROW FILTER prod_lakehouse.silver.region_row_filter ON (region);
```

### Dynamic Column Masking Pattern:
```sql
-- Define PII masking function with role-based redaction
CREATE OR REPLACE FUNCTION prod_lakehouse.silver.ssn_mask(ssn_val STRING)
RETURNS STRING
RETURN 
  CASE 
    WHEN IS_ACCOUNT_GROUP_MEMBER('hr_payroll_executives') THEN ssn_val
    ELSE CONCAT('XXX-XX-', RIGHT(ssn_val, 4))
  END;

-- Bind the column mask to the sensitive attribute
ALTER TABLE prod_lakehouse.silver.employees
ALTER COLUMN national_id SET MASK prod_lakehouse.silver.ssn_mask;
```

### 📐 Visual Architectural Blueprint: Dynamic Access & Masking Lifecycle
![Lakehouse Access & Masking Lifecycle](../assets/whiteboards/lakehouse_access_masking_lifecycle_architecture.webp)

---

## 4. Lakehouse Federation Architecture

Lakehouse Federation allows data engineers and BI analysts to query remote database engines (Snowflake, Google BigQuery, PostgreSQL, MySQL, Azure Synapse, and Amazon Redshift) directly through the Unity Catalog 3-level namespace without building ETL pipelines.

```mermaid
flowchart LR
    Client["Client Query: SELECT * FROM sf_catalog.sales.orders JOIN prod.silver.customers"]
    
    subgraph UC["Unity Catalog Engine"]
        Planner["Catalyst Query Planner"]
        Pushdown["Predicate & Aggregation Pushdown Analyzer"]
    end
    
    subgraph Remote["Remote External Database"]
        Snowflake["Snowflake / BigQuery / Postgres Engine"]
    end
    
    subgraph Lake["Databricks Lakehouse Storage"]
        Delta["Delta Lake Parquet Files (Customers)"]
    end

    Client --> Planner --> Pushdown
    Pushdown -->|"Pushed SQL: SELECT order_id, amount WHERE status='PAID'"| Snowflake
    Pushdown -->|"Scan Pruned Parquet"| Delta
    Snowflake & Delta -->|"In-Memory Stream Join"| Planner
```

1. **Foreign Connection**: Centralizes secure OAuth or credential secrets within Unity Catalog.
2. **Foreign Catalog**: Maps remote database schemas and tables automatically into Databricks.
3. **Intelligent Pushdown**: Filters (`WHERE`), projections (`SELECT`), and aggregations (`GROUP BY`) are translated into remote native SQL dialects and executed remotely, transferring only filtered rows across the network.

---

## 4. Open Source Unity Catalog (UC-OSS), ABAC & Clean Rooms

Unity Catalog has evolved into an open multi-engine standard (UC-OSS) governing data and AI assets across Apache Spark, Trino, Presto, DuckDB, Flink, and Daft via standardized REST APIs.

```mermaid
flowchart TD
    subgraph MultiEngine["Multi-Engine Open Computing Layer"]
        Spark["Apache Spark 3.5+"]
        Trino["Trino / Presto MPP"]
        DuckDB["DuckDB Local Analytics"]
        Flink["Apache Flink Streaming"]
    end

    subgraph UCGovernance["Unified Open Catalog Core"]
        Metastore["Open Source Unity Catalog (REST API)"]
        ABAC["Attribute-Based Access Control (ABAC)"]
        CleanRoom["Databricks Clean Rooms (Privacy Preserving)"]
        Monitor["Lakehouse Monitoring (Data/AI Drift Profiler)"]
    end

    subgraph DataAIAssets["3-Level Namespace Governed Assets"]
        Tables["Delta / Iceberg Tables (UniForm)"]
        Volumes["UC Volumes (Unstructured Files / Models)"]
        Functions["AI Functions & Prompt Templates"]
        Vectors["Mosaic AI Vector Indexes"]
    end

    MultiEngine --> Metastore
    Metastore --> ABAC --> DataAIAssets
    Metastore --> CleanRoom
    Metastore --> Monitor
```

### Production Security Implementation: Attribute-Based Access Control (ABAC) & Clean Rooms
```sql
-- 1. Apply governance tag to sensitive customer columns
ALTER TABLE prod_catalog.gold.dim_customer
ALTER COLUMN tax_identifier SET TAGS ('compliance_level' = 'restricted_pii');

-- 2. Define centralized ABAC policy masking tagged columns
CREATE OR REPLACE FUNCTION prod_catalog.governance.mask_restricted_pii(val STRING)
RETURN CASE
    WHEN IS_ACCOUNT_GROUP_MEMBER('compliance_officers') THEN val
    ELSE '***-RESTRICTED-PII-***'
END;

-- 3. Enforce policy dynamically across all tables with matching tag
CREATE OR REPLACE POLICY enforce_pii_masking
ON TAG compliance_level = 'restricted_pii'
APPLY MASK prod_catalog.governance.mask_restricted_pii;
```

### Key Governance Invariants:
- **Write Policy Once, Protect Everywhere**: Tag-based ABAC eliminates redundant column-by-column mask definitions across thousands of schemas.
- **Clean Rooms Differential Privacy**: Partners query shared lakehouse datasets without raw record visibility, enforcing minimum aggregation thresholds ($k \ge 50$).
- **Lakehouse Monitoring System Tables**: Automated data quality profiles, drift metrics, and anomaly scores land in `system.lakehouse_monitoring`.
