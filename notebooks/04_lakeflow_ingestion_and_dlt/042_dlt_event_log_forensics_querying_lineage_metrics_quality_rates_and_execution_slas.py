# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # 042. DLT Event Log Forensics: Querying Lineage, Metrics, Quality Rates & Execution SLAs
# MAGIC **Module**: Module 04: Lakeflow Ingestion, Auto Loader & Declarative Pipelines (DLT)
# MAGIC **Mastery Level**: `Advanced` | **Verification Tier**: `T2 Local-executable`
# MAGIC **Target Platform**: Databricks Runtime 15.4+ LTS | Apache Spark 3.5+ | Unity Catalog | Delta Lake 3.2
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏢 Enterprise Business Scenario
# MAGIC A regulatory audit requires generating an SLA compliance report detailing data quality pass/drop rates across all Delta Live Tables pipelines for the past 90 days.
# MAGIC
# MAGIC ### 🎯 Engineering Objective
# MAGIC Persist DLT-schema JSON telemetry inside a Delta event-log table, parse nested JSON expectations via Spark SQL (`get_json_object`), and compute per-flow pass rates and SLA breach alerts.
# MAGIC
# MAGIC ### 🏛️ Architectural Context & Under the Hood Mechanics
# MAGIC DLT stores flow telemetry (`flow_progress`, data quality expectations, SLA durations) in a Delta table queryable via `event_log('<pipeline_id>')`. Locally we write identical nested JSON event records into Delta and execute the forensic Spark SQL aggregation.
# COMMAND ----------

import json
import tempfile
from pathlib import Path
# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Forensic Parsing of DLT Event Log JSON & Data Quality SLA Calculation
# MAGIC
# MAGIC Write synthetic DLT `flow_progress` event rows to a Delta table, extract nested expectation pass/drop counts with Spark SQL, and detect SLA quality breaches.
# COMMAND ----------

lab_dir = Path(tempfile.mkdtemp(prefix="hb_042_", dir=globals().get("HANDBOOK_TMP_DIR")))
event_log_path = str(lab_dir / "dlt_system_events")

raw_events = [
    (
        "2026-11-20T08:00:00Z",
        "flow_progress",
        "orders_silver",
        json.dumps(
            {
                "flow_progress": {
                    "metrics": {"num_output_rows": 980},
                    "data_quality": {"dropped_records": 20, "expectations": [{"name": "valid_amt", "passed": 980, "failed": 20}]},
                }
            }
        ),
    ),
    (
        "2026-11-20T09:00:00Z",
        "flow_progress",
        "payments_silver",
        json.dumps(
            {
                "flow_progress": {
                    "metrics": {"num_output_rows": 500},
                    "data_quality": {"dropped_records": 150, "expectations": [{"name": "valid_iban", "passed": 500, "failed": 150}]},
                }
            }
        ),
    ),
]
spark.createDataFrame(raw_events, ["timestamp", "event_type", "flow_name", "details_json"]).write.format(
    "delta"
).save(event_log_path)
spark.sql(f"CREATE TABLE t042_event_log USING DELTA LOCATION '{event_log_path}'")

sla_df = spark.sql("""
    SELECT
        flow_name,
        CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS BIGINT) AS output_rows,
        CAST(get_json_object(details_json, '$.flow_progress.data_quality.dropped_records') AS BIGINT) AS dropped_rows,
        ROUND(
            CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS DOUBLE) * 100.0
            / (
                CAST(get_json_object(details_json, '$.flow_progress.metrics.num_output_rows') AS DOUBLE)
                + CAST(get_json_object(details_json, '$.flow_progress.data_quality.dropped_records') AS DOUBLE)
            ),
            2
        ) AS pass_rate_pct
    FROM t042_event_log
    WHERE event_type = 'flow_progress'
    ORDER BY pass_rate_pct ASC
""")

sla_map = {r["flow_name"]: r["pass_rate_pct"] for r in sla_df.collect()}
print(f"Pipeline Data Quality Pass Rates (%): {sla_map}")
assert sla_map["orders_silver"] == 98.0
assert sla_map["payments_silver"] < 80.0
# COMMAND ----------

# MAGIC %md
# MAGIC ### 📌 Production Invariants & Key Takeaways
# MAGIC
# MAGIC - **Single Source of Observability**: The DLT event log contains complete execution, metric, and quality history.
# MAGIC - **Audit Reports**: Easily query dropped record counts and expectation pass rates in standard SQL.
# MAGIC - **Lineage Tracking**: Graph relationships between datasets are recorded directly inside event-log metadata.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎓 Architect Interview Questions & Defense
# MAGIC
# MAGIC 1. How do you query the Delta Live Tables event log to find which expectations had the highest failure rates?
# MAGIC 2. What information is captured in `details:flow_progress` within the DLT event log?
