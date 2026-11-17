"""
Databricks App: Lakehouse FinOps & DBU Consumption Monitor
Built with Streamlit & Unity Catalog System Tables
"""

import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="Databricks Lakehouse FinOps Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Databricks Lakehouse FinOps & DBU Intelligence Monitor")
st.markdown("""
*Real-time observability into DBU spend, cluster efficiency, serverless warehouse queues, and Predictive Optimization ROI powered by Unity Catalog **System Tables**.*
""")

# Sidebar Controls
st.sidebar.header("🎯 FinOps Filters")
date_range = st.sidebar.date_input(
    "Analysis Window",
    value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today())
)
selected_env = st.sidebar.selectbox("Target Environment", ["All", "Production", "Staging", "Development"])
selected_sku = st.sidebar.multiselect(
    "Workload SKUs",
    ["ALL_PURPOSE", "JOBS", "SERVERLESS_SQL", "PRO_SQL", "DLT_ADVANCED", "MODEL_SERVING"],
    default=["ALL_PURPOSE", "JOBS", "SERVERLESS_SQL"]
)

# Top KPI metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total 30-Day DBUs", value="14,820", delta="-8.4% MoM")
with col2:
    st.metric(label="Estimated Cloud Cost", value="$4,446.00", delta="-$408.00")
with col3:
    st.metric(label="Avg Cluster Utilization", value="76.2%", delta="+4.1%")
with col4:
    st.metric(label="Predictive Opt Storage ROI", value="$1,240 / mo", delta="+12.5%")

st.divider()

# Tabbed Interface
tab1, tab2, tab3 = st.tabs(["📊 DBU Spend by SKU", "🔍 Cluster Right-Sizing", "💡 Predictive Optimization ROI"])

with tab1:
    st.subheader("Daily DBU Consumption across Workload Types")
    # Mock aggregated time-series data matching system.billing.usage
    dates = pd.date_range(end=datetime.date.today(), periods=14)
    df_spend = pd.DataFrame({
        "Date": dates,
        "Automated Jobs": [350 + i * 12 for i in range(14)],
        "Serverless SQL": [210 + i * 8 for i in range(14)],
        "Interactive / All-Purpose": [120 - i * 3 for i in range(14)],
        "DLT Pipelines": [90 + i * 4 for i in range(14)]
    }).set_index("Date")
    st.area_chart(df_spend)

with tab2:
    st.subheader("Zombie & Underutilized Interactive Clusters")
    st.info("Interactive clusters with < 15% average CPU over the last 7 days recommended for auto-termination reduction.")
    zombie_clusters = pd.DataFrame([
        {"Cluster Name": "adhoc-analyst-pool-01", "Owner": "dev_analyst@example.com", "Node Type": "Standard_E8ds_v5", "Max Workers": 8, "Avg CPU": "8.4%", "Action": "Reduce Auto-Stop to 10 min"},
        {"Cluster Name": "feature-eng-scratch", "Owner": "ml_engineer@example.com", "Node Type": "Standard_D16ds_v5", "Max Workers": 4, "Avg CPU": "11.2%", "Action": "Migrate to Single-User Job Cluster"},
        {"Cluster Name": "legacy-etl-sandbox", "Owner": "contractor@example.com", "Node Type": "Standard_D8ds_v5", "Max Workers": 6, "Avg CPU": "4.1%", "Action": "Terminate Immediately (Zero Activity)"}
    ])
    st.dataframe(zombie_clusters, use_container_width=True)

with tab3:
    st.subheader("Predictive Optimization: Automated Compaction & VACUUM Savings")
    st.success("Predictive Optimization automatically coalesced 412,000 small files into 1,840 optimized Parquet files, improving query read latency by 4.2x.")
    compaction_stats = pd.DataFrame({
        "Metric": ["Total Small Files Eliminated", "Tombstoned Parquet Cleaned (VACUUM)", "Storage Reclaimed (TB)", "Avg Query Read Speedup"],
        "Value": ["412,890 files", "184,200 files", "14.8 TB", "4.2x faster scan"]
    })
    st.table(compaction_stats)
