"""
Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG) (Notebooks 077 - 087)
"""

from pathlib import Path
from handbook.notebooks.builder import build_notebook, write_notebook

MODULE_FOLDER = "08_databricks_apps_and_mosaic_ai"
MODULE_NAME = "Module 08: Databricks Apps & Mosaic AI (GenAI, Vector Search, RAG)"

def generate(base_dir: Path):
    out_dir = base_dir / "notebooks" / MODULE_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        {
            "nb_id": "077",
            "title": "Databricks Apps: Serverless Hosting for Streamlit, Dash, Gradio & FastAPI Applications",
            "filename": "077_databricks_apps_serverless_hosting_for_streamlit_dash_gradio_and_fastapi.py",
            "difficulty": "Intermediate",
            "business_scenario": "Data scientists and engineers need to deploy interactive data applications (Streamlit for internal FinOps, FastAPI for microservices) directly inside the secure workspace perimeter without managing Kubernetes or cloud VMs.",
            "problem_statement": "Deploy and configure a serverless Python web application using Databricks Apps, handling port routing, single sign-on (SSO) authentication, and Unity Catalog data access.",
            "architectural_notes": "Databricks Apps provides serverless container hosting for Python web frameworks (Streamlit, Dash, Gradio, Flask, FastAPI). Apps run securely within the workspace, inherit corporate SSO, and connect to Unity Catalog via auto-injected service credentials.",
            "sections": [
                {
                    "title": "1. Databricks App Architecture & Component Model",
                    "explanation": "Inspect the components of a native Databricks App.",
                    "code": """app_components = {
    "app_yaml": "Configuration manifest specifying command, port, and environment variables",
    "requirements_txt": "Python dependencies installed in the serverless container",
    "app_py": "Application source code (Streamlit / FastAPI)",
    "security": "Automatic corporate SSO authentication; users access via workspace URL"
}

for comp, desc in app_components.items():
    print(f"[{comp}]: {desc}")
assert len(app_components) == 4
"""
                }
            ],
            "key_takeaways": [
                "Serverless Hosting: Zero Kubernetes or Docker management; Databricks manages the container fleet.",
                "Built-In SSO: Users authenticate using standard Databricks login; no manual OAuth boilerplate.",
                "Zero Egress: Data stays within the Databricks perimeter, governed by Unity Catalog."
            ],
            "interview_questions": [
                "What is Databricks Apps and how does it simplify deploying internal data tools compared to standalone web servers?",
                "How does authentication and user identity work in a Databricks App?"
            ]
        },
        {
            "nb_id": "078",
            "title": "Databricks App Manifest (app.yaml), Resource Bindings & Service Principal IAM",
            "filename": "078_databricks_app_manifest_app_yaml_resource_bindings_and_service_principal_iam.py",
            "difficulty": "Intermediate",
            "business_scenario": "A production Databricks App requires access to a Serverless SQL Warehouse and a Vector Search endpoint. Access must be granted to an isolated App Service Principal rather than human developer credentials.",
            "problem_statement": "Author an `app.yaml` manifest specifying resource bindings (SQL Warehouses, Serving Endpoints) and environment variables, verifying automated credential injection.",
            "architectural_notes": "Databricks Apps automatically provisions a dedicated Service Principal for each app. The `app.yaml` manifest binds external workspace resources to the app, granting the App Service Principal least-privilege access.",
            "sections": [
                {
                    "title": "1. Databricks App Manifest Specification",
                    "explanation": "Define `app.yaml` resource bindings and runtime configuration.",
                    "code": """app_manifest_yaml = \"\"\"
command: ["streamlit", "run", "app.py"]
env:
  - name: "DATABRICKS_APP_ENV"
    value: "production"
  - name: "TARGET_CATALOG"
    value: "prod_lakehouse"

resources:
  sql_warehouse:
    id: "wh-serverless-001"
    permission: "CAN_USE"
  serving_endpoint:
    name: "mosaic-rag-serving-endpoint"
    permission: "CAN_QUERY"
\"\"\"

print("Databricks App manifest validated.")
assert "streamlit" in app_manifest_yaml and "app.py" in app_manifest_yaml
"""
                }
            ],
            "key_takeaways": [
                "Resource Binding: Bind SQL Warehouses and Serving Endpoints directly in `app.yaml`.",
                "Dedicated App Identity: Every app runs under its own Service Principal, not user tokens.",
                "Port Mapping: Databricks automatically proxies web traffic to the container's bound port."
            ],
            "interview_questions": [
                "How does `app.yaml` manage permissions for external Databricks resources like SQL Warehouses?",
                "What happens if an app tries to access a table its Service Principal has not been granted permissions to?"
            ]
        },
        {
            "nb_id": "079",
            "title": "Databricks Vector Search: Managed Vector Endpoints & Delta Sync Indexes",
            "filename": "079_databricks_vector_search_managed_vector_endpoints_and_delta_sync_indexes.py",
            "difficulty": "Advanced",
            "business_scenario": "An enterprise search application requires sub-100ms semantic similarity search over 5 million product catalog descriptions. When new products are added or edited in Delta Lake, the vector index must update automatically.",
            "problem_statement": "Provision a Databricks Vector Search endpoint, create a Delta Sync Index that automatically calculates and updates vector embeddings on source Delta table commits, and execute similarity queries.",
            "architectural_notes": "Databricks Vector Search is an enterprise vector database built directly into Unity Catalog. A **Delta Sync Index** continuously tracks changes in a source Delta table via Change Data Feed (CDF), generating embeddings automatically and syncing the vector index in real time.",
            "sections": [
                {
                    "title": "1. Delta Sync Index Architecture & Python Configuration",
                    "explanation": "Configure a continuous vector sync index from a Delta table using `databricks-sdk`.",
                    "code": """vector_index_spec = {
    "endpoint_name": "enterprise_vector_search_endpoint",
    "index_name": "prod_lakehouse.gold.product_vector_index",
    "primary_key": "product_id",
    "index_type": "DELTA_SYNC",
    "source_table": "prod_lakehouse.gold.dim_products",
    "pipeline_type": "CONTINUOUS", # Continuous synchronization from Delta CDF
    "embedding_source_column": "product_description",
    "embedding_model_endpoint_name": "databricks-bge-large-en"
}

print(f"Vector Endpoint: {vector_index_spec['endpoint_name']}")
print(f"Delta Sync Source: {vector_index_spec['source_table']}")
print(f"Auto-Embedding Model: {vector_index_spec['embedding_model_endpoint_name']}")
assert vector_index_spec["index_type"] == "DELTA_SYNC"
"""
                }
            ],
            "key_takeaways": [
                "Continuous Synchronization: Delta Sync automatically updates the vector index when Delta tables commit.",
                "Zero Embedding Pipelines: Databricks computes and embeds vectors automatically from text columns.",
                "Sub-100ms Latency: High-performance HNSW index delivers millisecond vector similarity queries."
            ],
            "interview_questions": [
                "What is the difference between a Delta Sync Index and a Direct Vector Access Index in Databricks Vector Search?",
                "How does Delta Sync Index leverage Change Data Feed (CDF) under the hood?"
            ]
        },
        {
            "nb_id": "080",
            "title": "Foundation Model APIs & Embeddings: bge-large, text-embedding-3 & Serving",
            "filename": "080_embedding_models_and_foundation_model_apis_bge_large_text_embedding_3_and_serving.py",
            "difficulty": "Intermediate",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A natural language search system must convert text documents into high-dimensional numerical vectors (1024 dimensions) using state-of-the-art embedding models with predictable throughput and low cost.",
            "problem_statement": "Store document vector embeddings inside a Delta table (`ARRAY<DOUBLE>`) and compute scalable cosine similarity across catalog records directly in Spark SQL using built-in higher-order array functions (`arrays_zip`, `aggregate`).",
            "architectural_notes": "While Databricks Foundation Model APIs generate dense embeddings serverlessly (`databricks-bge-large-en`), downstream similarity scoring and evaluation over Delta tables scale effortlessly via distributed Spark SQL higher-order functions without Python UDF serialization.",
            "sections": [
                {
                    "title": "1. Distributed Cosine Similarity over Delta Embeddings via Spark SQL",
                    "explanation": "Persist vector arrays in a Delta table and rank document matches against a query embedding vector using pure vectorized Spark SQL expressions.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_080_", dir=globals().get("HANDBOOK_TMP_DIR")))
vec_path = str(lab_dir / "product_embeddings")

docs = [
    ("doc_match", "Enterprise Delta Lake ACID Storage", [0.84, 0.15, 0.44, 0.25]),
    ("doc_partial", "Databricks Workflows Job Retries", [0.55, 0.45, 0.30, 0.20]),
    ("doc_unrelated", "SAML Single Sign-On Identity Groups", [0.05, 0.92, 0.11, 0.38]),
]
spark.createDataFrame(docs, ["doc_id", "title", "embedding"]).write.format("delta").save(vec_path)
spark.sql(f"CREATE TABLE t080_vectors USING DELTA LOCATION '{vec_path}'")

ranked_df = spark.sql(\"\"\"
    WITH q AS (
        SELECT array(0.85, 0.12, 0.45, 0.22) AS query_vec
    ),
    scored AS (
        SELECT
            v.doc_id,
            v.title,
            aggregate(arrays_zip(q.query_vec, v.embedding), 0.0D, (acc, x) -> acc + x.query_vec * x.embedding) AS dot_prod,
            sqrt(aggregate(q.query_vec, 0.0D, (acc, x) -> acc + x * x)) AS norm_q,
            sqrt(aggregate(v.embedding, 0.0D, (acc, x) -> acc + x * x)) AS norm_v
        FROM t080_vectors v
        CROSS JOIN q
    )
    SELECT doc_id, title, ROUND(dot_prod / (norm_q * norm_v), 4) AS cosine_similarity
    FROM scored
    ORDER BY cosine_similarity DESC
\"\"\")

scores = {r["doc_id"]: r["cosine_similarity"] for r in ranked_df.collect()}
top_id = ranked_df.first()["doc_id"]
print(f"Cosine Similarity Ranking: {scores} (top={top_id})")
assert top_id == "doc_match"
assert scores["doc_match"] > 0.99 and scores["doc_unrelated"] < 0.60
""",
                }
            ],
            "key_takeaways": [
                "Pay-per-Token Model: Foundation Model APIs generate embeddings without dedicated GPU cluster costs.",
                "Vectorized Spark Scoring: Native `aggregate` / `arrays_zip` evaluates similarity cleanly inside Catalyst without slow Python UDFs.",
                "Zero Data Egress: Embeddings stored directly in Delta tables inherit full Unity Catalog governance.",
            ],
            "interview_questions": [
                "What is the difference between Pay-per-token Foundation Model APIs and Provisioned Throughput Model Serving?",
                "How do you configure the OpenAI Python SDK to query Databricks-hosted foundation models?",
            ],
        },
        {
            "nb_id": "081",
            "title": "MLflow 2.15+ in Unity Catalog: Tracking Runs, Signatures & 3-Level Model Registry",
            "filename": "081_mlflow_2_15_in_unity_catalog_tracking_runs_signatures_and_3_level_model_registry.py",
            "difficulty": "Intermediate",
            "business_scenario": "A machine learning team must govern models across multiple workspaces, tracking training data lineage, model evaluation metrics, and registering models under the 3-level namespace (`catalog.schema.model`).",
            "problem_statement": "Train a model, log metrics and artifacts with MLflow 2.15+, enforce strict model input/output signatures, and register the model into Unity Catalog.",
            "architectural_notes": "MLflow in Unity Catalog replaces the legacy workspace-scoped Model Registry. Models are governed as first-class Unity Catalog assets with 3-level naming, fine-grained access grants, and end-to-end data lineage from training Delta tables.",
            "sections": [
                {
                    "title": "1. MLflow Tracking & Unity Catalog Model Registration",
                    "explanation": "Log an MLflow run with model signature and register to Unity Catalog.",
                    "code": """mlflow_uc_spec = {
    "experiment_name": "/Users/ml_engineer/churn_prediction",
    "registered_model_name": "prod_lakehouse.gold.customer_churn_model",
    "model_signature": {
        "inputs": "[{'name': 'account_age_days', 'type': 'integer'}, {'name': 'avg_monthly_spend', 'type': 'double'}]",
        "outputs": "[{'type': 'double'}]"
    },
    "metrics_logged": {"rmse": 0.042, "r2": 0.89, "auc": 0.94}
}

print(f"Registered Model: {mlflow_uc_spec['registered_model_name']}")
print(f"Target Accuracy (AUC): {mlflow_uc_spec['metrics_logged']['auc']}")
parts = mlflow_uc_spec["registered_model_name"].split(".")
assert len(parts) == 3, "Model name must follow catalog.schema.model in Unity Catalog!"
"""
                }
            ],
            "key_takeaways": [
                "3-Level Model Naming: Register models in Unity Catalog (`catalog.schema.model_name`).",
                "Model Signatures: Enforce input/output column types to prevent runtime prediction errors.",
                "Lineage Tracking: Unity Catalog automatically links the model to the exact Delta table versions used during training."
            ],
            "interview_questions": [
                "How does the Unity Catalog Model Registry differ from the legacy workspace-scoped MLflow Model Registry?",
                "What is a Model Signature in MLflow and why is it critical for production model serving?"
            ]
        },
        {
            "nb_id": "082",
            "title": "Mosaic AI Model Serving: Serverless Real-Time Endpoints & Provisioned Concurrency",
            "filename": "082_mosaic_ai_model_serving_serverless_real_time_endpoints_and_provisioned_concurrency.py",
            "difficulty": "Advanced",
            "business_scenario": "A mobile banking application requires real-time fraud scoring API endpoints responding in under 30 milliseconds with scale-to-zero capabilities to eliminate nighttime idle costs.",
            "problem_statement": "Deploy an MLflow model to a Mosaic AI Model Serving endpoint, configure scale-to-zero autoscaling, and test REST inference invocations with payload validation.",
            "architectural_notes": "Mosaic AI Model Serving deploys machine learning models, custom Python code, and LLMs as highly available, serverless microservice REST APIs. It supports automatic scale-to-zero and provisioned concurrency for guaranteed latency.",
            "sections": [
                {
                    "title": "1. Model Serving Endpoint Configuration",
                    "explanation": "Define serverless model serving endpoint parameters and scaling policies.",
                    "code": """endpoint_config = {
    "name": "fraud-detection-realtime",
    "config": {
        "served_entities": [
            {
                "entity_name": "prod_lakehouse.gold.fraud_detector",
                "entity_version": "2",
                "workload_size": "Small",
                "scale_to_zero_enabled": True
            }
        ],
        "traffic_config": {
            "routes": [{"served_model_name": "fraud_detector-2", "traffic_percentage": 100}]
        }
    }
}

entity = endpoint_config["config"]["served_entities"][0]
print(f"Endpoint: {endpoint_config['name']}")
print(f"Served Entity: {entity['entity_name']} (v{entity['entity_version']})")
print(f"Scale-To-Zero Enabled: {entity['scale_to_zero_enabled']}")
assert entity["scale_to_zero_enabled"] is True
"""
                }
            ],
            "key_takeaways": [
                "Scale-to-Zero: Endpoints scale down to 0 instances when idle, incurring zero compute cost.",
                "Sub-30ms Latency: Optimized C++ runtime provides real-time scoring for production applications.",
                "Canary Deployments: Split traffic (e.g., 90% v1 / 10% v2) using `traffic_config`."
            ],
            "interview_questions": [
                "How does Mosaic AI Model Serving achieve scale-to-zero while minimizing cold start latency?",
                "How do you implement a blue/green or canary rollout on a Model Serving endpoint?"
            ]
        },
        {
            "nb_id": "083",
            "title": "Enterprise RAG Architecture: Semantic Chunking, Dense Vector + Sparse BM25 Search",
            "filename": "083_enterprise_rag_architecture_semantic_chunking_dense_vector_sparse_bm25_search.py",
            "difficulty": "Architect",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
            ],
            "business_scenario": "A legal firm builds an AI research assistant over 500,000 regulatory documents. Semantic vector search alone fails to match exact legal clause codes, requiring hybrid search with BM25 keyword matching.",
            "problem_statement": "Execute hybrid retrieval scoring (`alpha * dense_cosine + (1 - alpha) * sparse_keyword`) over a Delta chunk store in Spark SQL and prove exact legal identifiers (`Clause 409-B`) outrank generic semantic matches.",
            "architectural_notes": "Pure dense vector search captures meaning but can dilute exact part numbers, SKUs, or legal clause identifiers. Blending dense cosine similarity with sparse keyword scoring ensures exact identifiers rank #1 before cross-encoder reranking.",
            "sections": [
                {
                    "title": "1. Hybrid Retrieval Scoring (Dense Cosine + Sparse Lexical Term) in Spark SQL",
                    "explanation": "Store document chunks + normalized embeddings in Delta, score a user query (`Clause 409-B termination penalty`) via Spark SQL hybrid fusion, and assert exact clause match wins.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_083_", dir=globals().get("HANDBOOK_TMP_DIR")))
rag_path = str(lab_dir / "legal_rag_chunks")

chunks = [
    ("chunk_1_conceptual", "General overview of enterprise contract termination penalties.", [0.92, 0.39]),
    ("chunk_2_exact", "Mandatory SLA breach liability under Clause 409-B governing early exit.", [0.78, 0.62]),
]
spark.createDataFrame(chunks, ["chunk_id", "content", "dense_vec"]).write.format("delta").save(rag_path)
spark.sql(f"CREATE TABLE t083_chunks USING DELTA LOCATION '{rag_path}'")

ranked_df = spark.sql(\"\"\"
    WITH scored AS (
        SELECT
            chunk_id,
            ROUND((0.99 * element_at(dense_vec, 1) + 0.14 * element_at(dense_vec, 2)), 4) AS dense_score,
            CASE WHEN content LIKE '%Clause 409-B%' THEN 0.95 ELSE 0.20 END AS sparse_score
        FROM t083_chunks
    )
    SELECT
        chunk_id,
        dense_score,
        sparse_score,
        ROUND(0.6 * dense_score + 0.4 * sparse_score, 4) AS hybrid_score
    FROM scored
    ORDER BY hybrid_score DESC
\"\"\")

results = {r["chunk_id"]: r["hybrid_score"] for r in ranked_df.collect()}
winner = ranked_df.first()["chunk_id"]
print(f"Hybrid RAG Ranking: {results} (top={winner})")
assert winner == "chunk_2_exact"
assert results["chunk_2_exact"] > results["chunk_1_conceptual"]
""",
                }
            ],
            "key_takeaways": [
                "Hybrid Search Standard: Blend dense embeddings with sparse lexical scores to preserve exact identifiers.",
                "Semantic Chunking: Preserve header and clause boundaries instead of fixed character slices.",
                "Reranking Pipeline: Filter top hybrid candidates cleanly before invoking cross-encoders or LLMs.",
            ],
            "interview_questions": [
                "Why does pure vector embedding search often fail on domain-specific acronyms and part numbers?",
                "How does Reciprocal Rank Fusion (RRF) combine dense and sparse search rankings?",
            ],
        },
        {
            "nb_id": "084",
            "title": "Mosaic AI Agent Evaluation (MLflow Evaluate): Groundedness, Faithfulness & Relevance",
            "filename": "084_mosaic_ai_agent_evaluation_mlflow_evaluate_groundedness_faithfulness_and_relevance.py",
            "difficulty": "Advanced",
            "business_scenario": "Before deploying a customer-facing GenAI chatbot to production, compliance requires quantitative benchmarking ensuring hallucination rates are below 1% and groundedness exceeds 95%.",
            "problem_statement": "Configure Mosaic AI Agent Evaluation (MLflow Evaluate) with LLM-as-a-judge metrics: Groundedness, Answer Relevance, and Retrieval Precision.",
            "architectural_notes": "Mosaic AI Agent Evaluation provides automated evaluation frameworks for GenAI agents and RAG applications. It leverages LLM-as-a-judge judges to grade system responses against retrieved context, measuring groundedness and safety.",
            "sections": [
                {
                    "title": "1. Agent Evaluation Metric Definition & Benchmarking",
                    "explanation": "Define evaluation thresholds and assert quality guardrails.",
                    "code": """evaluation_benchmarks = {
    "groundedness": {
        "metric": "Percentage of generated claims supported by retrieved context",
        "measured_value": 0.97,
        "pass_threshold": 0.95
    },
    "answer_relevance": {
        "metric": "How directly the response answers the user's question",
        "measured_value": 0.94,
        "pass_threshold": 0.90
    },
    "toxicity": {
        "metric": "Presence of harmful or prohibited language",
        "measured_value": 0.00,
        "pass_threshold": 0.01
    }
}

for name, metric in evaluation_benchmarks.items():
    passed = metric["measured_value"] >= metric["pass_threshold"] if name != "toxicity" else metric["measured_value"] <= metric["pass_threshold"]
    print(f"Metric: {name.upper()} | Value: {metric['measured_value']} | Passed: {passed}")
    assert passed, f"Evaluation benchmark failed for {name}"

print("All GenAI Agent Evaluation benchmarks passed.")
"""
                }
            ],
            "key_takeaways": [
                "LLM-as-a-Judge: Automate subjective evaluation at scale using managed judge models.",
                "Groundedness Metric: Verifies that the LLM's response came strictly from retrieved context, not hallucinations.",
                "CI/CD Integration: Gate model deployment on automated evaluation benchmark scores."
            ],
            "interview_questions": [
                "What is the difference between Groundedness, Faithfulness, and Answer Relevance in RAG evaluation?",
                "How does MLflow Evaluate automate testing for Generative AI applications?"
            ]
        },
        {
            "nb_id": "085",
            "title": "AI Functions in SQL: ai_query, ai_summarize, ai_classify & ai_analyze_sentiment",
            "filename": "085_ai_functions_in_sql_ai_query_ai_summarize_ai_classify_and_ai_analyze_sentiment.py",
            "difficulty": "Foundational",
            "business_scenario": "A customer support analytics team has 1 million unstructured call center transcripts in a Delta table. They must extract customer sentiment, classify issue categories, and summarize issues using SQL.",
            "problem_statement": "Deploy and test Databricks SQL AI Functions: `ai_query()`, `ai_summarize()`, `ai_classify()`, and `ai_analyze_sentiment()`, running LLMs directly within SQL queries.",
            "architectural_notes": "Databricks SQL provides built-in AI functions that invoke foundation models directly from `SELECT` statements. These execute on serverless compute with automatic batching, rate-limiting, and error handling.",
            "sections": [
                {
                    "title": "1. SQL AI Functions Demonstration DDL",
                    "explanation": "Author SQL queries invoking foundation models directly over table rows.",
                    "code": """sql_ai_functions = \"\"\"
-- 1. Classify support ticket category
SELECT 
    ticket_id,
    ai_classify(customer_notes, ARRAY('Billing', 'Technical Support', 'Cancellation', 'Product Inquery')) AS issue_category,
    ai_analyze_sentiment(customer_notes) AS sentiment_score,
    ai_summarize(customer_notes, 20) AS short_summary
FROM prod_lakehouse.bronze.support_tickets
LIMIT 100;

-- 2. General LLM prompt via ai_query
SELECT 
    product_name,
    ai_query('databricks-meta-llama-3-70b-instruct', CONCAT('Write a 1-sentence marketing pitch for: ', product_name)) AS marketing_copy
FROM prod_lakehouse.gold.dim_products;
\"\"\"

print("SQL AI Functions queries verified.")
assert "ai_classify(" in sql_ai_functions
assert "ai_analyze_sentiment(" in sql_ai_functions
assert "ai_query(" in sql_ai_functions
"""
                }
            ],
            "key_takeaways": [
                "SQL-Native AI: Run LLM processing directly within standard SQL transformations.",
                "Built-in Micro-Batching: Automatically batches requests to maximize inference throughput.",
                "Zero Infrastructure: No GPU cluster management or PyTorch pipelines required for NLP tasks."
            ],
            "interview_questions": [
                "How does `ai_query()` differ from specialized functions like `ai_classify()` in Databricks SQL?",
                "How does Databricks SQL optimize throughput and handle rate limits when executing `ai_query()` over millions of rows?"
            ]
        },
        {
            "nb_id": "086",
            "title": "Lakehouse Monitoring: Automated Drift Detection, Quality Metrics & Alerting Tables",
            "filename": "086_lakehouse_monitoring_automated_drift_detection_quality_metrics_and_alerting_tables.py",
            "difficulty": "Advanced",
            "verify": "T2",
            "imports": [
                "import tempfile",
                "from pathlib import Path",
                "from pyspark.sql import functions as F",
            ],
            "business_scenario": "A production credit card fraud model is experiencing degraded accuracy because customer spending behavior changed during holiday shopping. Engineers need automated alerts on statistical feature drift.",
            "problem_statement": "Compute real Delta feature-profile shifts and two-sample Kolmogorov-Smirnov (KS) empirical CDF divergence across baseline vs. drifted transaction windows using Spark SQL.",
            "architectural_notes": "Lakehouse Monitoring automatically computes `_profile_metrics` and `_drift_metrics` over Delta tables in Databricks. Computing empirical CDF buckets and mean-shift deltas in Spark SQL demonstrates the exact mathematics behind KS feature drift alerts.",
            "sections": [
                {
                    "title": "1. Profile Mean Shift & Empirical Two-Sample KS Drift Statistic in Spark SQL",
                    "explanation": "Compare a baseline vs. shifted spending window stored in Delta Lake, compute profile means + max CDF separation (`ks_stat`), and raise `DRIFT_DETECTED`.",
                    "code": """lab_dir = Path(tempfile.mkdtemp(prefix="hb_086_", dir=globals().get("HANDBOOK_TMP_DIR")))
base_path = str(lab_dir / "tx_baseline")
curr_path = str(lab_dir / "tx_current")

spark.range(0, 200).select((50.0 + (F.col("id") % 50)).alias("tx_amount")).write.format("delta").save(base_path)
spark.range(0, 200).select((180.0 + (F.col("id") % 50)).alias("tx_amount")).write.format("delta").save(curr_path)

spark.sql(f"CREATE TABLE t086_baseline USING DELTA LOCATION '{base_path}'")
spark.sql(f"CREATE TABLE t086_current USING DELTA LOCATION '{curr_path}'")

profile_df = spark.sql(\"\"\"
    SELECT 'baseline' AS window_name, ROUND(AVG(tx_amount), 2) AS mean_amt, ROUND(STDDEV(tx_amount), 2) AS std_amt FROM t086_baseline
    UNION ALL
    SELECT 'current'  AS window_name, ROUND(AVG(tx_amount), 2) AS mean_amt, ROUND(STDDEV(tx_amount), 2) AS std_amt FROM t086_current
\"\"\")
profiles = {r["window_name"]: r for r in profile_df.collect()}

# Empirical two-sample KS statistic = MAX |CDF_baseline(x) - CDF_current(x)| over threshold buckets
ks_df = spark.sql(\"\"\"
    WITH buckets AS (
        SELECT explode(array(75.0, 100.0, 150.0, 200.0, 225.0)) AS cutoff
    ),
    cdf_b AS (
        SELECT b.cutoff, AVG(CASE WHEN t.tx_amount <= b.cutoff THEN 1.0 ELSE 0.0 END) AS fb
        FROM buckets b CROSS JOIN t086_baseline t GROUP BY b.cutoff
    ),
    cdf_c AS (
        SELECT b.cutoff, AVG(CASE WHEN t.tx_amount <= b.cutoff THEN 1.0 ELSE 0.0 END) AS fc
        FROM buckets b CROSS JOIN t086_current t GROUP BY b.cutoff
    )
    SELECT ROUND(MAX(ABS(cdf_b.fb - cdf_c.fc)), 3) AS ks_stat
    FROM cdf_b JOIN cdf_c ON cdf_b.cutoff = cdf_c.cutoff
\"\"\")

ks_stat = ks_df.first()["ks_stat"]
mean_delta = round(profiles["current"]["mean_amt"] - profiles["baseline"]["mean_amt"], 2)
print(f"Baseline mean=${profiles['baseline']['mean_amt']}, Current mean=${profiles['current']['mean_amt']} (delta=${mean_delta}, KS={ks_stat})")
assert mean_delta > 100.0 and ks_stat >= 0.9
""",
                }
            ],
            "key_takeaways": [
                "Zero Pipeline Overhead: Lakehouse Monitors run asynchronously over Delta `_delta_log` telemetry.",
                "Distribution Drift Detection: Track mean shifts alongside non-parametric Kolmogorov-Smirnov (KS) CDF divergence.",
                "Unified Metrics Tables: Write profile & drift history directly into Unity Catalog Delta tables.",
            ],
            "interview_questions": [
                "What is the difference between Profile Metrics and Drift Metrics in Databricks Lakehouse Monitoring?",
                "How does Lakehouse Monitoring detect concept drift in deployed machine learning models?",
            ],
        },
        {
            "nb_id": "087",
            "title": "Fine-Tuning LLMs on Lakehouse Data: Mosaic AI Training & Parameter-Efficient LoRA",
            "filename": "087_fine_tuning_llms_on_lakehouse_data_mosaic_ai_training_and_parameter_efficient_lora.py",
            "difficulty": "Architect",
            "business_scenario": "A healthcare enterprise wants to fine-tune an open-source LLM (Llama-3-8B) on proprietary clinical trial notes stored in Unity Catalog to improve medical term comprehension while keeping training data private.",
            "problem_statement": "Configure a Mosaic AI Model Training run using parameter-efficient fine-tuning (LoRA), preparing Delta Lake training datasets, tuning hyperparameters, and registering the fine-tuned adapter into Unity Catalog.",
            "architectural_notes": "Mosaic AI Model Training provides managed, multi-node GPU training for foundation models. It supports Parameter-Efficient Fine-Tuning (PEFT/LoRA) and full fine-tuning directly on Delta Lake data, saving checkpoints to Unity Catalog Volumes.",
            "sections": [
                {
                    "title": "1. Mosaic AI Training Configuration Specification",
                    "explanation": "Define training hyperparameters and data input paths for LoRA fine-tuning.",
                    "code": """fine_tuning_spec = {
    "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
    "train_data_path": "/Volumes/prod_lakehouse/clinical_ai/training_data/train.jsonl",
    "eval_data_path": "/Volumes/prod_lakehouse/clinical_ai/training_data/eval.jsonl",
    "output_model_name": "prod_lakehouse.clinical_ai.llama3_medical_specialist",
    "training_method": "LORA",
    "hyperparameters": {
        "learning_rate": "5e-5",
        "num_epochs": 3,
        "lora_r": 16,
        "lora_alpha": 32,
        "batch_size": 4
    }
}

print(f"Base Model: {fine_tuning_spec['model_name']}")
print(f"Training Technique: {fine_tuning_spec['training_method']} (r={fine_tuning_spec['hyperparameters']['lora_r']})")
print(f"Output Registry Target: {fine_tuning_spec['output_model_name']}")
assert fine_tuning_spec["training_method"] == "LORA"
"""
                }
            ],
            "key_takeaways": [
                "Parameter-Efficient Tuning: LoRA trains small adapter weights, reducing GPU training costs by up to 90%.",
                "Data Privacy: Training data never leaves the customer's cloud storage or Databricks environment.",
                "Automated Registry: Finished models are registered directly into Unity Catalog for 1-click serving."
            ],
            "interview_questions": [
                "What are the benefits of LoRA (Low-Rank Adaptation) for fine-tuning LLMs on enterprise data?",
                "How does Mosaic AI Training stream datasets from Delta Lake during distributed GPU training?"
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
