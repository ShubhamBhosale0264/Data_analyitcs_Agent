"""
Celery tasks for the analysis app.
These are the most compute-intensive tasks — they run pandas, scipy,
and scikit-learn operations that can take minutes on large datasets.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="analysis.run_full_profile")
def run_full_profile_task(self, dataset_id: str) -> dict:
    """
    Run complete statistical profiling on a dataset.
    Triggered automatically after successful ingestion.
    """
    from apps.datasets.models import Dataset
    from apps.analysis.models import DataProfile
    from utils.analysis.profiler import DataProfiler
    from utils.analysis.correlations import CorrelationEngine
    from utils.ai.narrative import generate_dataset_narrative

    dataset = Dataset.objects.get(id=dataset_id)

    # 1. Load the parquet snapshot (fast — no file re-reading)
    import pandas as pd
    df = pd.read_parquet(dataset.parquet_path)

    # 2. Run profiling engine
    self.update_state(state="PROGRESS", meta={"step": "profiling", "pct": 20})
    profiler = DataProfiler(df)
    profile_data = profiler.run()

    # 3. Run correlation analysis
    self.update_state(state="PROGRESS", meta={"step": "correlations", "pct": 50})
    corr_engine = CorrelationEngine(df)
    corr_data = corr_engine.compute()

    # 4. Generate AI narrative (LLM call — may take 2-5 seconds)
    self.update_state(state="PROGRESS", meta={"step": "ai_narrative", "pct": 80})
    narrative = generate_dataset_narrative(dataset, profile_data)

    # 5. Save results to DB
    profile, _ = DataProfile.objects.update_or_create(
        dataset=dataset,
        defaults={
            "profile_data": profile_data,
            "ai_narrative": narrative,
            "key_insights": profiler.extract_insights(),
        }
    )

    return {"status": "success", "profile_id": str(profile.id)}


@shared_task(bind=True, name="analysis.run_anomaly_detection")
def run_anomaly_detection_task(self, dataset_id: str, method: str = "isolation_forest") -> dict:
    """
    Run anomaly detection on a dataset.
    Uses IsolationForest by default (good for multivariate anomalies).
    Falls back to Z-score for single-column analysis.
    """
    from apps.datasets.models import Dataset
    from apps.analysis.models import AnomalyReport
    from utils.analysis.anomaly import AnomalyDetector
    import pandas as pd

    dataset = Dataset.objects.get(id=dataset_id)
    df = pd.read_parquet(dataset.parquet_path)

    detector = AnomalyDetector(df, method=method)
    results = detector.detect()

    AnomalyReport.objects.create(
        dataset=dataset,
        method=method,
        anomaly_count=len(results["anomaly_indices"]),
        anomaly_indices=results["anomaly_indices"],
        feature_importance=results["feature_importance"],
    )
    return {"status": "success", "anomalies_found": len(results["anomaly_indices"])}


@shared_task(bind=True, name="analysis.run_nl_query")
def run_nl_query_task(self, nl_query_id: str) -> dict:
    """
    Execute a natural language query:
      1. Build a schema-aware prompt from the dataset's Column objects
      2. Call LLM to generate SQL
      3. Validate and sanitize the generated SQL
      4. Execute against the dataset's parquet file (via DuckDB) or source DB
      5. Generate a Plotly chart config for the result
      6. Save everything to NLQueryResult
    """
    from apps.analysis.models import NLQueryResult
    from utils.ai.nl_to_sql import NLToSQLEngine
    from utils.charts.auto_chart import AutoChartEngine
    import pandas as pd

    nl_query = NLQueryResult.objects.select_related("dataset").get(id=nl_query_id)

    engine = NLToSQLEngine(nl_query.dataset)
    sql_result = engine.generate(nl_query.question)

    nl_query.generated_sql = sql_result["sql"]
    nl_query.sql_explanation = sql_result["explanation"]
    nl_query.llm_tokens_used = sql_result["tokens_used"]

    if sql_result["success"]:
        import duckdb
        df = pd.read_parquet(nl_query.dataset.parquet_path)
        conn = duckdb.connect()
        conn.register("data", df)
        result_df = conn.execute(sql_result["sql"]).df()

        chart_engine = AutoChartEngine(result_df)
        chart_config = chart_engine.recommend_and_build()

        nl_query.result_data = result_df.to_dict("records")
        nl_query.result_row_count = len(result_df)
        nl_query.chart_config = chart_config
        nl_query.was_successful = True

    nl_query.save()
    return {"status": "success"}
