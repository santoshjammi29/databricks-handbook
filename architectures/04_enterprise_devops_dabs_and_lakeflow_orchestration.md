# 🏛️ Architecture Deep Dive: Enterprise DevOps, DABs & Lakeflow Orchestration

## 1. Executive Overview: Infrastructure as Code for Data & AI

Modern enterprise data platforms require automated, reproducible, multi-environment deployment pipelines. **Databricks Asset Bundles (DABs)** provide declarative Infrastructure as Code (IaC) for Lakeflow Jobs, Delta Live Tables (DLT) declarative pipelines, Unity Catalog schemas, MLflow model serving endpoints, and Databricks Apps.

```mermaid
flowchart LR
    subgraph Repo["Git Repository (Source Control)"]
        YML["databricks.yml & resources/*.yml"]
        Code["Notebooks / Wheels / DLT Code"]
        App["Databricks App (Streamlit)"]
    end

    subgraph CI["CI/CD Automation (GitHub Actions / GitLab CI)"]
        Lint["bundle validate (Schema Check)"]
        Test["pytest + chispa (Unit Testing)"]
        Deploy["bundle deploy -t {env} (Asset Sync)"]
    end

    subgraph Environments["Target Databricks Workspaces"]
        Dev["Dev Workspace (Personal Sandbox: /Users/dev/.bundle)"]
        Staging["Staging Workspace (Integration Testing: /Shared/.bundle)"]
        Prod["Prod Workspace (Production Service Principal Deployment)"]
    end

    Repo --> Lint --> Test --> Deploy
    Deploy -->|Target: dev| Dev
    Deploy -->|Target: staging| Staging
    Deploy -->|Target: prod (OIDC / OAuth)| Prod
```

### 📐 Visual Architectural Blueprint: Databricks Asset Bundles (DABs) Enterprise DevOps
![Databricks DABs DevOps Pipeline](../assets/whiteboards/databricks_dabs_devops_pipeline.webp)

---

## 2. DABs Multi-Environment Targeting & Variable Scoping

A single bundle definition dynamically adapts across deployment targets via declarative variable substitution in `databricks.yml`:

```yaml
bundle:
  name: databricks-handbook

variables:
  catalog:
    default: "main"
  schema:
    default: "analytics"

targets:
  dev:
    mode: development
    default: true
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}
    variables:
      catalog: "dev_lakehouse"
      schema: "sandbox_${workspace.current_user.short_name}"

  prod:
    mode: production
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/${bundle.target}
    variables:
      catalog: "prod_lakehouse"
      schema: "gold_reporting"
    run_as:
      service_principal_name: "4f63c679-0db8-40a2-b91a-7b3b7e7136f4"
```

### Critical Production Rules:
- **`mode: development`**: Automatically pauses job schedules, prepends `[dev username]` to resource names, and deletes resources when developer sandboxes are torn down.
- **`mode: production`**: Enforces strict git branch validation, prevents accidental deletion of production tables, unpauses scheduled triggers, and mandates `run_as` Service Principal ownership.
- **Zero Human Credentials in CI/CD**: GitHub Actions authenticates via cloud OIDC (OpenID Connect) federation using Azure App Registrations or AWS IAM Roles. No static tokens are stored in repository secrets.

---

## 3. Lakeflow Jobs: Multi-Task Orchestration & Failure Recovery

Lakeflow Jobs provide enterprise DAG orchestration with fine-grained task dependencies, parameter inheritance, and conditional branching:

```mermaid
flowchart TD
    T1["Task 1: Auto Loader Bronze Ingestion (Ephemeral Job Cluster)"] --> T2["Task 2: DLT Silver Conformance & Quality Expectations"]
    T2 --> T3{"Conditional Task: Did Quality Pass?"}
    T3 -- "Pass (> 99.9% clean)" --> T4["Task 4: Gold Aggregation & Liquid Clustering"]
    T3 -- "Fail / Anomalies" --> T5["Task 5: Dead Letter Queue (DLQ) Quarantine Triage"]
    T4 --> T6["Task 6: Mosaic AI Lakehouse Monitoring & Drift Audit"]
    T5 --> T7["Task 7: PagerDuty On-Call Incident Notification"]
```

### 📐 Visual Architectural Blueprint: Lakeflow Declarative Delta Live Tables (DLT) Pipeline
![Databricks DLT Pipeline](../assets/whiteboards/databricks_dlt_pipeline.webp)

### Production Orchestration Invariants:
1. **Inter-Task Parameter Passing**: Upstream tasks emit dynamic metrics (processed row counts, execution timestamps, validation flags) using `dbutils.jobs.taskValues.set(key, value)`. Downstream tasks consume them via `dbutils.jobs.taskValues.get(taskKey, key)`.
2. **Surgical Repair and Rerun**: If Task 4 fails due to temporary network saturation, the data engineer triggers `Repair Run`. Lakeflow re-runs *only* Task 4 and downstream tasks, completely preserving the compute time and state of completed upstream tasks (Tasks 1 and 2).
3. **Ephemeral Job Clusters vs. Serverless**: Batch ETL jobs utilize ephemeral job clusters (which terminate immediately upon task completion) or Serverless Jobs (instant zero-startup-latency compute) to eliminate idle infrastructure waste.
