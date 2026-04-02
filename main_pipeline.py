# main_pipeline.py
"""
Pipeline Orchestrator — Entry point for the E-Commerce ETL pipeline.
Executes Bronze → Silver → Gold layers with timing and error handling.
"""
import time
from src.bronze.ingest import ingest_to_bronze
from src.silver.clean import clean_silver_layer
from src.gold.aggregate import aggregate_gold_layer
from src.utils.spark_utils import get_spark_session
from src.utils.logger import get_logger
from src.config import DATASETS, PROJECT_ROOT

logger = get_logger("pipeline")


def run_pipeline():
    """
    Orchestrates the full ETL pipeline:
    1. Bronze: Ingest raw CSVs into Spark TempViews
    2. Silver: Clean, cast, and enrich data
    3. Gold: Aggregate business-level KPIs
    4. Verify: Display key results
    """
    pipeline_start = time.time()
    spark = get_spark_session()

    logger.info(f"📍 Project Root: {PROJECT_ROOT}")
    logger.info(f"📦 Datasets to load: {len(DATASETS)}")

    # ─────────────────────────────────────────────────────────
    # 1. BRONZE LAYER (Raw Ingestion)
    # ─────────────────────────────────────────────────────────
    layer_start = time.time()
    logger.info("\n━━━ 🏗️ BRONZE LAYER ━━━")

    total_rows = 0
    for table_name, full_path in DATASETS.items():
        try:
            rows = ingest_to_bronze(spark, full_path, table_name)
            total_rows += rows
        except Exception as e:
            logger.error(f"❌ Bronze failed for '{table_name}': {e}")
            raise  # Stop pipeline if Bronze fails

    bronze_time = time.time() - layer_start
    logger.info(f"⏱️ Bronze completed in {bronze_time:.1f}s ({total_rows:,} total rows)")

    # ─────────────────────────────────────────────────────────
    # 2. SILVER LAYER (Cleaning & Enrichment)
    # ─────────────────────────────────────────────────────────
    layer_start = time.time()

    try:
        clean_silver_layer(spark)
    except Exception as e:
        logger.error(f"❌ Silver layer failed: {e}")
        raise

    silver_time = time.time() - layer_start
    logger.info(f"⏱️ Silver completed in {silver_time:.1f}s")

    # ─────────────────────────────────────────────────────────
    # 3. GOLD LAYER (Aggregation & KPIs)
    # ─────────────────────────────────────────────────────────
    layer_start = time.time()

    try:
        aggregate_gold_layer(spark)
    except Exception as e:
        logger.error(f"❌ Gold layer failed: {e}")
        raise

    gold_time = time.time() - layer_start
    logger.info(f"⏱️ Gold completed in {gold_time:.1f}s")

    # ─────────────────────────────────────────────────────────
    # 4. VERIFICATION — Display Key Results
    # ─────────────────────────────────────────────────────────
    logger.info("\n━━━ 🚀 PIPELINE RESULTS ━━━")

    logger.info("\n1. Logistics Performance:")
    spark.sql("SELECT * FROM gold_logistics_performance").show()

    logger.info("\n2. Customer Segments (RFM Analysis):")
    spark.sql("SELECT * FROM gold_customer_segments").show(truncate=False)

    logger.info("\n3. Monthly Revenue Trend (Last 3 Months):")
    spark.sql("SELECT * FROM gold_monthly_sales ORDER BY month DESC LIMIT 3").show()

    logger.info("\n4. Top 5 Categories by Revenue:")
    spark.sql("SELECT * FROM gold_product_performance LIMIT 5").show()

    logger.info("\n5. Payment Method Distribution:")
    spark.sql("SELECT * FROM gold_payment_analysis").show()

    logger.info("\n6. Top 5 Sellers by Revenue:")
    spark.sql("SELECT * FROM gold_seller_performance LIMIT 5").show()

    logger.info("\n7. Review Insights (Top 5 Categories):")
    spark.sql("SELECT * FROM gold_review_insights LIMIT 5").show()

    # ─────────────────────────────────────────────────────────
    # 5. SUMMARY
    # ─────────────────────────────────────────────────────────
    total_time = time.time() - pipeline_start
    logger.info(
        f"\n🎉 Pipeline Finished Successfully!\n"
        f"   ├── Bronze: {bronze_time:.1f}s\n"
        f"   ├── Silver: {silver_time:.1f}s\n"
        f"   ├── Gold:   {gold_time:.1f}s\n"
        f"   └── Total:  {total_time:.1f}s"
    )


if __name__ == "__main__":
    run_pipeline()