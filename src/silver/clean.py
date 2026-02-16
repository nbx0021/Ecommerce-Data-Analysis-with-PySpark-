# src/silver/clean.py
from pyspark.sql.functions import col, when, to_timestamp, coalesce
from pyspark.sql.types import DoubleType

def clean_silver_layer(spark):
    print("\n--- 🧹 SILVER LAYER (In-Memory) ---")

    # ---------------------------------------------------------
    # 1. CLEAN ORDERS
    # Logic: Convert strings to timestamps, handle nulls
    # ---------------------------------------------------------
    print("✨ Cleaning Orders...")
    df_orders = spark.table("orders_bronze")
    
    # Cast timestamps
    df_orders = (df_orders
        .withColumn("order_purchase_timestamp", to_timestamp("order_purchase_timestamp"))
        .withColumn("order_approved_at", to_timestamp("order_approved_at"))
        .withColumn("order_delivered_customer_date", to_timestamp("order_delivered_customer_date"))
        .withColumn("order_estimated_delivery_date", to_timestamp("order_estimated_delivery_date"))
    )
    
    # Business Logic: Fill null approval date with purchase date
    df_orders = df_orders.withColumn(
        "order_approved_at",
        coalesce(col("order_approved_at"), col("order_purchase_timestamp"))
    )
    
    # Register Silver View
    df_orders.createOrReplaceTempView("orders_silver")
    
    # ---------------------------------------------------------
    # 2. CLEAN ORDER ITEMS
    # Logic: Convert price/freight to Double
    # ---------------------------------------------------------
    print("✨ Cleaning Order Items...")
    df_items = spark.table("order_items_bronze")
    
    df_items = (df_items
        .withColumn("price", col("price").cast(DoubleType()))
        .withColumn("freight_value", col("freight_value").cast(DoubleType()))
    )
    
    df_items.createOrReplaceTempView("order_items_silver")

    # ---------------------------------------------------------
    # 3. CLEAN PRODUCTS
    # Logic: Join with Translations to get English names
    # ---------------------------------------------------------
    print("✨ Cleaning Products...")
    df_products = spark.table("products_bronze")
    df_translations = spark.table("category_translation_bronze")
    
    # Handle null categories
    df_products = df_products.fillna({"product_category_name": "unknown"})
    
    # Join
    df_products_enriched = df_products.join(
        df_translations, 
        "product_category_name", 
        "left"
    ).select(
        df_products["*"],
        # Use English name if available, else 'Unknown'
        coalesce(col("product_category_name_english"), lit("Unknown")).alias("category_name")
    )
    
    df_products_enriched.createOrReplaceTempView("products_silver")
    
    print("✅ Silver Views Created: orders_silver, order_items_silver, products_silver")