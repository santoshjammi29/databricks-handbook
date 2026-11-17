# 🚨 Production Runbook 06: Unity Catalog Storage Credential & Permission Disasters

> **Incident Severity**: SEV-1 (Enterprise Data Access Blackout)  
> **Target Systems**: Unity Catalog, Cloud Storage Credentials, External Locations, IAM / Managed Identities  
> **Recovery Objective**: Restore cloud storage access delegation, resolve expired credential tokens, and repair catalog permissions within 15 minutes.

---

## 1. Emergency Decision Tree

```
               [Alert: User Queries Fail: PERMISSION_DENIED / StorageAccessDenied]
                                                   │
                                      Inspect Failure Exception
                                                   │
                    ┌──────────────────────────────┴──────────────────────────────┐
                    ▼                                                             ▼
     [StorageAccessDenied / 403 Forbidden]                         [PERMISSION_DENIED in UC]
   (Cloud Object Storage Level Rejection)                      (Unity Catalog Metastore ACL Failure)
                    │                                                             │
         Check Storage Credential Status                               Check Grants on 3-Level Hierarchy
          (DESCRIBE STORAGE CREDENTIAL)                                  (SHOW GRANTS ON TABLE/SCHEMA)
                    │                                                             │
            ┌───────┴───────┐                                             ┌───────┴───────┐
            ▼               ▼                                             ▼               ▼
        [Expired]       [Role Loss]                                    [Missing]       [RLS Function]
      Rotate Secret   Restore Cloud                                    GRANT SELECT    Fix Boolean
      or Re-bind      IAM / Managed                                    or USE SCHEMA   Logic in Row
      Managed ID      Identity Policy                                  to Target Group Filter Function
```

### 📐 Visual Architectural Blueprint: Unity Catalog Security & Storage Credential Architecture
![Unity Catalog Security Architecture](../assets/whiteboards/unity_catalog_architecture.webp)

---

## 2. Forensic Diagnostic Queries

Execute these queries as an Account Admin or Metastore Admin:

```sql
-- 1. Inspect the Storage Credential configuration and cloud identity ARN / client ID
DESCRIBE STORAGE CREDENTIAL prod_storage_credential;

-- 2. Inspect the External Location bound to the storage container
DESCRIBE EXTERNAL LOCATION prod_data_lake_location;

-- 3. Verify user and group privileges across the 3-level namespace
SHOW GRANTS ON CATALOG prod_lakehouse;
SHOW GRANTS ON SCHEMA prod_lakehouse.silver;
SHOW GRANTS ON TABLE prod_lakehouse.silver.orders;

-- 4. Check audit logs for who revoked privileges or altered credentials
SELECT 
    event_time,
    user_identity.email AS performed_by,
    action_name,
    request_params.table_full_name,
    response.status_code
FROM system.access.audit
WHERE action_name IN ('revokePermissions', 'updateStorageCredential', 'updateExternalLocation')
  AND event_time >= NOW() - INTERVAL 4 HOURS
ORDER BY event_time DESC;
```

---

## 3. Surgical Remediation & Recovery

### 3.1 Repairing Cloud Storage Identity Delegation
If the cloud identity (Azure Managed Identity or AWS IAM Role) was accidentally detached from storage:
1. Re-assign `Storage Blob Data Contributor` (Azure) or `s3:GetObject, s3:PutObject` (AWS) to the cloud identity.
2. In Databricks, test credential validation:
   ```sql
   ALTER STORAGE CREDENTIAL prod_storage_credential 
   SET COMMENT 'Re-verified production storage access credential';
   ```

### 3.2 Repairing the 3-Level Privilege Chain
In Unity Catalog, a user needs `USE CATALOG`, `USE SCHEMA`, and `SELECT` to read a table. If any level is missing, queries fail with `PERMISSION_DENIED`:

```sql
-- Grant full readable traversal chain to analysts group
GRANT USE CATALOG ON CATALOG prod_lakehouse TO `analytics_users`;
GRANT USE SCHEMA ON SCHEMA prod_lakehouse.silver TO `analytics_users`;
GRANT SELECT ON TABLE prod_lakehouse.silver.orders TO `analytics_users`;
```

---

## 4. Permanent Architectural Prevention

1. **Role-Based Access via SCIM Groups**: Never grant permissions to individual user emails (`user@company.com`). Always grant to enterprise SCIM groups synchronized from Okta / Microsoft Entra ID.
2. **Infrastructure as Code (IaC) Only**: Manage all Unity Catalog grants, storage credentials, and external locations exclusively via Databricks Asset Bundles (DABs) or Terraform to prevent unauthorized manual clicks in the UI.
3. **Automated Credential Monitoring**: Schedule a daily test notebook via Lakeflow Jobs that reads and writes a 1-row canary table across all external locations and fires PagerDuty alerts on failure.
