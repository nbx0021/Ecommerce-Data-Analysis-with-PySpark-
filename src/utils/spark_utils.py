# src/utils/spark_utils.py
from pyspark.sql import SparkSession
import os

def get_spark_session(app_name="Olist_Lakehouse"):
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        return SparkSession.builder.getOrCreate()
    else:
        return (SparkSession.builder
                .appName(app_name)
                .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0")
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
                .getOrCreate())