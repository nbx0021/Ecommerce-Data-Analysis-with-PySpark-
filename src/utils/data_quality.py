# src/utils/data_quality.py
"""
Reusable data quality checks for the pipeline.
Industry-standard observability: null rates, row counts, quality reports.
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, when, isnan
from src.utils.logger import get_logger

logger = get_logger("data_quality")


def check_row_count(df: DataFrame, view_name: str, min_rows: int = 1) -> int:
    """
    Validates that a DataFrame has at least `min_rows` rows.
    Returns the actual row count.
    Raises ValueError if below threshold.
    """
    row_count = df.count()
    if row_count < min_rows:
        logger.error(f"❌ QUALITY GATE FAILED: '{view_name}' has {row_count} rows (min: {min_rows})")
        raise ValueError(f"Data quality check failed: '{view_name}' has {row_count} rows, expected >= {min_rows}")
    
    logger.info(f"✅ '{view_name}' row count: {row_count:,}")
    return row_count


def check_nulls(df: DataFrame, columns: list, view_name: str, threshold: float = 0.05) -> dict:
    """
    Checks null rate for specified columns.
    Logs warnings if null rate exceeds threshold (default 5%).
    Returns dict of {column: null_rate}.
    """
    total = df.count()
    if total == 0:
        logger.warning(f"⚠️ '{view_name}' is empty, skipping null check")
        return {}

    null_rates = {}
    for col_name in columns:
        null_count = df.filter(col(col_name).isNull() | (col(col_name) == "")).count()
        null_rate = null_count / total
        null_rates[col_name] = null_rate

        if null_rate > threshold:
            logger.warning(
                f"⚠️ '{view_name}.{col_name}' null rate: {null_rate:.1%} "
                f"(threshold: {threshold:.1%}, nulls: {null_count:,}/{total:,})"
            )

    return null_rates


def log_quality_report(df: DataFrame, view_name: str) -> None:
    """
    Logs a summary quality report for a view.
    Shows row count and null counts per column.
    """
    row_count = df.count()
    col_count = len(df.columns)
    logger.info(f"📋 Quality Report for '{view_name}': {row_count:,} rows × {col_count} columns")

    # Calculate nulls per column in a single pass
    null_exprs = [
        count(when(col(c).isNull(), c)).alias(c) 
        for c in df.columns
    ]
    null_counts = df.select(null_exprs).collect()[0]

    for c in df.columns:
        nc = null_counts[c]
        if nc > 0:
            rate = nc / row_count if row_count > 0 else 0
            logger.info(f"   ├── {c}: {nc:,} nulls ({rate:.1%})")
