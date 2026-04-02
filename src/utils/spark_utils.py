# src/utils/spark_utils.py
"""
Spark Session factory — optimized for Databricks Community Edition.
Handles Spark Connect limitations:
  - spark.conf.set() blocked for many configs on serverless
  - spark.table() can trigger PERSIST TABLE checks
"""
from pyspark.sql import SparkSession
from src.utils.logger import get_logger
import os

logger = get_logger("spark_utils")


def get_spark_session(app_name: str = "Olist_Lakehouse") -> SparkSession:
    """
    Returns a configured SparkSession.
    
    - On Databricks CE: uses the existing session as-is (no config changes)
    - Locally: creates a session with optimized settings
    """
    is_databricks = "DATABRICKS_RUNTIME_VERSION" in os.environ

    if is_databricks:
        runtime_version = os.environ.get("DATABRICKS_RUNTIME_VERSION", "unknown")
        logger.info(f"🔷 Running on Databricks (Runtime: {runtime_version})")
        # On serverless, do NOT set any config — most are blocked
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

    logger.info("⚙️ Spark session ready")
    return spark