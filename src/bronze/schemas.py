# src/bronze/schemas.py
"""
Explicit StructType schemas for all Olist datasets.
Applied after Pandas → Spark conversion to enforce types at Bronze layer.
"""
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, TimestampType
)

# ─── Orders ──────────────────────────────────────────────────
ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("order_status", StringType(), True),
    StructField("order_purchase_timestamp", StringType(), True),
    StructField("order_approved_at", StringType(), True),
    StructField("order_delivered_carrier_date", StringType(), True),
    StructField("order_delivered_customer_date", StringType(), True),
    StructField("order_estimated_delivery_date", StringType(), True),
])

# ─── Customers ───────────────────────────────────────────────
CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", StringType(), False),
    StructField("customer_unique_id", StringType(), False),
    StructField("customer_zip_code_prefix", StringType(), True),
    StructField("customer_city", StringType(), True),
    StructField("customer_state", StringType(), True),
])

# ─── Order Items ─────────────────────────────────────────────
ORDER_ITEMS_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("order_item_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("seller_id", StringType(), True),
    StructField("shipping_limit_date", StringType(), True),
    StructField("price", StringType(), True),
    StructField("freight_value", StringType(), True),
])

# ─── Order Payments ──────────────────────────────────────────
ORDER_PAYMENTS_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("payment_sequential", StringType(), True),
    StructField("payment_type", StringType(), True),
    StructField("payment_installments", StringType(), True),
    StructField("payment_value", StringType(), True),
])

# ─── Order Reviews ───────────────────────────────────────────
ORDER_REVIEWS_SCHEMA = StructType([
    StructField("review_id", StringType(), False),
    StructField("order_id", StringType(), False),
    StructField("review_score", StringType(), True),
    StructField("review_comment_title", StringType(), True),
    StructField("review_comment_message", StringType(), True),
    StructField("review_creation_date", StringType(), True),
    StructField("review_answer_timestamp", StringType(), True),
])

# ─── Products ────────────────────────────────────────────────
PRODUCTS_SCHEMA = StructType([
    StructField("product_id", StringType(), False),
    StructField("product_category_name", StringType(), True),
    StructField("product_name_lenght", StringType(), True),
    StructField("product_description_lenght", StringType(), True),
    StructField("product_photos_qty", StringType(), True),
    StructField("product_weight_g", StringType(), True),
    StructField("product_length_cm", StringType(), True),
    StructField("product_height_cm", StringType(), True),
    StructField("product_width_cm", StringType(), True),
])

# ─── Sellers ─────────────────────────────────────────────────
SELLERS_SCHEMA = StructType([
    StructField("seller_id", StringType(), False),
    StructField("seller_zip_code_prefix", StringType(), True),
    StructField("seller_city", StringType(), True),
    StructField("seller_state", StringType(), True),
])

# ─── Geolocation ─────────────────────────────────────────────
GEOLOCATION_SCHEMA = StructType([
    StructField("geolocation_zip_code_prefix", StringType(), True),
    StructField("geolocation_lat", StringType(), True),
    StructField("geolocation_lng", StringType(), True),
    StructField("geolocation_city", StringType(), True),
    StructField("geolocation_state", StringType(), True),
])

# ─── Category Translation ───────────────────────────────────
CATEGORY_TRANSLATION_SCHEMA = StructType([
    StructField("product_category_name", StringType(), False),
    StructField("product_category_name_english", StringType(), True),
])

# ─── Registry: table_name → schema mapping ──────────────────
SCHEMA_REGISTRY = {
    "customers": CUSTOMERS_SCHEMA,
    "orders": ORDERS_SCHEMA,
    "order_items": ORDER_ITEMS_SCHEMA,
    "order_payments": ORDER_PAYMENTS_SCHEMA,
    "order_reviews": ORDER_REVIEWS_SCHEMA,
    "products": PRODUCTS_SCHEMA,
    "sellers": SELLERS_SCHEMA,
    "geolocation": GEOLOCATION_SCHEMA,
    "category_translation": CATEGORY_TRANSLATION_SCHEMA,
}
