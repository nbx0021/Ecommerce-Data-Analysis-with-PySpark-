# tests/test_silver.py
"""
Unit tests for Silver Layer cleaning logic.
Tests type casting, NULL handling, category enrichment, and deduplication.
"""
import pytest
from pyspark.sql.types import StructType, StructField, StringType


class TestSilverOrders:
    """Tests for orders cleaning."""

    def _setup_bronze_views(self, spark):
        """Create all required Bronze mock views."""
        # Orders
        orders_schema = StructType([
            StructField("order_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("order_status", StringType(), True),
            StructField("order_purchase_timestamp", StringType(), True),
            StructField("order_approved_at", StringType(), True),
            StructField("order_delivered_carrier_date", StringType(), True),
            StructField("order_delivered_customer_date", StringType(), True),
            StructField("order_estimated_delivery_date", StringType(), True),
        ])
        orders_data = [
            ("ord1", "c1", "delivered", "2023-01-01 10:00:00", None, 
             "2023-01-03 10:00:00", "2023-01-05 10:00:00", "2023-01-06 10:00:00"),
            ("ord2", "c2", "delivered", "2023-01-02 10:00:00", "2023-01-02 10:05:00",
             "2023-01-04 10:00:00", "2023-01-05 10:00:00", "2023-01-06 10:00:00"),
        ]
        spark.createDataFrame(orders_data, orders_schema).createOrReplaceTempView("orders_bronze")

        # Order Items
        items_schema = StructType([
            StructField("order_id", StringType(), True),
            StructField("order_item_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("seller_id", StringType(), True),
            StructField("shipping_limit_date", StringType(), True),
            StructField("price", StringType(), True),
            StructField("freight_value", StringType(), True),
        ])
        items_data = [
            ("ord1", "1", "p1", "s1", "2023-01-03 10:00:00", "99.99", "12.50"),
            ("ord2", "1", "p2", "s2", "2023-01-04 10:00:00", "50.00", "8.00"),
        ]
        spark.createDataFrame(items_data, items_schema).createOrReplaceTempView("order_items_bronze")

        # Products
        products_schema = StructType([
            StructField("product_id", StringType(), True),
            StructField("product_category_name", StringType(), True),
        ])
        products_data = [("p1", "beleza_saude"), ("p2", None)]
        spark.createDataFrame(products_data, products_schema).createOrReplaceTempView("products_bronze")

        # Category Translation
        trans_schema = StructType([
            StructField("product_category_name", StringType(), True),
            StructField("product_category_name_english", StringType(), True),
        ])
        trans_data = [("beleza_saude", "health_beauty")]
        spark.createDataFrame(trans_data, trans_schema).createOrReplaceTempView("category_translation_bronze")

        # Customers
        cust_schema = StructType([
            StructField("customer_id", StringType(), True),
            StructField("customer_unique_id", StringType(), True),
            StructField("customer_zip_code_prefix", StringType(), True),
            StructField("customer_city", StringType(), True),
            StructField("customer_state", StringType(), True),
        ])
        cust_data = [
            ("c1", "u1", "01310", "  Sao Paulo  ", "sp"),
            ("c2", "u1", "01310", "Sao Paulo", "SP"),  # duplicate customer_unique_id
            ("c3", "u2", "20040", "Rio De Janeiro", "rj"),
        ]
        spark.createDataFrame(cust_data, cust_schema).createOrReplaceTempView("customers_bronze")

        # Payments
        pay_schema = StructType([
            StructField("order_id", StringType(), True),
            StructField("payment_sequential", StringType(), True),
            StructField("payment_type", StringType(), True),
            StructField("payment_installments", StringType(), True),
            StructField("payment_value", StringType(), True),
        ])
        pay_data = [
            ("ord1", "1", "credit_card", "3", "99.99"),
            ("ord2", "1", "boleto", "1", "50.00"),
            ("ord2", "2", "unknown_type", "1", "10.00"),
        ]
        spark.createDataFrame(pay_data, pay_schema).createOrReplaceTempView("order_payments_bronze")

        # Sellers
        seller_schema = StructType([
            StructField("seller_id", StringType(), True),
            StructField("seller_zip_code_prefix", StringType(), True),
            StructField("seller_city", StringType(), True),
            StructField("seller_state", StringType(), True),
        ])
        seller_data = [("s1", "01310", "  SAO PAULO  ", "sp"), ("s2", "20040", "rio", "rj")]
        spark.createDataFrame(seller_data, seller_schema).createOrReplaceTempView("sellers_bronze")

        # Reviews
        reviews_schema = StructType([
            StructField("review_id", StringType(), True),
            StructField("order_id", StringType(), True),
            StructField("review_score", StringType(), True),
            StructField("review_comment_title", StringType(), True),
            StructField("review_comment_message", StringType(), True),
            StructField("review_creation_date", StringType(), True),
            StructField("review_answer_timestamp", StringType(), True),
        ])
        reviews_data = [
            ("r1", "ord1", "5", "Great", "Loved it!", "2023-01-06 10:00:00", "2023-01-07 10:00:00"),
            ("r2", "ord2", "3", None, None, "2023-01-06 10:00:00", "2023-01-07 10:00:00"),
        ]
        spark.createDataFrame(reviews_data, reviews_schema).createOrReplaceTempView("order_reviews_bronze")

    def test_clean_orders_fills_nulls(self, spark):
        """NULL approval dates should be filled with purchase date."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        result = spark.sql(
            "SELECT order_approved_at FROM orders_silver WHERE order_id = 'ord1'"
        ).collect()[0][0]

        assert result is not None
        assert str(result) == "2023-01-01 10:00:00"

    def test_order_items_price_is_double(self, spark):
        """Price and freight should be cast to DoubleType."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        df = spark.table("order_items_silver")
        assert df.schema["price"].dataType.simpleString() == "double"
        assert df.schema["freight_value"].dataType.simpleString() == "double"

    def test_products_category_enriched(self, spark):
        """Products should have English category names."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        result = spark.sql(
            "SELECT category_name FROM products_silver WHERE product_id = 'p1'"
        ).collect()[0][0]
        assert result == "health_beauty"

    def test_products_unknown_category_handled(self, spark):
        """Products with NULL category should get 'Unknown'."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        result = spark.sql(
            "SELECT category_name FROM products_silver WHERE product_id = 'p2'"
        ).collect()[0][0]
        assert result == "Unknown"

    def test_customers_deduplicated(self, spark):
        """Customers should be deduplicated by customer_unique_id."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        count = spark.table("customers_silver").count()
        # 3 rows input, 2 unique customer_unique_ids (u1, u2)
        assert count == 2

    def test_payment_type_validated(self, spark):
        """Unknown payment types should be mapped to 'other'."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        result = spark.sql(
            "SELECT payment_type FROM payments_silver WHERE payment_value = 10.0"
        ).collect()[0][0]
        assert result == "other"

    def test_review_null_comments_handled(self, spark):
        """NULL review comments should be filled with empty string."""
        self._setup_bronze_views(spark)
        from src.silver.clean import clean_silver_layer
        clean_silver_layer(spark)

        result = spark.sql(
            "SELECT review_comment_message FROM reviews_silver WHERE review_id = 'r2'"
        ).collect()[0][0]
        assert result is not None
        assert result == ""
