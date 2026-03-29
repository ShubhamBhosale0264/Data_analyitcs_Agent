"""
Celery tasks for the datasets app.

All heavy data operations live here, never in views.
Views are only responsible for: receiving a request, kicking off a task,
and returning an immediate response. The task does the actual work
asynchronously and updates the Dataset status when it finishes.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="datasets.ingest_file")
def ingest_file_task(self, dataset_id: str) -> dict:
    """
    Process an uploaded CSV or Excel file.

    Steps:
      1. Load Dataset from DB
      2. Use CSVAdapter to read file into DataFrame (chunked for large files)
      3. Detect column types and semantic types
      4. Save processed data as parquet
      5. Create Column records for each column
      6. Update Dataset status to READY

    The `bind=True` argument gives us access to `self` (the task instance),
    which lets us update task progress so the UI can show a progress bar.
    """
    from apps.datasets.models import Dataset
    from utils.adapters.csv_adapter import CSVAdapter
    from utils.adapters.column_detector import ColumnTypeDetector

    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = Dataset.Status.PROCESSING
        dataset.save(update_fields=["status"])

        # Step 1: Read file using the adapter (handles CSV and Excel)
        self.update_state(state="PROGRESS", meta={"step": "reading_file", "pct": 10})
        adapter = CSVAdapter(dataset.file.path)
        df = adapter.to_dataframe()

        # Step 2: Detect types
        self.update_state(state="PROGRESS", meta={"step": "detecting_types", "pct": 40})
        detector = ColumnTypeDetector(df)
        column_metadata = detector.detect_all()

        # Step 3: Save parquet snapshot
        self.update_state(state="PROGRESS", meta={"step": "saving_parquet", "pct": 65})
        parquet_path = f"datasets/processed/{dataset_id}.parquet"
        df.to_parquet(parquet_path, index=False)

        # Step 4: Create Column records
        self.update_state(state="PROGRESS", meta={"step": "saving_metadata", "pct": 80})
        from apps.datasets.models import Column
        Column.objects.filter(dataset=dataset).delete()  # clean re-run
        columns = []
        for i, (col_name, meta) in enumerate(column_metadata.items()):
            columns.append(Column(
                dataset=dataset,
                name=col_name,
                position=i,
                data_type=meta["data_type"],
                semantic_type=meta["semantic_type"],
                null_count=meta["null_count"],
                null_percentage=meta["null_percentage"],
                unique_count=meta["unique_count"],
                unique_percentage=meta["unique_percentage"],
                sample_values=meta["sample_values"],
                min_value=meta.get("min_value"),
                max_value=meta.get("max_value"),
                mean_value=meta.get("mean_value"),
                std_value=meta.get("std_value"),
                top_values=meta.get("top_values", {}),
            ))
        Column.objects.bulk_create(columns)

        # Step 5: Mark dataset ready
        dataset.status = Dataset.Status.READY
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.parquet_path = parquet_path
        dataset.last_refreshed_at = timezone.now()
        dataset.save()

        logger.info(f"Dataset {dataset_id} ingested: {len(df)} rows, {len(df.columns)} cols")
        return {"status": "success", "rows": len(df), "columns": len(df.columns)}

    except Exception as exc:
        logger.error(f"Ingestion failed for dataset {dataset_id}: {exc}")
        Dataset.objects.filter(id=dataset_id).update(
            status=Dataset.Status.ERROR,
            processing_error=str(exc),
        )
        raise  # re-raise so Celery marks the task as FAILED


@shared_task(bind=True, name="datasets.ingest_sql_table")
def ingest_sql_table_task(self, dataset_id: str) -> dict:
    """
    Pull a table from an analyst's SQL database into a parquet snapshot.
    Uses SQLAdapter which wraps SQLAlchemy for database-agnostic connectivity.
    """
    from apps.datasets.models import Dataset
    from utils.adapters.sql_adapter import SQLAdapter

    dataset = Dataset.objects.get(id=dataset_id)
    adapter = SQLAdapter(
        connection_string=dataset.source.connection_string,
        table_name=dataset.table_name,
        custom_query=dataset.sql_query or None,
    )
    df = adapter.to_dataframe()
    # ... same processing pipeline as ingest_file_task
    return {"status": "success", "rows": len(df)}
