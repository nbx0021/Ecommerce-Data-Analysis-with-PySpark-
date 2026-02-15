# main_pipeline.py
from src.bronze.ingest import ingest_to_bronze
from src.utils.spark_utils import get_spark_session
import os

# 1. CATALOG: Map every raw CSV to a clean Table Name
DATASETS = {
    "customers": "data/olist_customers_dataset.csv",
    "orders": "data/olist_orders_dataset.csv",
    "order_items": "data/olist_order_items_dataset.csv",
    "order_payments": "data/olist_order_payments_dataset.csv",
    "order_reviews": "data/olist_order_reviews_dataset.csv",
    "products": "data/olist_products_dataset.csv",
    "sellers": "data/olist_sellers_dataset.csv",
    "geolocation": "data/olist_geolocation_dataset.csv",
    "category_translation": "data/product_category_name_translation.csv"
}

def run_pipeline():
    spark = get_spark_session()
    print("🚀 Starting Olist Lakehouse Pipeline...")

    # --- STEP 1: BRONZE LAYER (Raw Ingestion) ---
    print("\n--- 🏗️ BRONZE LAYER ---")
    for table_name, relative_path in DATASETS.items():
        
        # 🛡️ DYNAMIC PATH LOGIC (No Hardcoded Email)
        if "DATABRICKS_RUNTIME_VERSION" in os.environ:
            # We are on Databricks!
            # os.getcwd() in a Repo usually returns /Workspace/Repos/email/repo_name
            # We can use that directly without hardcoding
            current_dir = os.getcwd()
            full_path = f"file:{current_dir}/{relative_path}"
        else:
            # We are Local!
            # Use the absolute path of your local project
            current_dir = os.getcwd()
            full_path = f"{current_dir}/{relative_path}"

        ingest_to_bronze(spark, full_path, table_name)

    print("\n🎉 Pipeline Finished Successfully!")

if __name__ == "__main__":
    run_pipeline()