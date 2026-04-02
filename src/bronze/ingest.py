# src/bronze/ingest.py
"""
Bronze Layer — Raw Data Ingestion.
Reads CSVs via Pandas bridge (required for Databricks CE compatibility)
and registers them as Spark Temporary Views with schema enforcement.
"""
from pyspark.sql.functions import current_timestamp, lit, input_file_name
from src.bronze.schemas import SCHEMA_REGISTRY
from src.utils.logger import get_logger
import os
import pandas as pd

logger = get_logger("bronze.ingest")


def ingest_to_bronze(spark, source_path: str, table_name: str) -> int:
    """
    Ingests a CSV file into a Bronze-layer Spark TempView.

    Args:
        spark: SparkSession
        source_path: Absolute path to the CSV file
        table_name: Logical name (e.g., 'orders', 'customers')

    Returns:
        Row count of the ingested data

    Raises:
        FileNotFoundError: If source CSV does not exist
        ValueError: If schema not found in SCHEMA_REGISTRY
    """
    view_name = f"{table_name}_bronze"

    try:
        logger.info(f"⏳ Ingesting '{table_name}' from: {source_path}")

        # --- 1. VALIDATE ---
        clean_path = source_path.replace("file:", "")
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Data missing at: {clean_path}")

        # --- 2. READ via Pandas Bridge ---
        # (spark.read.csv() errors on Databricks CE; Pandas bridge is required)
        pdf = pd.read_csv(clean_path, dtype=str, keep_default_na=False)
        
        # --- 3. CONVERT to Spark with Schema ---
        schema = SCHEMA_REGISTRY.get(table_name)
        if schema:
            # Ensure column alignment: keep only columns defined in schema
            schema_cols = [f.name for f in schema.fields]
            pdf = pdf[[c for c in schema_cols if c in pdf.columns]]
            df = spark.createDataFrame(pdf, schema=schema)
            logger.info(f"   Schema enforced: {len(schema.fields)} columns")
        else:
            logger.warning(f"   ⚠️ No schema found for '{table_name}', using inferred types")
            df = spark.createDataFrame(pdf)

        # --- 4. ADD Audit Columns ---
        df_enriched = (
            df
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file", lit(os.path.basename(clean_path)))
        )

        # --- 5. REGISTER as TempView ---
        df_enriched.createOrReplaceTempView(view_name)
        row_count = df_enriched.count()

        logger.info(f"✅ '{view_name}' loaded → {row_count:,} rows")
        return row_count

    except FileNotFoundError:
        logger.error(f"❌ File not found: {clean_path}")
        raise
    except Exception as e:
        logger.error(f"❌ Error ingesting '{table_name}': {str(e)}")
        raise