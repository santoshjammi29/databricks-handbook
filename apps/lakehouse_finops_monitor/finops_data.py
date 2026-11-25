"""Pure-Python telemetry loader, live Databricks SDK bridge, and filter engine for FinOps App."""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Any

DEFAULT_ENVIRONMENTS: tuple[str, ...] = ("All", "Production", "Staging", "Development")
DEFAULT_SKUS: tuple[str, ...] = (
    "ALL_PURPOSE",
    "JOBS",
    "SERVERLESS_SQL",
    "PRO_SQL",
    "DLT_ADVANCED",
    "MODEL_SERVING",
)

SKU_DISPLAY_NAMES: dict[str, str] = {
    "JOBS": "Automated Jobs",
    "SERVERLESS_SQL": "Serverless SQL",
    "ALL_PURPOSE": "Interactive / All-Purpose",
    "DLT_ADVANCED": "DLT Pipelines",
    "PRO_SQL": "Pro SQL Warehouses",
    "MODEL_SERVING": "Mosaic AI Model Serving",
}

SKU_PRICING_USD_PER_DBU: dict[str, float] = {
    "JOBS": 0.15,
    "SERVERLESS_SQL": 0.70,
    "ALL_PURPOSE": 0.55,
    "DLT_ADVANCED": 0.36,
    "PRO_SQL": 0.22,
    "MODEL_SERVING": 0.07,
}

_SKU_KEYWORD_BUCKETS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("ALL_PURPOSE",), "ALL_PURPOSE"),
    (("SERVERLESS", "SQL"), "SERVERLESS_SQL"),
    (("PRO_SQL",), "PRO_SQL"),
    (("SQL_PRO",), "PRO_SQL"),
    (("DLT",), "DLT_ADVANCED"),
    (("DELTA_LIVE_TABLES",), "DLT_ADVANCED"),
    (("MODEL_SERVING",), "MODEL_SERVING"),
    (("SERVERLESS_REAL_TIME_INFERENCE",), "MODEL_SERVING"),
    (("JOBS",), "JOBS"),
)


def normalize_sku_name(raw_sku: str) -> str:
    """Maps raw Databricks system.billing.usage sku_name values into DEFAULT_SKUS buckets."""
    normalized = raw_sku.strip().upper()
    if normalized in DEFAULT_SKUS:
        return normalized
    for required_tokens, bucket in _SKU_KEYWORD_BUCKETS:
        if all(token in normalized for token in required_tokens):
            return bucket
    return normalized


@dataclass(frozen=True)
class SpendRecord:
    """Single day x environment x SKU DBU and compute utilization observation."""

    usage_date: datetime.date
    environment: str
    sku: str
    dbus: float
    cost_usd: float
    avg_cpu_pct: float


@dataclass(frozen=True)
class ZombieCluster:
    """Interactive cluster flagged for low CPU utilization."""

    cluster_name: str
    environment: str
    owner: str
    node_type: str
    max_workers: int
    avg_cpu_pct: float
    action: str


@dataclass(frozen=True)
class PredictiveOptMetric:
    """Unity Catalog Predictive Optimization storage & latency impact per environment."""

    environment: str
    files_eliminated: int
    files_vacuumed: int
    storage_reclaimed_tb: float
    avg_speedup_x: float
    monthly_roi_usd: float


@dataclass(frozen=True)
class FinOpsSnapshot:
    """Filtered KPI, chart, zombie cluster, and Predictive Optimization snapshot."""

    source: str
    source_detail: str
    total_dbus: float
    estimated_cost_usd: float
    avg_cpu_pct: float
    po_storage_roi_usd: float
    daily_spend_rows: list[dict[str, object]]
    zombie_clusters: list[dict[str, object]]
    compaction_rows: list[dict[str, str]]


