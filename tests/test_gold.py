# tests/test_gold.py
"""
Unit tests for Gold Layer aggregation logic.
Tests RFM segmentation, delivery metrics, and payment analysis.
"""
import pytest
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, TimestampType
)
from datetime import datetime


class TestGoldAggregations:
    """Tests for aggregate_gold_layer()."""

    def _setup_silver_views(self, spark):
        """Create all required Silver mock views for Gold layer tests."""
        # Orders Silver (already cleaned/typed)
        orders_data = [
            ("ord1", "c1", "delivered",
             datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10),
             datetime(2023, 1, 3, 10), datetime(2023, 1, 5, 10), datetime(2023, 1, 8, 10)),
            ("ord2", "c1", "delivered",
             datetime(2023, 2, 1, 10), datetime(2023, 2, 1, 10),
             datetime(2023, 2, 3, 10), datetime(2023, 2, 5, 10), datetime(2023, 2, 4, 10)),
            ("ord3", "c2", "delivered",
             datetime(2023, 1, 15, 10), datetime(2023, 1, 15, 10),
             datetime(2023, 1, 17, 10), datetime(2023, 1, 20, 10), datetime(2023, 1, 25, 10)),
        ]
        orders_schema = StructType([
            StructField("order_id", StringType()),
            StructField("customer_id", StringType()),
            StructField("order_status", StringType()),
            StructField("order_purchase_timestamp", TimestampType()),
            StructField("order_approved_at", TimestampType()),
            StructField("order_delivered_carrier_date", TimestampType()),
            StructField("order_delivered_customer_date", TimestampType()),
            StructField("order_estimated_delivery_date", TimestampType()),
        ])
        spark.createDataFrame(orders_data, orders_schema).createOrReplaceTempView("orders_silver")

        # Order Items Silver
        items_data = [
            ("ord1", "1", "p1", "s1", "2023-01-03", 100.0, 10.0),
            ("ord2", "1", "p1", "s1", "2023-02-03", 200.0, 15.0),
            ("ord3", "1", "p2", "s2", "2023-01-17", 300.0, 20.0),
        ]
        items_schema = StructType([
            StructField("order_id", StringType()),
            StructField("order_item_id", StringType()),
            StructField("product_id", StringType()),
            StructField("seller_id", StringType()),
            StructField("shipping_limit_date", StringType()),
            StructField("price", DoubleType()),
            StructField("freight_value", DoubleType()),
        ])
        spark.createDataFrame(items_data, items_schema).createOrReplaceTempView("order_items_silver")

        # Products Silver
        products_data = [("p1", "health_beauty"), ("p2", "electronics")]
        products_schema = StructType([
            StructField("product_id", StringType()),
            StructField("category_name", StringType()),
        ])
        spark.createDataFrame(products_data, products_schema).createOrReplaceTempView("products_silver")

        # Customers Silver
        cust_data = [
            ("c1", "u1", "01310", "sao paulo", "SP"),
            ("c2", "u2", "20040", "rio de janeiro", "RJ"),
        ]
        cust_schema = StructType([
            StructField("customer_id", StringType()),
            StructField("customer_unique_id", StringType()),
            StructField("customer_zip_code_prefix", StringType()),
            StructField("customer_city", StringType()),
            StructField("customer_state", StringType()),
        ])
        spark.createDataFrame(cust_data, cust_schema).createOrReplaceTempView("customers_silver")

        # Payments Silver
        pay_data = [
            ("ord1", 1, "credit_card", 3, 100.0),
            ("ord2", 1, "boleto", 1, 200.0),
            ("ord3", 1, "credit_card", 2, 300.0),
        ]
        pay_schema = StructType([
            StructField("order_id", StringType()),
            StructField("payment_sequential", IntegerType()),
            StructField("payment_type", StringType()),
            StructField("payment_installments", IntegerType()),
            StructField("payment_value", DoubleType()),
        ])
        spark.createDataFrame(pay_data, pay_schema).createOrReplaceTempView("payments_silver")

        # Sellers Silver
        seller_data = [("s1", "01310", "sao paulo", "SP"), ("s2", "20040", "rio", "RJ")]
        seller_schema = StructType([
            StructField("seller_id", StringType()),
            StructField("seller_zip_code_prefix", StringType()),
            StructField("seller_city", StringType()),
            StructField("seller_state", StringType()),
        ])
        spark.createDataFrame(seller_data, seller_schema).createOrReplaceTempView("sellers_silver")

        # Reviews Silver
        reviews_data = [
            ("r1", "ord1", 5, "Great", "Loved it!", datetime(2023, 1, 6), datetime(2023, 1, 7)),
            ("r2", "ord2", 4, "", "", datetime(2023, 2, 6), datetime(2023, 2, 7)),
            ("r3", "ord3", 2, "Bad", "Didn't work", datetime(2023, 1, 21), datetime(2023, 1, 22)),
        ]
        reviews_schema = StructType([
            StructField("review_id", StringType()),
            StructField("order_id", StringType()),
            StructField("review_score", IntegerType()),
            StructField("review_comment_title", StringType()),
            StructField("review_comment_message", StringType()),
            StructField("review_creation_date", TimestampType()),
            StructField("review_answer_timestamp", TimestampType()),
        ])
        spark.createDataFrame(reviews_data, reviews_schema).createOrReplaceTempView("reviews_silver")

    def test_gold_views_created(self, spark):
        """All 7 Gold views should be created."""
        self._setup_silver_views(spark)
        from src.gold.aggregate import aggregate_gold_layer
        aggregate_gold_layer(spark)

        expected_views = [
            "gold_logistics_performance", "gold_monthly_sales",
            "gold_product_performance", "gold_customer_segments",
            "gold_payment_analysis", "gold_seller_performance",
            "gold_review_insights"
        ]
        views = [row.viewName for row in spark.sql("SHOW VIEWS").collect()]
        for v in expected_views:
            assert v in views, f"Missing Gold view: {v}"

    def test_delivery_metrics_calculated(self, spark):
        """Delivery metrics should have non-null values."""
        self._setup_silver_views(spark)
        from src.gold.aggregate import aggregate_gold_layer
        aggregate_gold_layer(spark)

        df = spark.table("gold_logistics_performance")
        row = df.collect()[0]
        assert row["avg_delivery_days"] is not None
        assert row["total_delivered_orders"] == 3

    def test_rfm_segmentation(self, spark):
        """RFM should produce customer segments."""
        self._setup_silver_views(spark)
        from src.gold.aggregate import aggregate_gold_layer
        aggregate_gold_layer(spark)

        df = spark.table("gold_customer_segments")
        assert df.count() > 0
        segments = [row["customer_segment"] for row in df.collect()]
        # All segments should be valid
        valid_segments = {"Champion", "Big Spender", "New Customer", "Loyal - At Risk", "Lost / Hibernating"}
        for s in segments:
            assert s in valid_segments, f"Invalid segment: {s}"

    def test_payment_analysis(self, spark):
        """Payment analysis should break down by payment type."""
        self._setup_silver_views(spark)
        from src.gold.aggregate import aggregate_gold_layer
        aggregate_gold_layer(spark)

        df = spark.table("gold_payment_analysis")
        types = [row["payment_type"] for row in df.collect()]
        assert "credit_card" in types
        assert "boleto" in types

    def test_product_performance(self, spark):
        """Product performance should show revenue by category."""
        self._setup_silver_views(spark)
        from src.gold.aggregate import aggregate_gold_layer
        aggregate_gold_layer(spark)

        df = spark.table("gold_product_performance")
        assert df.count() == 2  # health_beauty and electronics
        top_row = df.collect()[0]
        assert top_row["total_revenue"] > 0
