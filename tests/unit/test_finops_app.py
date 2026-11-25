"""Unit and regression tests for apps/lakehouse_finops_monitor."""

from __future__ import annotations

import ast
import datetime
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_finops_data_module(base_dir: Path):
    mod_path = base_dir / "apps" / "lakehouse_finops_monitor" / "finops_data.py"
    assert mod_path.exists(), f"Expected FinOps data module at {mod_path}"
    spec = importlib.util.spec_from_file_location("finops_data", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_app_wires_sidebar_filters_and_drops_hardcoded_kpi(base_dir: Path):
    app_path = base_dir / "apps" / "lakehouse_finops_monitor" / "app.py"
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert tree is not None

    # Regression check: hardcoded KPI metrics and static table literals must be gone.
    assert 'value="14,820"' not in source
    assert 'value="$4,446.00"' not in source
    assert "finops_data" in source
    assert "load_finops_telemetry" in source
    assert "summarize_finops" in source


def test_finops_filtering_responds_to_dates_env_and_skus(base_dir: Path, monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_SQL_WAREHOUSE_ID", raising=False)
    finops = _load_finops_data_module(base_dir)

    today = datetime.date(2026, 11, 25)
    records, zombies, po_metrics, src, _detail = finops.load_finops_telemetry(
        start_date=today - datetime.timedelta(days=29),
        end_date=today,
        anchor_date=today,
    )
    assert src == "demo"
    assert len(records) > 0

    full = finops.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=today - datetime.timedelta(days=29),
        end_date=today,
        selected_env="All",
        selected_skus=list(finops.DEFAULT_SKUS),
        source=src,
    )
    prod_only = finops.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=today - datetime.timedelta(days=29),
        end_date=today,
        selected_env="Production",
        selected_skus=["JOBS", "SERVERLESS_SQL"],
        source=src,
    )
    short_window = finops.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=today - datetime.timedelta(days=6),
        end_date=today,
        selected_env="All",
        selected_skus=list(finops.DEFAULT_SKUS),
        source=src,
    )

    assert full.total_dbus > prod_only.total_dbus > 0
    assert full.total_dbus > short_window.total_dbus > 0
    assert full.estimated_cost_usd > prod_only.estimated_cost_usd > 0
    assert len(short_window.daily_spend_rows) == 7
    assert all(z["Environment"] == "Production" for z in prod_only.zombie_clusters)
    assert len(prod_only.zombie_clusters) < len(full.zombie_clusters)


def test_finops_empty_sku_selection_returns_zeroed_snapshot(base_dir: Path):
    finops = _load_finops_data_module(base_dir)
    today = datetime.date(2026, 11, 25)
    records, zombies, po_metrics, src, _ = finops.load_finops_telemetry(
        start_date=today - datetime.timedelta(days=13),
        end_date=today,
        anchor_date=today,
    )
    empty = finops.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=today - datetime.timedelta(days=13),
        end_date=today,
        selected_env="All",
        selected_skus=[],
        source=src,
    )
    assert empty.total_dbus == 0.0
    assert empty.estimated_cost_usd == 0.0
    assert empty.avg_cpu_pct == 0.0
    assert empty.daily_spend_rows == []


def test_finops_live_sdk_execution_and_fallback(base_dir: Path, monkeypatch):
    finops = _load_finops_data_module(base_dir)
    today = datetime.date(2026, 11, 25)

    class _FakeStatementResp:
        def __init__(self):
            self.status = SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED"))
            self.result = SimpleNamespace(
                data_array=[
                    ["2026-11-24", "Production", "JOBS", "420.5", "63.08", "81.2"],
                    ["2026-11-25", "Staging", "SERVERLESS_SQL", "180.0", "126.00", "64.0"],
                ]
            )

    class _FakeStatementExecution:
        def execute_statement(self, **kwargs):
            assert kwargs["warehouse_id"] == "wh-123"
            assert "system.billing.usage" in kwargs["statement"]
            assert ":start_date AND :end_date" in kwargs["statement"]
            assert len(kwargs["parameters"]) == 2
            return _FakeStatementResp()

    class _FakeWorkspaceClient:
        def __init__(self):
            self.statement_execution = _FakeStatementExecution()

    monkeypatch.setenv("DATABRICKS_HOST", "https://adb-example.azuredatabricks.net")
    monkeypatch.setenv("DATABRICKS_SQL_WAREHOUSE_ID", "wh-123")
    monkeypatch.setattr(finops, "_create_workspace_client", lambda: _FakeWorkspaceClient())

    records, _, _, src, detail = finops.load_finops_telemetry(
        start_date=today - datetime.timedelta(days=7),
        end_date=today,
        anchor_date=today,
    )
    assert src == "live"
    assert "wh-123" in detail
    assert len(records) == 2
    assert sum(r.dbus for r in records) == 600.5

    # Simulate transient workspace failure -> clean demo fallback
    monkeypatch.setattr(
        finops,
        "_create_workspace_client",
        lambda: (_ for _ in ()).throw(RuntimeError("auth unavailable")),
    )
    fb_records, _, _, fb_src, fb_detail = finops.load_finops_telemetry(
        start_date=today - datetime.timedelta(days=7),
        end_date=today,
        anchor_date=today,
    )
    assert fb_src == "demo"
    assert "auth unavailable" in fb_detail
    assert len(fb_records) > 0