def normalize_date_range(
    raw_range: datetime.date | tuple[datetime.date, ...] | list[datetime.date],
    fallback_end: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Normalizes Streamlit date_input outputs (single date, 1-tuple, or 2-tuple)."""
    today = fallback_end or datetime.date.today()
    if isinstance(raw_range, datetime.date):
        return raw_range, raw_range
    items = list(raw_range)
    if not items:
        return today - datetime.timedelta(days=30), today
    if len(items) == 1:
        return items[0], items[0]
    start_d, end_d = items[0], items[1]
    if start_d > end_d:
        return end_d, start_d
    return start_d, end_d


def generate_demo_telemetry(
    anchor_date: datetime.date | None = None,
    days: int = 35,
) -> tuple[list[SpendRecord], list[ZombieCluster], list[PredictiveOptMetric]]:
    """Generates deterministic multi-env, multi-SKU synthetic System Table telemetry."""
    end_d = anchor_date or datetime.date.today()
    start_d = end_d - datetime.timedelta(days=max(days - 1, 0))

    env_multipliers = {
        "Production": (1.0, 81.5),
        "Staging": (0.38, 68.0),
        "Development": (0.24, 52.5),
    }
    sku_baselines = {
        "JOBS": 310.0,
        "SERVERLESS_SQL": 185.0,
        "ALL_PURPOSE": 95.0,
        "DLT_ADVANCED": 78.0,
        "PRO_SQL": 52.0,
        "MODEL_SERVING": 40.0,
    }

    records: list[SpendRecord] = []
    for day_idx in range(days):
        curr_date = start_d + datetime.timedelta(days=day_idx)
        weekend_factor = 0.72 if curr_date.weekday() >= 5 else 1.0
        for env_name, (env_scale, base_cpu) in env_multipliers.items():
            for sku_idx, sku in enumerate(DEFAULT_SKUS):
                base_dbus = sku_baselines[sku] * env_scale * weekend_factor
                trend = ((day_idx + sku_idx * 3) % 9 - 4) * 3.5 * env_scale
                dbus = round(max(base_dbus + trend, 4.0), 2)
                rate = SKU_PRICING_USD_PER_DBU[sku]
                cost = round(dbus * rate, 2)
                cpu_delta = ((day_idx + sku_idx) % 7 - 3) * 1.1
                cpu = round(min(max(base_cpu + cpu_delta, 10.0), 96.0), 1)
                records.append(
                    SpendRecord(
                        usage_date=curr_date,
                        environment=env_name,
                        sku=sku,
                        dbus=dbus,
                        cost_usd=cost,
                        avg_cpu_pct=cpu,
                    )
                )

    zombies = [
        ZombieCluster(
            cluster_name="legacy-etl-sandbox",
            environment="Development",
            owner="contractor@example.com",
            node_type="Standard_D8ds_v5",
            max_workers=6,
            avg_cpu_pct=4.1,
            action="Terminate Immediately (Zero Activity)",
        ),
        ZombieCluster(
            cluster_name="adhoc-analyst-pool-01",
            environment="Development",
            owner="dev_analyst@example.com",
            node_type="Standard_E8ds_v5",
            max_workers=8,
            avg_cpu_pct=8.4,
            action="Reduce Auto-Stop to 10 min",
        ),
        ZombieCluster(
            cluster_name="feature-eng-scratch",
            environment="Staging",
            owner="ml_engineer@example.com",
            node_type="Standard_D16ds_v5",
            max_workers=4,
            avg_cpu_pct=11.2,
            action="Migrate to Single-User Job Cluster",
        ),
        ZombieCluster(
            cluster_name="bi-shared-allpurpose-02",
            environment="Production",
            owner="bi_platform@example.com",
            node_type="Standard_E16ds_v5",
            max_workers=10,
            avg_cpu_pct=13.7,
            action="Route Ad-Hoc SQL to Serverless SQL Warehouse",
        ),
    ]

    po_metrics = [
        PredictiveOptMetric(
            environment="Production",
            files_eliminated=298400,
            files_vacuumed=132600,
            storage_reclaimed_tb=10.4,
            avg_speedup_x=4.5,
            monthly_roi_usd=890.0,
        ),
        PredictiveOptMetric(
            environment="Staging",
            files_eliminated=74120,
            files_vacuumed=34800,
            storage_reclaimed_tb=2.9,
            avg_speedup_x=3.8,
            monthly_roi_usd=235.0,
        ),
        PredictiveOptMetric(
            environment="Development",
            files_eliminated=40370,
            files_vacuumed=16800,
            storage_reclaimed_tb=1.5,
            avg_speedup_x=3.1,
            monthly_roi_usd=115.0,
        ),
    ]
    return records, zombies, po_metrics


def _create_workspace_client() -> Any:
    """Creates a Databricks WorkspaceClient using ambient Databricks Apps / SDK auth."""
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _build_date_params(start_date: datetime.date, end_date: datetime.date) -> list[Any]:
    """Builds StatementParameterListItem objects for parameterized Databricks SQL."""
    try:
        from databricks.sdk.service.sql import StatementParameterListItem

        return [
            StatementParameterListItem(
                name="start_date", value=start_date.isoformat(), type="DATE"
            ),
            StatementParameterListItem(name="end_date", value=end_date.isoformat(), type="DATE"),
        ]
    except ImportError:
        return [
            {"name": "start_date", "value": start_date.isoformat(), "type": "DATE"},
            {"name": "end_date", "value": end_date.isoformat(), "type": "DATE"},
        ]


def _query_live_system_tables(
    warehouse_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[SpendRecord]:
    """Queries system.billing.usage via Databricks Statement Execution API."""
    client = _create_workspace_client()
    query = """
    SELECT
        CAST(usage_date AS STRING) AS usage_date,
        COALESCE(custom_tags['environment'], 'Production') AS environment,
        sku_name AS sku,
        ROUND(SUM(usage_quantity), 2) AS dbus,
        ROUND(SUM(usage_quantity * 0.30), 2) AS cost_usd,
        75.0 AS avg_cpu_pct
    FROM system.billing.usage
    WHERE usage_date BETWEEN :start_date AND :end_date
    GROUP BY 1, 2, 3
    ORDER BY 1 ASC
    """
    resp = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=query,
        parameters=_build_date_params(start_date, end_date),
        wait_timeout="30s",
    )
    state = getattr(getattr(resp, "status", None), "state", None)
    state_val = getattr(state, "value", str(state))
    if state_val != "SUCCEEDED":
        raise RuntimeError(f"Statement execution ended with state={state_val}")

    data_array = getattr(getattr(resp, "result", None), "data_array", None) or []
    records: list[SpendRecord] = []
    for row in data_array:
        records.append(
            SpendRecord(
                usage_date=datetime.date.fromisoformat(str(row[0])),
                environment=str(row[1]),
                sku=normalize_sku_name(str(row[2] or "")),
                dbus=float(row[3] or 0.0),
                cost_usd=float(row[4] or 0.0),
                avg_cpu_pct=float(row[5] or 0.0),
            )
        )
    return records


def load_finops_telemetry(
    start_date: datetime.date,
    end_date: datetime.date,
    anchor_date: datetime.date | None = None,
) -> tuple[list[SpendRecord], list[ZombieCluster], list[PredictiveOptMetric], str, str]:
    """Loads live Databricks System Table telemetry when configured, else clean demo data."""
    days = max((end_date - start_date).days + 1, 35)
    effective_anchor = anchor_date if anchor_date is not None else end_date
    demo_records, zombies, po_metrics = generate_demo_telemetry(
        anchor_date=effective_anchor,
        days=days,
    )

    host = os.environ.get("DATABRICKS_HOST", "").strip()
    warehouse_id = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", "").strip()
    if not (host and warehouse_id):
        return (
            demo_records,
            zombies,
            po_metrics,
            "demo",
            "Simulated System Table telemetry (set DATABRICKS_HOST & DATABRICKS_SQL_WAREHOUSE_ID for live SQL).",
        )

    try:
        live_records = _query_live_system_tables(warehouse_id, start_date, end_date)
        return (
            live_records,
            zombies,
            po_metrics,
            "live",
            f"Connected to Databricks SQL Warehouse {warehouse_id} (system.billing.usage).",
        )
    except Exception as exc:
        return (
            demo_records,
            zombies,
            po_metrics,
            "demo",
            f"Live query fallback ({exc}); showing deterministic simulated telemetry.",
        )


def summarize_finops(
    records: list[SpendRecord],
    zombies: list[ZombieCluster],
    po_metrics: list[PredictiveOptMetric],
    *,
    start_date: datetime.date,
    end_date: datetime.date,
    selected_env: str,
    selected_skus: list[str],
    source: str = "demo",
    source_detail: str = "",
) -> FinOpsSnapshot:
    """Computes filtered KPIs, daily SKU chart rows, zombie clusters, and PO ROI table."""
    allowed_skus = set(selected_skus)
    filtered = [
        r
        for r in records
        if start_date <= r.usage_date <= end_date
        and (selected_env == "All" or r.environment == selected_env)
        and r.sku in allowed_skus
    ]

    total_dbus = round(sum(r.dbus for r in filtered), 1)
    estimated_cost = round(sum(r.cost_usd for r in filtered), 2)
    avg_cpu = round(sum(r.avg_cpu_pct for r in filtered) / len(filtered), 1) if filtered else 0.0

    filtered_po = [p for p in po_metrics if selected_env == "All" or p.environment == selected_env]
    po_roi = round(sum(p.monthly_roi_usd for p in filtered_po), 2)

    # Aggregate daily spend rows keyed by Date and SKU display label
    daily_buckets: dict[datetime.date, dict[str, float]] = {}
    for rec in filtered:
        bucket = daily_buckets.setdefault(rec.usage_date, {})
        label = SKU_DISPLAY_NAMES.get(rec.sku, rec.sku)
        bucket[label] = round(bucket.get(label, 0.0) + rec.dbus, 2)

    active_labels = [
        SKU_DISPLAY_NAMES.get(sku, sku) for sku in selected_skus if sku in allowed_skus
    ]
    daily_spend_rows: list[dict[str, object]] = []
    for usage_day in sorted(daily_buckets):
        row: dict[str, object] = {"Date": usage_day.isoformat()}
        for label in active_labels:
            row[label] = daily_buckets[usage_day].get(label, 0.0)
        daily_spend_rows.append(row)

    filtered_zombies = sorted(
        (z for z in zombies if selected_env == "All" or z.environment == selected_env),
        key=lambda z: z.avg_cpu_pct,
    )
    zombie_rows = [
        {
            "Cluster Name": z.cluster_name,
            "Environment": z.environment,
            "Owner": z.owner,
            "Node Type": z.node_type,
            "Max Workers": z.max_workers,
            "Avg CPU": f"{z.avg_cpu_pct:.1f}%",
            "Action": z.action,
        }
        for z in filtered_zombies
    ]

    total_eliminated = sum(p.files_eliminated for p in filtered_po)
    total_vacuumed = sum(p.files_vacuumed for p in filtered_po)
    total_reclaimed = round(sum(p.storage_reclaimed_tb for p in filtered_po), 1)
    avg_speedup = (
        round(sum(p.avg_speedup_x for p in filtered_po) / len(filtered_po), 1)
        if filtered_po
        else 0.0
    )
    compaction_rows = [
        {"Metric": "Total Small Files Eliminated", "Value": f"{total_eliminated:,} files"},
        {"Metric": "Tombstoned Parquet Cleaned (VACUUM)", "Value": f"{total_vacuumed:,} files"},
        {"Metric": "Storage Reclaimed (TB)", "Value": f"{total_reclaimed:.1f} TB"},
        {"Metric": "Avg Query Read Speedup", "Value": f"{avg_speedup:.1f}x faster scan"},
    ]

    return FinOpsSnapshot(
        source=source,
        source_detail=source_detail,
        total_dbus=total_dbus,
        estimated_cost_usd=estimated_cost,
        avg_cpu_pct=avg_cpu,
        po_storage_roi_usd=po_roi,
        daily_spend_rows=daily_spend_rows,
        zombie_clusters=zombie_rows,
        compaction_rows=compaction_rows,
    )
