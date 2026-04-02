# src/silver/clean.py
"""
Silver Layer — Data Cleaning, Type Casting, and Enrichment.
Cleans ALL Bronze tables (not just orders/items/products).
Includes data quality validation after each transformation.

NOTE: Uses spark.sql() instead of spark.table() for Databricks CE
serverless compatibility (Spark Connect can block spark.table).
"""
from pyspark.sql.functions import (
    col, when, to_timestamp, coalesce, lit, 
    trim, lower, upper, to_date
)
from pyspark.sql.types import DoubleType, IntegerType
from src.utils.logger import get_logger
from src.utils.data_quality import check_row_count, check_nulls

logger = get_logger("silver.clean")


def _read_view(spark, view_name):
    """Read a temp view using spark.sql() for serverless compatibility."""
    return spark.sql(f"SELECT * FROM {view_name}")


def clean_silver_layer(spark):
    """
    Transforms all Bronze views into Silver views with:
    - Type casting (strings → timestamps, doubles, ints)
    - NULL handling with business logic
    - Deduplication where applicable
    - Data quality checks
    """
    logger.info("━━━ 🧹 SILVER LAYER (In-Memory) ━━━")

    # ─────────────────────────────────────────────────────────
    # 1. CLEAN ORDERS
    # Logic: Convert strings to timestamps, handle nulls
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [1/7] Cleaning Orders...")
    df_orders = _read_view(spark, "orders_bronze")

    # Cast all timestamp columns
    timestamp_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date", 
        "order_estimated_delivery_date"
    ]
    for tc in timestamp_cols:
        df_orders = df_orders.withColumn(tc, to_timestamp(tc))

    # Business Logic: Fill null approval date with purchase date
    df_orders = df_orders.withColumn(
        "order_approved_at",
        coalesce(col("order_approved_at"), col("order_purchase_timestamp"))
    )

    df_orders.createOrReplaceTempView("orders_silver")
    check_row_count(df_orders, "orders_silver")
    check_nulls(df_orders, ["order_id", "customer_id"], "orders_silver")

    # ─────────────────────────────────────────────────────────
    # 2. CLEAN ORDER ITEMS
    # Logic: Cast price/freight to Double
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [2/7] Cleaning Order Items...")
    df_items = _read_view(spark, "order_items_bronze")

    df_items = (df_items
        .withColumn("price", col("price").cast(DoubleType()))
        .withColumn("freight_value", col("freight_value").cast(DoubleType()))
    )

    df_items.createOrReplaceTempView("order_items_silver")
    check_row_count(df_items, "order_items_silver")

    # ─────────────────────────────────────────────────────────
    # 3. CLEAN PRODUCTS (with English category translation)
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [3/7] Cleaning Products...")
    df_products = _read_view(spark, "products_bronze")
    df_translations = _read_view(spark, "category_translation_bronze")

    # Handle null categories
    df_products = df_products.fillna({"product_category_name": "unknown"})

    # Join with translations
    df_products_enriched = df_products.join(
        df_translations,
        "product_category_name",
        "left"
    ).select(
        df_products["*"],
        coalesce(col("product_category_name_english"), lit("Unknown")).alias("category_name")
    )

    df_products_enriched.createOrReplaceTempView("products_silver")
    check_row_count(df_products_enriched, "products_silver")

    # ─────────────────────────────────────────────────────────
    # 4. CLEAN CUSTOMERS (deduplicate by customer_unique_id)
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [4/7] Cleaning Customers...")
    df_customers = _read_view(spark, "customers_bronze")

    # Standardize city names
    df_customers = (df_customers
        .withColumn("customer_city", trim(lower(col("customer_city"))))
        .withColumn("customer_state", trim(upper(col("customer_state"))))
    )

    # Deduplicate: keep first occurrence per customer_unique_id
    df_customers = df_customers.dropDuplicates(["customer_unique_id"])

    df_customers.createOrReplaceTempView("customers_silver")
    check_row_count(df_customers, "customers_silver")

    # ─────────────────────────────────────────────────────────
    # 5. CLEAN PAYMENTS (cast values, validate types)
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [5/7] Cleaning Payments...")
    df_payments = _read_view(spark, "order_payments_bronze")

    df_payments = (df_payments
        .withColumn("payment_value", col("payment_value").cast(DoubleType()))
        .withColumn("payment_installments", col("payment_installments").cast(IntegerType()))
        .withColumn("payment_sequential", col("payment_sequential").cast(IntegerType()))
    )

    # Validate payment_type against known values
    valid_types = ["credit_card", "boleto", "voucher", "debit_card", "not_defined"]
    df_payments = df_payments.withColumn(
        "payment_type",
        when(col("payment_type").isin(valid_types), col("payment_type"))
        .otherwise(lit("other"))
    )

    df_payments.createOrReplaceTempView("payments_silver")
    check_row_count(df_payments, "payments_silver")

    # ─────────────────────────────────────────────────────────
    # 6. CLEAN SELLERS (standardize city/state)
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [6/7] Cleaning Sellers...")
    df_sellers = _read_view(spark, "sellers_bronze")

    df_sellers = (df_sellers
        .withColumn("seller_city", trim(lower(col("seller_city"))))
        .withColumn("seller_state", trim(upper(col("seller_state"))))
    )

    df_sellers.createOrReplaceTempView("sellers_silver")
    check_row_count(df_sellers, "sellers_silver")

    # ─────────────────────────────────────────────────────────
    # 7. CLEAN REVIEWS (cast score, handle null comments)
    # ─────────────────────────────────────────────────────────
    logger.info("✨ [7/7] Cleaning Reviews...")
    df_reviews = _read_view(spark, "order_reviews_bronze")

    df_reviews = (df_reviews
        .withColumn("review_score", col("review_score").cast(IntegerType()))
        .withColumn("review_creation_date", to_timestamp("review_creation_date"))
        .withColumn("review_answer_timestamp", to_timestamp("review_answer_timestamp"))
        .withColumn("review_comment_message",
            coalesce(col("review_comment_message"), lit(""))
        )
    )

    df_reviews.createOrReplaceTempView("reviews_silver")
    check_row_count(df_reviews, "reviews_silver")

    logger.info(
        "✅ Silver Views Created: orders_silver, order_items_silver, "
        "products_silver, customers_silver, payments_silver, "
        "sellers_silver, reviews_silver"
    )