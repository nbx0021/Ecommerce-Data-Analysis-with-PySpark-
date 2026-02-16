import sys
import os
from pathlib import Path
from src.bronze.ingest import ingest_to_bronze
from src.utils.spark_utils import get_spark_session

def run_pipeline():
    spark = get_spark_session()
    
    # 🧠 DYNAMIC ROOT DETECTION (Industry Standard)
    # Finds the folder where THIS file (main_pipeline.py) lives
    PROJECT_ROOT = Path(__file__).resolve().parent
    
    print(f"📍 Detected Project Root: {PROJECT_ROOT}")
    
    # Map datasets relative to the detected root
    DATA_DIR = PROJECT_ROOT / "data"
    
    # Convert paths to strings (.as_posix()) for Spark compatibility
    DATASETS = {
        "customers": (DATA_DIR / "olist_customers_dataset.csv").as_posix(),
        "orders": (DATA_DIR / "olist_orders_dataset.csv").as_posix(),
        "order_items": (DATA_DIR / "olist_order_items_dataset.csv").as_posix(),
        "order_payments": (DATA_DIR / "olist_order_payments_dataset.csv").as_posix(),
        "order_reviews": (DATA_DIR / "olist_order_reviews_dataset.csv").as_posix(),
        "products": (DATA_DIR / "olist_products_dataset.csv").as_posix(),
        "sellers": (DATA_DIR / "olist_sellers_dataset.csv").as_posix(),
        "geolocation": (DATA_DIR / "olist_geolocation_dataset.csv").as_posix(),
        "category_translation": (DATA_DIR / "product_category_name_translation.csv").as_posix()
    }

    print("\n--- 🏗️ BRONZE LAYER ---")
    for table_name, full_path in DATASETS.items():
        ingest_to_bronze(spark, full_path, table_name)

    print("\n🎉 Pipeline Finished Successfully!")

if __name__ == "__main__":
    run_pipeline()