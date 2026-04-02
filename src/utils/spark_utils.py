# src/utils/spark_utils.py
"""
Spark Session factory — optimized for Databricks Community Edition.
Handles Spark Connect limitations (some configs are not settable on CE).
"""
from pyspark.sql import SparkSession
from src.utils.logger import get_logger
import os

logger = get_logger("spark_utils")


def _safe_set_conf(spark, key: str, value: str):
    """Safely set a Spark config — silently skips if not available (Spark Connect)."""
    try:
        spark.conf.set(key, value)
    except Exception as e:
        logger.warning(f"⚠️ Could not set '{key}': {e} (skipping)")


def get_spark_session(app_name: str = "Olist_Lakehouse") -> SparkSession:
    """
    Returns a configured SparkSession.
    
    - On Databricks CE: uses the existing session (no custom config)
    - Locally: creates a session with optimized settings
    """
    is_databricks = "DATABRICKS_RUNTIME_VERSION" in os.environ

    if is_databricks:
        runtime_version = os.environ.get("DATABRICKS_RUNTIME_VERSION", "unknown")
        logger.info(f"🔷 Running on Databricks (Runtime: {runtime_version})")
        spark = SparkSession.builder.getOrCreate()
    else:
        logger.info("💻 Running locally")
        spark = (SparkSession.builder
                .appName(app_name)
                .master("local[*]")
                .config("spark.sql.shuffle.partitions", "8")
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.driver.memory", "2g")
                .getOrCreate()
        )

    # Apply tuning — use safe setter for Databricks Spark Connect compatibility
    _safe_set_conf(spark, "spark.sql.shuffle.partitions", "8")

    logger.info("⚙️ Spark session ready")
    return spark