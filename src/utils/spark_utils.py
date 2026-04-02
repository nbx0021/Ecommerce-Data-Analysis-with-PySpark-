# src/utils/spark_utils.py
"""
Spark Session factory — optimized for Databricks Community Edition.
Removes unused Delta config, adds AQE and shuffle partition tuning.
"""
from pyspark.sql import SparkSession
from src.utils.logger import get_logger
from src.config import SPARK_SHUFFLE_PARTITIONS, SPARK_AQE_ENABLED
import os

logger = get_logger("spark_utils")


def get_spark_session(app_name: str = "Olist_Lakehouse") -> SparkSession:
    """
    Returns a configured SparkSession.
    
    - On Databricks CE: uses the existing session (no custom config needed)
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
                .config("spark.sql.shuffle.partitions", str(SPARK_SHUFFLE_PARTITIONS))
                .config("spark.sql.adaptive.enabled", str(SPARK_AQE_ENABLED).lower())
                .config("spark.driver.memory", "2g")
                .getOrCreate()
        )

    # Apply tuning to both environments
    spark.conf.set("spark.sql.shuffle.partitions", str(SPARK_SHUFFLE_PARTITIONS))
    spark.conf.set("spark.sql.adaptive.enabled", str(SPARK_AQE_ENABLED).lower())

    logger.info(
        f"⚙️ Spark Config: shuffle.partitions={SPARK_SHUFFLE_PARTITIONS}, "
        f"AQE={'enabled' if SPARK_AQE_ENABLED else 'disabled'}"
    )

    return spark