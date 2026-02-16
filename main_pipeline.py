
import sys
import os
from pathlib import Path
from src.bronze.ingest import ingest_to_bronze
from src.utils.spark_utils import get_spark_session

def run_pipeline():
    spark = get_spark_session()
    
    # 🧠 DYNAMIC ROOT DETECTION
    try:
        PROJECT_ROOT = Path(__file__).resolve().parent
    except NameError:
        PROJECT_ROOT = Path(os.getcwd())
    
    print(f"📍 Project Root: {PROJECT_ROOT}")
    DATA_DIR = PROJECT_ROOT / "data"
    
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

    print("\n--- 🏗️ BRONZE LAYER (In-Memory) ---")
    for table_name, full_path in DATASETS.items():
        ingest_to_bronze(spark, full_path, table_name)
        
    # VERIFICATION
    print("\n--- 🔍 Verifying Data Load ---")
    try:
        # 🛑 OLD: global_temp.customers_bronze
        # ✅ NEW: customers_bronze
        row_count = spark.sql("SELECT count(*) FROM customers_bronze").collect()[0][0]
        print(f"Verified: 'customers_bronze' has {row_count} rows.")
    except Exception as e:
        print(f"Verification Failed: {e}")

    print("\n🎉 Pipeline Finished Successfully!")

if __name__ == "__main__":
    run_pipeline()