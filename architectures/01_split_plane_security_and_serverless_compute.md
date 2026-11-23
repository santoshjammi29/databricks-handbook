# 🏛️ Architecture Deep Dive: Split-Plane Cloud Security & Serverless Compute

## 1. Executive Overview & Theoretical Foundations

The Databricks Data Intelligence Platform is engineered on a **split-plane cloud architecture** that cleanly separates workspace orchestration and metadata management from raw compute execution and persistent customer storage. This decoupling guarantees that enterprise data assets remain strictly within the customer's cloud boundary while allowing Databricks to manage compute lifecycle, cluster orchestration, and platform telemetry.

```mermaid
flowchart TB
    subgraph CP["Control Plane (Databricks-Managed Cloud<br/>Tenant)"]
        UI["Workspace Web UI & IDE"]
        Scheduler["Lakeflow Jobs Scheduler"]
        Metastore["Unity Catalog Metastore Service"]
        ClusterMgr["Cluster Manager & Node Allocator"]
    end

    subgraph NetSec["Zero-Trust Network Perimeter"]
        PL_Front["Front-End Private Link (User -><br/>Workspace)"]
        PL_Back["Back-End Private Link (Control<br/>Plane -> Compute Plane)"]
    end

    subgraph DP["Compute Plane (Classic Customer VNet or<br/>Managed Serverless)"]
        subgraph Classic["Classic Compute (Customer Cloud VNet)"]
            Driver["Spark Driver Node"]
            Worker1["Spark Worker Node 1"]
            Worker2["Spark Worker Node 2"]
        end
        subgraph Serverless["Serverless Compute (Pre-warmed Container<br/>Fleet)"]
            SQL_WH["Serverless SQL Warehouses"]
            Serverless_Jobs["Serverless Jobs & Notebooks"]
        end
    end

    subgraph Storage["Persistent Customer Cloud Storage Layer"]
        ADLS["Azure ADLS Gen2 / AWS S3 / Google<br/>Cloud Storage"]
        SecCred["Unity Catalog Storage Credentials<br/>(OIDC / Managed Identity)"]
    end

    UI --> PL_Front
    ClusterMgr --> PL_Back --> Driver
    Driver --> Worker1 & Worker2
    Worker1 & Worker2 -->|"Direct HTTPS / TLS 1.3"| ADLS
    SQL_WH -->|Storage Credentials| ADLS
    Metastore -.->|Metadata Grants| Driver & SQL_WH
```

### 📐 Visual Architectural Blueprint: Unified Lakehouse Platform
![Databricks Unified Ecosystem & Lakehouse Architecture](../assets/whiteboards/databricks_ecosystem_landscape.webp)

---

## 2. Architectural Comparison: Classic Compute vs. Serverless Compute

| Architectural Dimension | Classic Compute Plane | Serverless Compute Plane |
| :--- | :--- | :--- |
| **Hosting Boundary** | Customer cloud subscription (VNet / VPC) | Databricks-managed secure cloud subscription |
| **Provisioning Latency** | 3 to 7 minutes (VM allocation, disk mount, OS boot) | 2 to 6 seconds (pre-warmed container micro-VMs) |
| **Networking & Security** | Customer manages VNet injection, NSGs, NAT gateways, route tables | Databricks manages network isolation + Private Endpoints to storage |
| **Autoscaling Mechanics** | VM-level horizontal scaling based on task backlog | Sub-second workload-aware horizontal and vertical elasticity |
| **Runtime Upgrades** | Manual Databricks Runtime (DBR) version selection & regression testing | Fully versionless; continuous security patching and engine optimizations |
| **Billing Model** | Databricks DBUs + Cloud Provider VM/Disk Infrastructure Costs | Unified all-inclusive Databricks DBU billing (zero direct VM bills) |
| **Idle Cost Waste** | Minimum 15-20 min cluster termination delays incur cost | Scale-to-zero within seconds of query completion |
| **Workload Suitability** | Long-running legacy batch pipelines requiring custom OS packages | DBSQL BI queries, automated Lakeflow Jobs, and DLT pipelines |

### 📐 Visual Architectural Blueprint: Serverless Photon Engine vs. Classic JVM
![Photon Engine vs. JVM Architecture](../assets/whiteboards/photon_engine_vs_jvm.webp)

---

## 3. Zero-Trust Network Perimeter & Private Link Architecture

