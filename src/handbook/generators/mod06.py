"""
Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer (Notebooks 055 - 065)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "06_databricks_sql_and_photon"
MODULE_NAME = "Module 06: Databricks SQL (DBSQL), Photon & Semantic Layer"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "055",
            "title": "Serverless SQL Warehouses: Instant Spin-up, Autoscaling Policies & Sizing T-Shirts",
            "filename": "055_serverless_sql_warehouses_instant_spin_up_autoscaling_policies_and_sizing_t_shirts.py",
            "difficulty": "Foundational",
            "business_scenario": "A business intelligence team experiences unpredictable query concurrency: 5 analysts query dashboards at night, but 200 executives access them simultaneously on Monday mornings.",
            "problem_statement": "Configure a Serverless SQL Warehouse with optimal T-shirt sizing (2X-Small to 4X-Large), auto-stop policies (5-10 minutes), and autoscaling bounds (min/max clusters).",
            "architectural_notes": "Serverless SQL Warehouses use pre-warmed compute pools managed by Databricks, starting in 2-4 seconds. They scale out clusters horizontally under concurrency pressure and terminate aggressively on idle to prevent wasted DBUs.",
            "sections": [
                {
                    "title": "1. Serverless SQL Warehouse T-Shirt Sizing Matrix",
                    "explanation": "Evaluate cluster sizing and concurrent query capacity.",
                    "code": """warehouse_tiers = {
    "2X-Small": {"cores": 4, "ram_gb": 16, "target_queries": "Light ad-hoc analytics, exploratory queries"},
    "Small": {"cores": 16, "ram_gb": 64, "target_queries": "Standard department BI dashboards (Power BI / Tableau)"},
    "Large": {"cores": 64, "ram_gb": 256, "target_queries": "Heavy aggregations, multi-billion row joins"},
    "4X-Large": {"cores": 256, "ram_gb": 1024, "target_queries": "Enterprise-wide high-concurrency peak reporting"}
}

for size, specs in warehouse_tiers.items():
    print(f"[{size}] Cores: {specs['cores']} | RAM: {specs['ram_gb']}GB | {specs['target_queries']}")