def test_normalize_date_range_handles_single_tuple_reversed_and_empty(base_dir: Path):
    finops = _load_finops_data_module(base_dir)
    fallback = datetime.date(2026, 11, 25)
    d1 = datetime.date(2026, 11, 10)
    d2 = datetime.date(2026, 11, 20)

    assert finops.normalize_date_range(d1, fallback_end=fallback) == (d1, d1)
    assert finops.normalize_date_range((d1,), fallback_end=fallback) == (d1, d1)
    assert finops.normalize_date_range([d1], fallback_end=fallback) == (d1, d1)
    assert finops.normalize_date_range((d1, d2), fallback_end=fallback) == (d1, d2)
    assert finops.normalize_date_range((d2, d1), fallback_end=fallback) == (d1, d2)
    assert finops.normalize_date_range((), fallback_end=fallback) == (
        fallback - datetime.timedelta(days=30),
        fallback,
    )


def test_normalize_sku_name_and_live_sql_mapping(base_dir: Path, monkeypatch):
    finops = _load_finops_data_module(base_dir)
    today = datetime.date(2026, 11, 25)

    assert finops.normalize_sku_name("STANDARD_ALL_PURPOSE_COMPUTE") == "ALL_PURPOSE"
    assert finops.normalize_sku_name("ENTERPRISE_JOBS_COMPUTE") == "JOBS"
    assert finops.normalize_sku_name("PREMIUM_SQL_SERVERLESS_COMPUTE") == "SERVERLESS_SQL"
    assert finops.normalize_sku_name("PRO_SQL") == "PRO_SQL"
    assert finops.normalize_sku_name("ENTERPRISE_SQL_PRO_COMPUTE") == "PRO_SQL"
    assert finops.normalize_sku_name("DLT_CORE") == "DLT_ADVANCED"
    assert finops.normalize_sku_name("MODEL_SERVING_GPU") == "MODEL_SERVING"
    assert finops.normalize_sku_name("custom_vector_search") == "CUSTOM_VECTOR_SEARCH"

    class _FakeStatementResp:
        def __init__(self):
            self.status = SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED"))
            self.result = SimpleNamespace(
                data_array=[
                    [
                        "2026-11-24",
                        "Production",
                        "STANDARD_ALL_PURPOSE_COMPUTE",
                        "100.0",
                        "55.0",
                        "70.0",
                    ],
                    [
                        "2026-11-24",
                        "Production",
                        "ENTERPRISE_JOBS_COMPUTE",
                        "200.0",
                        "30.0",
                        "82.0",
                    ],
                    [
                        "2026-11-25",
                        "Staging",
                        "PREMIUM_SQL_SERVERLESS_COMPUTE",
                        "150.0",
                        "105.0",
                        "75.0",
                    ],
                    ["2026-11-25", "Staging", "ENTERPRISE_SQL_PRO_COMPUTE", "50.0", "11.0", "68.0"],
                    ["2026-11-25", "Production", "DLT_CORE", "75.0", "27.0", "80.0"],
                    ["2026-11-25", "Production", "MODEL_SERVING_GPU", "25.0", "1.75", "65.0"],
                ]
            )

    class _FakeWorkspaceClient:
        def __init__(self):
            self.statement_execution = SimpleNamespace(
                execute_statement=lambda **_kwargs: _FakeStatementResp()
            )

    gen_calls: list[tuple[datetime.date | None, int]] = []
    orig_gen = finops.generate_demo_telemetry

    def _counting_gen(anchor_date=None, days=35):
        gen_calls.append((anchor_date, days))
        return orig_gen(anchor_date=anchor_date, days=days)

    monkeypatch.setattr(finops, "generate_demo_telemetry", _counting_gen)
    monkeypatch.setenv("DATABRICKS_HOST", "https://adb-example.azuredatabricks.net")
    monkeypatch.setenv("DATABRICKS_SQL_WAREHOUSE_ID", "wh-sku-norm")
    monkeypatch.setattr(finops, "_create_workspace_client", lambda: _FakeWorkspaceClient())

    records, zombies, po_metrics, src, _ = finops.load_finops_telemetry(
        start_date=today - datetime.timedelta(days=2),
        end_date=today,
        anchor_date=today,
    )
    assert src == "live"
    assert gen_calls == [(today, 35)]
    assert [r.sku for r in records] == list(finops.DEFAULT_SKUS)

    snap = finops.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=today - datetime.timedelta(days=2),
        end_date=today,
        selected_env="All",
        selected_skus=list(finops.DEFAULT_SKUS),
        source=src,
    )
    assert snap.total_dbus == 600.0
    assert len(snap.daily_spend_rows) == 2