In enterprise deployments (Banking, Healthcare, Government), public internet access to Databricks workspaces and data planes is strictly prohibited. Production environments implement dual Private Link endpoints:

1. **Front-End Private Link (User-to-Workspace)**:
   - Connects corporate VPNs or ExpressRoute / Direct Connect lines to the Databricks Web UI and REST API.
   - Public internet traffic is rejected at the workspace boundary (`publicNetworkAccess = Disabled`).
2. **Back-End Private Link (Control Plane to Compute Plane)**:
   - Secures the secure cluster connectivity relay (SCC).
   - Compute nodes establish outbound-only secure tunnels to the control plane without requiring public IP addresses on VMs (`enableNoPublicIp = true`).
3. **Storage Firewall & Private Endpoints**:
   - Customer storage accounts (ADLS Gen2 / S3) allow access *only* from the customer's VNet subnets and Databricks Serverless NAT IP ranges.
   - All data in transit is encrypted using TLS 1.3 with Customer-Managed Keys (CMK) for double encryption at rest.

---

## 4. Unity Catalog Storage Credential Delegation

Legacy architectures relied on static storage account keys or DBFS root mounts (`/mnt/`), creating significant security risks. Unity Catalog replaces mounts with **identity-based credential delegation**:

1. A cloud identity (Azure Managed Identity or AWS IAM Role) is created with least-privilege storage blob reader/writer access.
2. An account admin creates a **Storage Credential** in Unity Catalog pointing to that identity.
3. An **External Location** is created binding the Storage Credential to a specific container path (`abfss://data@lake.dfs.core.windows.net/`).
4. Users and compute clusters access tables using standard 3-level SQL (`SELECT * FROM prod.silver.orders`), and the driver obtains short-lived scoped SAS / STS tokens on demand. The user never sees or accesses storage keys.

---

## 4. Serverless Compute Architecture & Zero-Trust Workload Identity

Databricks Serverless Compute abstracts cluster provisioning entirely into an instant-on, auto-elastic compute fleet managed within Databricks cloud infrastructure with strict network and tenant isolation.

```mermaid
flowchart TD
    subgraph Client["Developer / CI/CD Client"]
        CLI["Databricks CLI / IDE (Databricks<br/>Connect)"]
        GHA["GitHub Actions (OIDC Token)"]
    end

    subgraph Auth["Zero-Trust Workload Identity"]
        OIDC["OIDC Token Exchange (Azure Entra /<br/>AWS IAM)"]
        OAuth["Short-Lived OAuth 2.0 Bearer Token<br/>(1 Hour)"]
    end

    subgraph ServerlessFleet["Serverless Compute Plane"]
        WarmPool["Auto-Warming Container Fleet (&lt;<br/>2s Startup)"]
        MicroVM["Encrypted Ephemeral Micro-VM<br/>(Single Tenant Pod)"]
        NCC["Network Connectivity Config (NCC)"]
    end

    subgraph CustomerCloud["Customer Cloud Storage Plane"]
        ADLS["ADLS Gen2 / AWS S3 (Data &<br/>Volumes)"]
        PrivateLink["Private Endpoint / AWS Privatelink<br/>VPC"]
    end

    Client --> OIDC --> OAuth
    OAuth --> MicroVM
    WarmPool --> MicroVM
    MicroVM --> NCC --> PrivateLink --> ADLS
```

### Production Security Implementation: OAuth M2M Workload Identity (GitHub Actions)
```yaml
# GitHub Actions workflow authenticating via OIDC federation
name: Deploy Serverless Workload
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write # Mandate OIDC JWT token generation
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Authenticate to Databricks via OIDC
        uses: databricks/setup-cli@v0.220.0
        with:
          host: https://adb-1234567890123456.7.azuredatabricks.net
          client-id: ${{ secrets.DATABRICKS_CLIENT_ID }}
          azure-tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          oidc-token: true # Zero static long-lived PAT tokens
```

### Key Serverless Security Invariants:
- **Instant Warm Pools**: Compute initializes in $< 2$ seconds by drawing from pre-warmed, patched container pools.
- **Network Connectivity Config (NCC)**: Directs outbound traffic from serverless compute through dedicated customer private endpoints.
- **Zero Static Credentials**: All service-to-service communication relies on short-lived OAuth 2.0 access tokens refreshed every 60 minutes.