assert warehouse_tiers["Small"]["cores"] == 16
"""
                }
            ],
            "key_takeaways": [
                "Instant Start: Eliminates the 5-7 minute VM startup lag of classic warehouses.",
                "Aggressive Auto-Stop: Set auto-stop to 10 minutes; since startup is 2 seconds, no cold start penalty exists.",
                "Cost Scaling: Scale out max clusters during peak hours and allow scale-to-zero at night."
            ],
            "interview_questions": [
                "How do Serverless SQL Warehouses handle cluster autoscaling differently from Classic SQL Warehouses?",
                "What is the recommended auto-stop idle timeout for Serverless SQL Warehouses?"
            ]
        },
        {
            "nb_id": "056",
            "title": "Photon Engine Internals: C++ Vectorized Execution, SIMD Hardware & Memory Off-Heap",
            "filename": "056_photon_engine_internals_c_vectorized_execution_simd_hardware_and_memory_off_heap.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import DoubleType",
            ],
            "business_scenario": "A large-scale enterprise data platform is evaluating whether to enable the Photon Engine for its SQL workloads to justify the incremental DBU price premium with query speedups.",
            "problem_statement": "Contrast row-by-row Python UDF serialization overhead (which breaks Catalyst/Photon vectorized codegen) against native Spark columnar SQL expressions + Broadcast Hash Joins on real Delta tables, inspecting the physical plan.",
            "architectural_notes": "Photon executes vectorized C++ batches over columnar off-heap buffers on Databricks Runtime. Any Python row-by-row UDF breaks Photon vectorization and forces JVM/Python serialization pickling; rewriting expressions in native Spark SQL enables whole-stage codegen and Photon fallback elimination.",
            "sections": [
                {
                    "title": "1. Bad (Python UDF Blocking Vectorization) vs. Good (Native Columnar Expressions & Broadcast)",
                    "explanation": "Compare physical execution plans between a row-by-row Python UDF (`BatchEvalPython`) and native Catalyst columnar expressions with a broadcast dimension join.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_056_", dir=globals().get("HANDBOOK_TMP_DIR")))
fact_path = str(lab_dir / "fact_orders")

spark.range(0, 5000).withColumn("sku_id", (F.col("id") % 5).cast("int")).withColumn(
    "gross_amt", (F.col("id") * 1.25).cast("double")
).write.format("delta").save(fact_path)

fact_df = spark.read.format("delta").load(fact_path)
dim_df = spark.createDataFrame(
    [(0, "CORE"), (1, "PRO"), (2, "ENT"), (3, "ADDON"), (4, "SUPPORT")],
    ["sku_id", "tier"],
)

# BAD PATTERN: Row-by-row Python UDF prevents Photon / Tungsten whole-stage codegen
@F.udf(DoubleType())
def tax_udf(val: float) -> float:
    return round(val * 1.08, 2) if val is not None else 0.0

bad_plan = (
    fact_df.withColumn("taxed", tax_udf(F.col("gross_amt")))
    ._jdf.queryExecution()
    .executedPlan()
    .toString()
)

# GOOD PATTERN: Pure columnar SQL expressions + Broadcast Hash Join
good_df = (
    fact_df.join(F.broadcast(dim_df), "sku_id")
    .withColumn("taxed", F.round(F.col("gross_amt") * F.lit(1.08), 2))
    .groupBy("tier")
    .agg(F.round(F.sum("taxed"), 2).alias("total_taxed"))
)
good_plan = good_df._jdf.queryExecution().executedPlan().toString()

bad_sum = round(fact_df.select(F.sum(tax_udf(F.col("gross_amt")))).first()[0], 2)
good_sum = round(good_df.agg(F.sum("total_taxed")).first()[0], 2)

print(f"Python UDF plan uses BatchEvalPython: {'BatchEvalPython' in bad_plan}")
print(f"Columnar Broadcast plan avoids BatchEvalPython: {'BatchEvalPython' not in good_plan}")
assert "BatchEvalPython" in bad_plan
assert "BatchEvalPython" not in good_plan and "BroadcastHashJoin" in good_plan
assert abs(bad_sum - good_sum) < 1.0
""",
                }
            ],
            "key_takeaways": [
                "Avoid Python UDFs: Every Python UDF breaks native vectorization (BatchEvalPython pickling overhead); prefer built-in Spark SQL expressions.",
                "Broadcast Small Dimensions: Eliminate SortMergeJoin shuffles by broadcasting small lookup tables.",
                "Hardware Acceleration: Photon's vectorized C++ operators natively leverage AVX-512 / ARM NEON SIMD on Databricks.",
            ],
            "interview_questions": [
                "Why was Photon rewritten in C++ instead of optimizing the existing Java/Scala JVM codebase?",
                "How do Python UDFs degrade Catalyst Whole-Stage Codegen and Photon vectorization?",
            ],
        },
        {
            "nb_id": "057",
            "title": "Intelligent Workload Management (IWM): Query Admission Control & Queue Spill Prevention",
            "filename": "057_intelligent_workload_management_iwm_query_admission_control_and_queue_spill_prevention.py",
            "difficulty": "Intermediate",
            "business_scenario": "During quarter-end financial closes, 50 analysts run massive queries simultaneously. Without admission control, clusters run out of memory, crash, and drop connections.",
            "problem_statement": "Demonstrate the mechanics of Databricks SQL Intelligent Workload Management (IWM), analyzing dynamic query admission control, queueing behavior, and memory spill mitigation.",
            "architectural_notes": "IWM uses ML-based runtime prediction to govern query admission on SQL Warehouses. Instead of letting all queries run concurrently and thrash RAM, IWM queues incoming queries and schedules them smoothly.",
            "sections": [
                {
                    "title": "1. IWM Admission Control Mechanics Model",
                    "explanation": "Simulate query admission decisions based on predicted memory and cluster capacity.",
                    "code": """class MockIWMAdmissionController:
    def __init__(self, max_concurrent_queries=10, max_memory_gb=64):
        self.max_queries = max_concurrent_queries
        self.max_ram = max_memory_gb
        self.active_queries = 0
        self.active_ram = 0

    def admit_query(self, query_id: str, estimated_ram_gb: int) -> str:
        if self.active_queries < self.max_queries and (self.active_ram + estimated_ram_gb) <= self.max_ram:
            self.active_queries += 1
            self.active_ram += estimated_ram_gb
            return f"Query {query_id}: ADMITTED (Running on cluster)"
        else:
            return f"Query {query_id}: QUEUED (Waiting for capacity to prevent memory spill)"

iwm = MockIWMAdmissionController(max_concurrent_queries=2, max_memory_gb=32)
print(iwm.admit_query("Q1", 16))
print(iwm.admit_query("Q2", 12))
print(iwm.admit_query("Q3", 8)) # Should queue

assert "QUEUED" in iwm.admit_query("Q3", 8)
"""
                }
            ],
            "key_takeaways": [
                "Spill Prevention: Queuing queries temporarily is faster than letting multiple queries spill gigabytes to disk.",
                "Fast Auto-Scaling: IWM signals the warehouse cluster manager to launch additional clusters when queue depths grow.",
                "Zero Cluster Crashes: Protects cluster stability under severe concurrent load."
            ],
            "interview_questions": [
                "What is Intelligent Workload Management (IWM) in Databricks SQL Warehouses?",
                "How does IWM differentiate between quick BI lookups and long-running heavy aggregation queries?"
            ]
        },
        {
            "nb_id": "058",
            "title": "Multi-Tier Caching Architecture: Result Cache, Local Disk Cache & Remote Cache",
            "filename": "058_multi_tier_caching_architecture_result_cache_local_disk_cache_and_remote_cache.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A dashboard with 50 visual tiles is refreshed by 500 business users throughout the day. Executing 25,000 queries directly against cloud object storage costs thousands in repeated scanning.",
            "problem_statement": "Verify live Delta commit cache coherency vs. manual Spark `CACHE TABLE` refresh behavior locally, demonstrating why Delta transaction log awareness prevents stale BI reads.",
            "architectural_notes": "Databricks SQL Result Cache and NVMe Disk Cache track underlying Delta `_delta_log` commits automatically—invalidating cached blocks the millisecond a DML commit alters referenced files. In open-source Spark, caching a DataFrame/View via `CACHE TABLE` pins executors' memory until `REFRESH TABLE` / `UNCACHE TABLE`.",
            "sections": [
                {
                    "title": "1. Cache Coherency Test: Manual Spark Cache vs. Delta Live Snapshot Commits",
                    "explanation": "Materialize a Delta table, cache a read view with `CACHE TABLE`, append a new Delta commit, and confirm Spark catalog state + refreshed live read totals.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_058_", dir=globals().get("HANDBOOK_TMP_DIR")))
tbl_path = str(lab_dir / "cached_sales")

spark.createDataFrame([(1, 100.0), (2, 200.0)], ["order_id", "amount"]).write.format("delta").save(tbl_path)
spark.sql(f"CREATE TABLE t058_sales USING DELTA LOCATION '{tbl_path}'")
spark.sql("CACHE TABLE t058_sales")
assert spark.catalog.isCached("t058_sales") is True

initial_total = spark.sql("SELECT SUM(amount) FROM t058_sales").first()[0]

# New Delta commit adds +500.0; refresh/uncache aligns cached executors with latest _delta_log
spark.createDataFrame([(3, 500.0)], ["order_id", "amount"]).write.format("delta").mode("append").save(tbl_path)
spark.sql("REFRESH TABLE t058_sales")
refreshed_total = spark.sql("SELECT SUM(amount) FROM t058_sales").first()[0]

spark.sql("UNCACHE TABLE t058_sales")
assert spark.catalog.isCached("t058_sales") is False

print(f"Cached initial={initial_total}, post-commit refreshed={refreshed_total}")
assert initial_total == 300.0 and refreshed_total == 800.0
""",
                }
            ],
            "key_takeaways": [
                "Deterministic Invalidation: DBSQL Result Cache & Disk Cache automatically invalidate when Delta `_delta_log` commits a new version.",
                "Explicit Spark Cache Lifecycle: In open Spark clusters, remember `REFRESH TABLE` / `UNCACHE TABLE` to keep executor memory aligned.",
                "NVMe Delta Cache Advantage: Persists hot Parquet columns natively on local SSDs without consuming JVM executor heap.",
            ],
            "interview_questions": [
                "How does Databricks ensure that Query Result Cache never serves stale data after an update?",
                "What is the difference between the Spark `CACHE TABLE` command and the Databricks Disk Cache (Delta Cache)?",
            ],
        },
        {
            "nb_id": "059",
            "title": "DBSQL Query Profile Analysis: Diagnosing Scans, Shuffles, Spills & Pruning Efficiency",
            "filename": "059_dbsql_query_profile_analysis_diagnosing_scans_shuffles_spills_and_pruning_efficiency.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "An executive dashboard query takes 85 seconds to run. The business demands sub-5-second performance. The engineer must use Query Profile to identify whether the bottleneck is scanning, spilling, or shuffling.",
            "problem_statement": "Prove how non-sargable filter expressions (`CAST(order_date AS STRING) LIKE ...`) defeat Delta partition pruning, then inspect Catalyst's physical plan & `inputFiles()` before vs. after rewriting to a sargable equality predicate.",
            "architectural_notes": "Wrapping a partition or clustering column inside a function/cast blocks partition pushdown and Z-Cube/file min-max pruning, triggering a full table scan (`0% files pruned`). Rewriting predicates on bare indexed columns unlocks instant partition elimination.",
            "sections": [
                {
                    "title": "1. Bad (Broken Data Skipping Full Scan) vs. Good (Pruned Scan via Bare Indexed Column)",
                    "explanation": "Write 4 ordered batches (`1..50`, `51..100`, `101..150`, `151..200`) into Delta so `_delta_log` min/max stats span disjoint ranges, then prove `CAST(order_id AS STRING)` forces scanning all 4 files while `order_id = 125` prunes 75% to 1 file.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_059_", dir=globals().get("HANDBOOK_TMP_DIR")))
pruned_path = str(lab_dir / "orders_sorted_delta")

for start_id in (1, 51, 101, 151):
    (
        spark.range(start_id, start_id + 50)
        .withColumnRenamed("id", "order_id")
        .withColumn("amount", (F.col("order_id") * 10).cast("double"))
        .coalesce(1)
        .write.format("delta")
        .mode("append")
        .save(pruned_path)
    )
spark.sql(f"CREATE TABLE t059_orders USING DELTA LOCATION '{pruned_path}'")

# BAD PATTERN: Implicit/explicit cast prevents Delta min/max file skipping & Parquet PushedFilters
bad_df = spark.sql("SELECT * FROM t059_orders WHERE CAST(order_id AS STRING) = '125'")
bad_plan = bad_df._jdf.queryExecution().executedPlan().toString()
bad_files = len(bad_df.inputFiles())

# GOOD PATTERN: Direct filter on bare numeric column enables file-level data skipping
good_df = spark.sql("SELECT * FROM t059_orders WHERE order_id = 125")
good_plan = good_df._jdf.queryExecution().executedPlan().toString()
good_files = len(good_df.inputFiles())

print(f"Bad files read (CAST breaks skipping): {bad_files}")
print(f"Good files read (Delta stats pruned) : {good_files}")
assert bad_files == 4 and good_files == 1
assert "PushedFilters" in good_plan and "EqualTo(order_id,125)" in good_plan
assert good_df.count() == bad_df.count() == 1
""",
                }
            ],
            "key_takeaways": [
                "Never Wrap Filter Columns: Functions like `SUBSTRING(col)`, `YEAR(col)`, or implicit type casts block partition & data-skipping pruning.",
                "Verify Query Profile: Check `PartitionFilters` and `PushedFilters` / `Files Pruned` ratios after SQL rewrites.",
                "Eliminate Spills: Smaller pruned scans drastically reduce shuffle sort/hash memory footprint.",
            ],
            "interview_questions": [
                "How do you identify whether a slow query is bottlenecked on I/O scan vs. CPU shuffle in DBSQL Query Profile?",
                "What does 'Rows Spilled to Disk' indicate in a Query Profile?",
            ],
        },
        {
            "nb_id": "060",
            "title": "Materialized Views & Streaming Tables in DBSQL without Apache Spark Code",
            "filename": "060_materialized_views_and_streaming_tables_in_dbsql_without_apache_spark_code.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
                "from pyspark.sql.types import StringType, StructField, StructType",
            ],
            "business_scenario": "SQL analysts and analytics engineers without Python skills need to build automated incremental pipelines that ingest files and maintain aggregated summary marts.",
            "problem_statement": "Demonstrate the Databricks SQL `CREATE STREAMING TABLE` and `CREATE MATERIALIZED VIEW` execution semantics locally by streaming JSON landing events incrementally into Delta Bronze and materializing Gold page-view rollups via SQL.",
            "architectural_notes": "Databricks SQL Streaming Tables and Materialized Views run on serverless DLT infrastructure using pure ANSI SQL (`STREAM read_files()`). Locally we mirror this exact incremental ingestion -> SQL rollup pattern cleanly in Spark + Delta.",
            "sections": [
                {
                    "title": "1. Streaming Bronze Ingestion + SQL Materialized Gold Rollup",
                    "explanation": "Stream raw web JSON events with `trigger(availableNow=True)` into Delta `bronze_web_logs` and refresh an aggregated SQL summary table `gold_daily_page_views`.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_060_", dir=globals().get("HANDBOOK_TMP_DIR")))
