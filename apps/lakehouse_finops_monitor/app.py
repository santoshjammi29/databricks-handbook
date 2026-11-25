"""
Databricks App: Lakehouse FinOps & DBU Consumption Monitor.

Built with Streamlit and Unity Catalog System Tables (with deterministic demo fallback).
"""

from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st

try:
    from apps.lakehouse_finops_monitor import finops_data
except ImportError:  # When executed directly from apps/lakehouse_finops_monitor via Streamlit
    import finops_data


def render_app() -> None:
    """Renders the Lakehouse FinOps & DBU Intelligence Streamlit dashboard."""
    st.set_page_config(
        page_title="Databricks Lakehouse FinOps Monitor",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("⚡ Databricks Lakehouse FinOps & DBU Intelligence Monitor")
    st.markdown(
        "*Real-time observability into DBU spend, cluster efficiency, serverless warehouse queues, "
        "and Predictive Optimization ROI powered by Unity Catalog **System Tables**.*"
    )

    # Sidebar Controls
    st.sidebar.header("🎯 FinOps Filters")
    default_end = datetime.date.today()
    default_start = default_end - datetime.timedelta(days=30)
    raw_dates = st.sidebar.date_input("Analysis Window", value=(default_start, default_end))
    start_date, end_date = finops_data.normalize_date_range(raw_dates, fallback_end=default_end)

    selected_env = st.sidebar.selectbox(
        "Target Environment", list(finops_data.DEFAULT_ENVIRONMENTS)
    )
    selected_skus = st.sidebar.multiselect(
        "Workload SKUs",
        list(finops_data.DEFAULT_SKUS),
        default=["ALL_PURPOSE", "JOBS", "SERVERLESS_SQL"],
    )

    records, zombies, po_metrics, src_mode, src_detail = finops_data.load_finops_telemetry(
        start_date=start_date,
        end_date=end_date,
    )
    snapshot = finops_data.summarize_finops(
        records,
        zombies,
        po_metrics,
        start_date=start_date,
        end_date=end_date,
        selected_env=selected_env,
        selected_skus=selected_skus,
        source=src_mode,
        source_detail=src_detail,
    )

    if snapshot.source == "live":
        st.sidebar.success(f"🟢 Live System Tables\n\n{snapshot.source_detail}")
    else:
        st.sidebar.info(f"🟡 Simulated Telemetry Mode\n\n{snapshot.source_detail}")

    window_days = max((end_date - start_date).days + 1, 1)

    # Dynamic Top KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"Total {window_days}-Day DBUs",
            value=f"{snapshot.total_dbus:,.1f}",
            delta=f"{len(selected_skus)} SKUs active",
        )
    with col2:
        st.metric(
            label="Estimated Cloud Cost",
            value=f"${snapshot.estimated_cost_usd:,.2f}",
            delta=f"Env: {selected_env}",
        )
    with col3:
        st.metric(
            label="Avg Cluster Utilization",
            value=f"{snapshot.avg_cpu_pct:.1f}%",
            delta="Target >= 70.0%",
        )
    with col4:
        st.metric(
            label="Predictive Opt Storage ROI",
            value=f"${snapshot.po_storage_roi_usd:,.0f} / mo",
            delta=f"Env: {selected_env}",
        )

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["📊 DBU Spend by SKU", "🔍 Cluster Right-Sizing", "💡 Predictive Optimization ROI"]
    )

    with tab1:
        st.subheader("Daily DBU Consumption across Filtered Workload SKUs")
        if not snapshot.daily_spend_rows or not selected_skus:
            st.warning("No matching telemetry records for the selected window, env, or SKUs.")
        else:
            df_spend = pd.DataFrame(snapshot.daily_spend_rows).set_index("Date")
            st.area_chart(df_spend)

    with tab2:
        st.subheader("Zombie & Underutilized Interactive Clusters")
        st.info(
            "Interactive clusters with < 15% average CPU over the last 7 days recommended "
            "for auto-termination reduction."
        )
        if not snapshot.zombie_clusters:
            st.success("No underutilized clusters flagged for the selected environment.")
        else:
            st.dataframe(pd.DataFrame(snapshot.zombie_clusters), use_container_width=True)

    with tab3:
        st.subheader("Predictive Optimization: Automated Compaction & VACUUM Savings")
        st.success(
            "Predictive Optimization eliminates manual OPTIMIZE/VACUUM scheduling overhead "
            "via automated small-file compaction and tombstone cleanup."
        )
        st.table(pd.DataFrame(snapshot.compaction_rows))


if __name__ == "__main__":
    render_app()
