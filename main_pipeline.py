# main_pipeline.py
import sys
import os
from pathlib import Path
from src.bronze.ingest import ingest_to_bronze
from src.silver.clean import clean_silver_layer
from src.gold.aggregate import aggregate_gold_layer
from src.utils.spark_utils import get_spark_session

def run_pipeline():
    spark = get_spark_session()
    
    # ---------------------------------------
    # 1. SETUP & BRONZE (Raw Ingestion)
    # ---------------------------------------
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
        
    # ---------------------------------------
    # 2. SILVER LAYER (Cleaning)
    # ---------------------------------------
    # Imports the functions we just wrote
    # Note: Lit needs to be imported in the silver module, adding it here for safety if missing
    from pyspark.sql.functions import lit 
    clean_silver_layer(spark)
    
    # ---------------------------------------
    # 3. GOLD LAYER (Aggregation)
    # ---------------------------------------
    aggregate_gold_layer(spark)
    
    # ---------------------------------------
    # 4. FINAL VERIFICATION
    # ---------------------------------------
    print("\n--- 🚀 FINAL RESULTS ---")
    
    print("Delivery Metrics:")
    spark.sql("SELECT * FROM gold_logistics_performance").show()
    
    print("\n1. Customer Segments (RFM Analysis):")
    spark.sql("SELECT * FROM gold_customer_segments").show(truncate=False)
    
    print("\n2. Monthly Revenue Trend (Last 3 Months):")
    spark.sql("SELECT * FROM gold_monthly_sales ORDER BY month DESC LIMIT 3").show()

    print("\n3. Top 3 Categories by Revenue:")
    spark.sql("SELECT * FROM gold_product_performance LIMIT 3").show()
    
    print("\n4. Logistics Performance:")
    spark.sql("SELECT * FROM gold_logistics_performance").show()

    print("\n🎉 Pipeline Finished Successfully!")

if __name__ == "__main__":
    run_pipeline()