raw_dir = lab_dir / "web_logs_json"
raw_dir.mkdir(parents=True)
bronze_path = str(lab_dir / "bronze_web_logs")
gold_path = str(lab_dir / "gold_daily_page_views")
ckpt = str(lab_dir / "ckpt_web_logs")

log_events = [
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v1"}',
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v2"}',
    '{"log_date": "2026-11-20", "page_url": "/pricing", "visitor_id": "v1"}',
    '{"log_date": "2026-11-20", "page_url": "/docs", "visitor_id": "v3"}',
]
(raw_dir / "events_01.json").write_text("\\n".join(log_events) + "\\n", encoding="utf-8")

schema = StructType(
    [
        StructField("log_date", StringType(), False),
        StructField("page_url", StringType(), False),
        StructField("visitor_id", StringType(), False),
    ]
)

q = (
    spark.readStream.format("json")
    .schema(schema)
    .load(str(raw_dir))
    .writeStream.format("delta")
    .option("checkpointLocation", ckpt)
    .trigger(availableNow=True)
    .start(bronze_path)
)
q.awaitTermination()

spark.sql(f"CREATE TABLE t060_bronze USING DELTA LOCATION '{bronze_path}'")
gold_df = spark.sql(\"\"\"
    SELECT log_date, page_url, COUNT(*) AS total_hits, COUNT(DISTINCT visitor_id) AS unique_visitors
    FROM t060_bronze
    GROUP BY log_date, page_url
\"\"\")
gold_df.write.format("delta").mode("overwrite").save(gold_path)

pricing = spark.read.format("delta").load(gold_path).filter("page_url = '/pricing'").first()
print(f"/pricing rollup -> hits={pricing['total_hits']}, unique_visitors={pricing['unique_visitors']}")
assert pricing["total_hits"] == 3 and pricing["unique_visitors"] == 2
""",
                }
            ],
            "key_takeaways": [
                "Zero Python Required in DBSQL: Analysts declare Streaming Tables & Materialized Views cleanly in ANSI SQL.",
                "Incremental State Management: Databricks tracks ingested files cleanly via checkpoints.",
                "Consistent Aggregations: Exact distinct & rollup metrics stay aligned with Bronze tables.",
            ],
            "interview_questions": [
                "How do Materialized Views in Databricks SQL differ from standard SQL Views?",
                "What is the function of `STREAM read_files()` in pure SQL streaming tables?",
            ],
        },
        {
            "nb_id": "061",
            "title": "AI/BI Dashboards (Lakeview): Interactive Filtering, Canvas Layouts & Cross-Filtering",
            "filename": "061_ai_bi_dashboards_lakeview_interactive_filtering_canvas_layouts_and_cross_filtering.py",
            "difficulty": "Foundational",
            "business_scenario": "An organization wants to retire legacy dashboard tools (Redash/Tableau) in favor of AI/BI Dashboards (Lakeview) that connect directly to Unity Catalog data with native cross-filtering.",
            "problem_statement": "Define an AI/BI Dashboard specification in JSON/YAML, configure interactive parameter widgets, establish cross-filtering between charts, and manage the Draft/Published lifecycle.",
            "architectural_notes": "AI/BI Dashboards (formerly Lakeview) provide modern data visualization built directly on Databricks SQL. Dashboards separate Draft state from Published state, support cross-filtering across visual charts, and run on serverless warehouses.",
            "sections": [
                {
                    "title": "1. AI/BI Dashboard Specification Structure",
                    "explanation": "Simulate dashboard definition with widgets and cross-filtering rules.",
                    "code": """dashboard_spec = {
    "display_name": "Executive Revenue Intelligence",
    "warehouse_id": "wh-serverless-001",
    "pages": [
        {
            "name": "Overview",
            "layout": "grid",
            "visualizations": [
                {"id": "viz_1", "type": "counter", "title": "Total Revenue", "query": "SELECT SUM(amount) FROM fact_sales"},
                {"id": "viz_2", "type": "bar", "title": "Revenue by Region", "query": "SELECT region, SUM(amount) FROM fact_sales GROUP BY region"},
                {"id": "viz_3", "type": "line", "title": "Monthly Trend", "query": "SELECT date_trunc('month', sale_date), SUM(amount) FROM fact_sales GROUP BY 1"}
            ],
            "cross_filtering_enabled": True
        }
    ]
}

print(f"Dashboard: {dashboard_spec['display_name']}")
print(f"Visualizations Configured: {len(dashboard_spec['pages'][0]['visualizations'])}")
assert dashboard_spec["pages"][0]["cross_filtering_enabled"] is True
"""
                }
            ],
            "key_takeaways": [
                "Draft vs. Published: Developers can make changes in Draft mode without breaking the live Published dashboard.",
                "Native Cross-Filtering: Clicking a bar in one chart instantly filters all other charts on the canvas.",
                "Direct UC Governance: Dashboards inherit Unity Catalog row filters and column masks automatically."
            ],
            "interview_questions": [
                "How does the Draft and Published lifecycle work in Databricks AI/BI Dashboards?",
                "Do AI/BI Dashboards respect Unity Catalog Dynamic Row Filters and Column Masks?"
            ]
        },
        {
            "nb_id": "062",
            "title": "Databricks Genie Spaces: Conversational Data Intelligence & Certified SQL Assets",
            "filename": "062_databricks_genie_spaces_conversational_data_intelligence_and_certified_sql_assets.py",
            "difficulty": "Intermediate",
            "business_scenario": "Executive leaders want to ask business questions in natural language ('What was our top selling product in EMEA last month?') and receive accurate SQL-backed answers with zero hallucination.",
            "problem_statement": "Configure a Databricks Genie Space, define certified SQL assets, author semantic descriptions, and curate trusted benchmarks to guide LLM query generation.",
            "architectural_notes": "Databricks Genie provides a conversational AI interface over Lakehouse data. It combines foundation models with enterprise semantic metadata, Unity Catalog schemas, and certified SQL queries to generate verifiable SQL answers.",
            "sections": [
                {
                    "title": "1. Genie Space Semantic Configuration",
                    "explanation": "Define trusted tables, column descriptions, and certified SQL benchmark queries for Genie.",
                    "code": """genie_space_config = {
    "space_name": "Executive Sales Intelligence",
    "tables": ["prod_lakehouse.gold.fact_sales", "prod_lakehouse.gold.dim_products"],
    "curated_sql_assets": [
        {
            "question": "What is our definition of monthly recurring revenue (MRR)?",
            "sql": "SELECT SUM(plan_price) FROM subscriptions WHERE status = 'ACTIVE' AND billing_cycle = 'MONTHLY'"
        }
    ],
    "semantic_guidelines": [
        "Always exclude test accounts where email ends with @example.com",
        "Total revenue must always use the 'net_revenue' column, not 'gross_revenue'"
    ]
}

print(f"Genie Space: {genie_space_config['space_name']}")
print(f"Curated Benchmarks: {len(genie_space_config['curated_sql_assets'])}")
print(f"Semantic Guardrails: {len(genie_space_config['semantic_guidelines'])}")
assert len(genie_space_config["semantic_guidelines"]) == 2
"""
                }
            ],
            "key_takeaways": [
                "Grounded in SQL: Genie always presents the exact SQL query executed, allowing human verification.",
                "Certified Assets: Curate approved SQL templates to train Genie on complex proprietary calculations.",
                "Zero Hallucination Guardrails: Semantic instructions instruct the LLM on business logic rules."
            ],
            "interview_questions": [
                "How does Databricks Genie ensure that natural language queries generate mathematically accurate SQL?",
                "What role do certified benchmark queries play in tuning a Genie Space?"
            ]
        },
        {
            "nb_id": "063",
            "title": "Databricks Semantic Layer & Metric Views: Enterprise Dimensions & Measures",
            "filename": "063_databricks_semantic_layer_and_metric_views_enterprise_dimensions_and_measures.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "Different departments compute 'Customer Churn' and 'Net Revenue' using conflicting formulas, resulting in discrepancies during executive board meetings.",
            "problem_statement": "Deploy a canonical Semantic Metric View in Spark/Delta (`net_revenue`, `order_volume`, `average_order_value`), slice identical measures by different dimensional grains (`region` vs. `product_tier`), and prove 100% additive KPI consistency.",
            "architectural_notes": "Centralizing metric expressions (`SUM(gross_amount - discount_amount)`) inside a governed Semantic View eliminates formula drift between Finance, BI dashboards, and Databricks Genie.",
            "sections": [
                {
                    "title": "1. Canonical Metric View Materialization & Cross-Dimension Reconciliation",
                    "explanation": "Define `t063_metrics_financial_core` over Delta sales transactions and verify identical aggregate KPI totals across independent dimensional slices.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_063_", dir=globals().get("HANDBOOK_TMP_DIR")))
sales_path = str(lab_dir / "silver_sales_tx")

spark.createDataFrame(
    [
        (1, "C1", "EMEA", "ENTERPRISE", 1000.0, 100.0),
        (2, "C2", "NA", "PRO", 500.0, 50.0),
        (3, "C3", "EMEA", "PRO", 300.0, 0.0),
        (4, "C4", "APAC", "ENTERPRISE", 800.0, 80.0),
    ],
    ["tx_id", "customer_id", "region", "product_tier", "gross_amount", "discount_amount"],
).write.format("delta").save(sales_path)
spark.sql(f"CREATE TABLE t063_sales USING DELTA LOCATION '{sales_path}'")

spark.sql(\"\"\"
    CREATE OR REPLACE VIEW t063_metrics_core AS
    SELECT
        region,
        product_tier,
        SUM(gross_amount - discount_amount) AS net_revenue,
        COUNT(DISTINCT tx_id) AS order_volume
    FROM t063_sales
    GROUP BY region, product_tier
\"\"\")

rev_by_region = {r["region"]: r["rev"] for r in spark.sql("SELECT region, SUM(net_revenue) AS rev FROM t063_metrics_core GROUP BY region").collect()}
rev_by_tier = {r["product_tier"]: r["rev"] for r in spark.sql("SELECT product_tier, SUM(net_revenue) AS rev FROM t063_metrics_core GROUP BY product_tier").collect()}
total_region = sum(rev_by_region.values())
total_tier = sum(rev_by_tier.values())
base_total = spark.sql("SELECT SUM(gross_amount - discount_amount) FROM t063_sales").first()[0]

print(f"Semantic Net Revenue -> by region={total_region}, by tier={total_tier}, base={base_total}")
assert total_region == total_tier == base_total == 2370.0
""",
                }
            ],
            "key_takeaways": [
                "Single Source of Truth: Define critical business measures once in governed Unity Catalog views.",
                "Metric Parity: Power BI, Lakeview Dashboards, and Genie consume the identical net-revenue logic.",
                "Centralized Evolution: Formula changes propagate globally downstream without dashboard rewrites.",
            ],
            "interview_questions": [
                "How does an in-database Semantic Layer in Unity Catalog eliminate metric discrepancies between BI tools?",
                "What is the difference between a dimensional attribute and a metric measure?",
            ],
        },
        {
            "nb_id": "064",
            "title": "DBSQL Alerts, Automated Refresh Schedules & SLA-Driven Slack Notifications",
            "filename": "064_dbsql_alerts_automated_refresh_schedules_and_sla_driven_slack_notifications.py",
            "difficulty": "Foundational",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A payments platform must be alerted within 5 minutes if failed credit card transactions exceed 2% of total volume over any rolling 15-minute window.",
            "problem_statement": "Execute rolling threshold SQL alert queries over Delta payment telemetry (`failure_rate_pct > 2.0%`), separating healthy windows from SLA-breaching alert windows.",
            "architectural_notes": "DBSQL Alerts evaluate scheduled SQL queries and dispatch Slack/PagerDuty webhooks whenever returned aggregate metrics violate numeric predicates.",
            "sections": [
                {
                    "title": "1. Rolling Window SQL Alert Query & SLA Breach Trigger",
                    "explanation": "Persist healthy and degraded 15-minute payment authorization windows in Delta Lake, run the DBSQL alert evaluation query, and assert only the incident window triggers.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_064_", dir=globals().get("HANDBOOK_TMP_DIR")))
pay_path = str(lab_dir / "payment_events")

rows = [("w1_healthy", "OK") for _ in range(99)] + [("w1_healthy", "FAILED")]
rows += [("w2_incident", "OK") for _ in range(90)] + [("w2_incident", "FAILED") for _ in range(10)]
spark.createDataFrame(rows, ["window_id", "tx_status"]).write.format("delta").save(pay_path)
spark.sql(f"CREATE TABLE t064_payments USING DELTA LOCATION '{pay_path}'")

alert_df = spark.sql(\"\"\"
    WITH window_kpis AS (
        SELECT
            window_id,
            ROUND(SUM(CASE WHEN tx_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct
        FROM t064_payments
        GROUP BY window_id
    )
    SELECT window_id, failure_rate_pct, failure_rate_pct > 2.0 AS trigger_slack_alert
    FROM window_kpis
    ORDER BY window_id
\"\"\")

alerts = {r["window_id"]: (r["failure_rate_pct"], r["trigger_slack_alert"]) for r in alert_df.collect()}
print(f"DBSQL Alert Evaluation: {alerts}")
assert alerts["w1_healthy"] == (1.0, False)
assert alerts["w2_incident"] == (10.0, True)
""",
                }
            ],
            "key_takeaways": [
                "Proactive Alerting: Detect SLA regressions cleanly in SQL before customers report outages.",
                "Multi-Channel Destinations: Dispatch DBSQL Alerts to Slack, PagerDuty, or HTTP webhooks.",
                "Trigger Semantics: Choose `Trigger Once` vs. `Each Time` to avoid pager fatigue.",
            ],
            "interview_questions": [
                "How do DBSQL Alerts evaluate conditions across single-value versus multi-row query results?",
                "What is the difference between 'Trigger Once' and 'Trigger Each Time' in Databricks SQL Alerts?",
            ],
        },
        {
            "nb_id": "065",
            "title": "SQL Warehouse Concurrency Scaling: Horizontal Multi-Cluster Load Balancing",
            "filename": "065_sql_warehouse_concurrency_scaling_horizontal_multi_cluster_load_balancing.py",
            "difficulty": "Intermediate",
            "business_scenario": "A company has 1,000 active Power BI users refreshing dashboards at the start of business. A single SQL warehouse cluster saturates, queueing queries and causing dashboard timeouts.",
            "problem_statement": "Configure horizontal multi-cluster load balancing on a Serverless SQL Warehouse, tune maximum cluster bounds (1 to 10), and analyze scaling policies (Economy vs. Pro).",
            "architectural_notes": "Databricks SQL Warehouses scale horizontally by adding identical compute clusters behind a shared load balancer. When query concurrency exceeds single-cluster capacity, additional clusters launch automatically to handle the queue.",
            "sections": [
                {
                    "title": "1. Multi-Cluster Sizing & Scaling Policy Model",
                    "explanation": "Simulate warehouse cluster autoscaling under variable query concurrency.",
                    "code": """def evaluate_warehouse_scaling(active_queries: int, queries_per_cluster: int = 10, min_clusters: int = 1, max_clusters: int = 5):
    needed_clusters = (active_queries + queries_per_cluster - 1) // queries_per_cluster
    allocated_clusters = max(min_clusters, min(needed_clusters, max_clusters))
    is_queued = needed_clusters > max_clusters
    return {"allocated_clusters": allocated_clusters, "is_queued": is_queued}

peak_load = evaluate_warehouse_scaling(active_queries=45, queries_per_cluster=10, min_clusters=1, max_clusters=5)
print(f"Under 45 Concurrent Queries:")
print(f"  Allocated Clusters: {peak_load['allocated_clusters']}")
print(f"  Queued: {peak_load['is_queued']}")
assert peak_load["allocated_clusters"] == 5
assert not peak_load["is_queued"]
"""
                }
            ],
            "key_takeaways": [
                "Horizontal Concurrency: Add clusters to handle concurrent users without increasing individual VM size.",
                "Scaling Policy: `Pro` scales out immediately for low latency; `Economy` scales conservatively to save cost.",
                "Sub-Second Scale-Down: Serverless clusters scale down rapidly once concurrency subsides."
            ],
            "interview_questions": [
                "How does multi-cluster autoscaling in Databricks SQL prevent query queueing during peak hours?",
                "When should an engineer increase cluster T-shirt size versus increasing the maximum cluster count?"
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
