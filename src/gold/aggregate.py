# src/gold/aggregate.py
"""
Gold Layer — Business-Level Aggregations and KPIs.
All inputs read from Silver layer (proper Medallion lineage).
Includes caching for frequently-joined DataFrames.
"""
from pyspark.sql.functions import (
    col, datediff, avg, sum, count, round, lit,
    max, current_date, date_trunc, when, countDistinct
)
from src.utils.logger import get_logger
from src.utils.data_quality import check_row_count

logger = get_logger("gold.aggregate")


def aggregate_gold_layer(spark):
    """
    Builds all Gold-layer aggregations from Silver views.
    Creates 7 Gold views for executive reporting.
    """
    logger.info("━━━ 🏆 GOLD LAYER (Advanced Analytics) ━━━")

    # ─── Load shared Silver tables ───────────────────────────
    # Note: .cache() is not supported on Databricks CE serverless
    df_orders = spark.table("orders_silver")
    df_items = spark.table("order_items_silver")
    df_products = spark.table("products_silver")

    # ─────────────────────────────────────────────────────────
    # 1. DELIVERY PERFORMANCE (Logistics)
    # "Are we delivering late? What is the average delay?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [1/7] Aggregating Delivery Metrics...")

    df_delivered = df_orders.filter(col("order_delivered_customer_date").isNotNull())

    df_perf = df_delivered.withColumn(
        "actual_days",
        datediff(col("order_delivered_customer_date"), col("order_purchase_timestamp"))
    ).withColumn(
        "estimated_days",
        datediff(col("order_estimated_delivery_date"), col("order_purchase_timestamp"))
    )

    df_gold_delivery = df_perf.select(
        round(avg("actual_days"), 2).alias("avg_delivery_days"),
        round(avg("estimated_days"), 2).alias("avg_estimated_days"),
        round(avg(col("actual_days") - col("estimated_days")), 2).alias("avg_delay_vs_estimate"),
        count("*").alias("total_delivered_orders"),
        # NEW: On-time delivery rate
        round(
            count(when(col("actual_days") <= col("estimated_days"), 1)) / count("*") * 100, 2
        ).alias("on_time_delivery_pct")
    )

    df_gold_delivery.createOrReplaceTempView("gold_logistics_performance")

    # ─────────────────────────────────────────────────────────
    # 2. MONTHLY SALES TREND (Finance)
    # "Is the business growing month over month?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [2/7] Aggregating Monthly Sales Trends...")

    df_trend = df_orders.join(df_items, "order_id") \
        .withColumn("month", date_trunc("month", col("order_purchase_timestamp"))) \
        .groupBy("month") \
        .agg(
            round(sum("price"), 2).alias("total_revenue"),
            round(sum("freight_value"), 2).alias("total_freight"),
            countDistinct("order_id").alias("total_orders"),
            round(sum("price") / countDistinct("order_id"), 2).alias("avg_order_value")
        ) \
        .orderBy("month")

    df_trend.createOrReplaceTempView("gold_monthly_sales")

    # ─────────────────────────────────────────────────────────
    # 3. SALES BY CATEGORY (Product)
    # "Which categories drive the most revenue?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [3/7] Aggregating Product Performance...")

    df_cat_sales = df_items.join(df_products, "product_id") \
        .groupBy("category_name") \
        .agg(
            round(sum("price"), 2).alias("total_revenue"),
            count("order_id").alias("total_items_sold"),
            round(avg("price"), 2).alias("avg_item_price"),
            round(sum("freight_value"), 2).alias("total_freight_cost")
        ) \
        .orderBy(col("total_revenue").desc())

    df_cat_sales.createOrReplaceTempView("gold_product_performance")

    # ─────────────────────────────────────────────────────────
    # 4. RFM SEGMENTATION (Marketing)
    # "Who are our Champions vs. At-Risk customers?"
    # FIXED: Now reads from customers_silver (was customers_bronze)
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [4/7] Calculating Customer RFM Segments...")
    df_customers = spark.table("customers_silver")

    rfm_base = df_orders.join(df_items, "order_id") \
        .join(df_customers, "customer_id") \
        .groupBy("customer_unique_id") \
        .agg(
            max("order_purchase_timestamp").alias("last_purchase_date"),
            countDistinct("order_id").alias("frequency"),
            round(sum("price"), 2).alias("monetary")
        ) \
        .withColumn("recency_days", datediff(current_date(), col("last_purchase_date")))

    # RFM Scoring Logic (Rule-Based)
    rfm_segmented = rfm_base.withColumn(
        "customer_segment",
        when((col("recency_days") < 90) & (col("frequency") >= 2), "Champion")
        .when((col("monetary") >= 500), "Big Spender")
        .when((col("recency_days") < 90), "New Customer")
        .when((col("frequency") >= 2), "Loyal - At Risk")
        .otherwise("Lost / Hibernating")
    )

    df_rfm_summary = rfm_segmented.groupBy("customer_segment") \
        .agg(
            count("customer_unique_id").alias("customer_count"),
            round(avg("monetary"), 2).alias("avg_spend"),
            round(avg("recency_days"), 0).alias("avg_recency_days"),
            round(avg("frequency"), 1).alias("avg_frequency")
        ) \
        .orderBy(col("avg_spend").desc())

    df_rfm_summary.createOrReplaceTempView("gold_customer_segments")

    # ─────────────────────────────────────────────────────────
    # 5. PAYMENT ANALYSIS (Finance)
    # "How do customers prefer to pay?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [5/7] Aggregating Payment Analysis...")
    df_payments = spark.table("payments_silver")

    df_pay_analysis = df_payments.groupBy("payment_type") \
        .agg(
            count("*").alias("transaction_count"),
            round(sum("payment_value"), 2).alias("total_value"),
            round(avg("payment_value"), 2).alias("avg_value"),
            round(avg("payment_installments"), 1).alias("avg_installments")
        ) \
        .orderBy(col("total_value").desc())

    df_pay_analysis.createOrReplaceTempView("gold_payment_analysis")

    # ─────────────────────────────────────────────────────────
    # 6. SELLER PERFORMANCE
    # "Who are the top sellers? Who delivers slowest?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [6/7] Aggregating Seller Performance...")
    df_sellers = spark.table("sellers_silver")

    df_seller_perf = df_items.join(df_sellers, "seller_id") \
        .join(df_orders, "order_id") \
        .groupBy("seller_id", "seller_city", "seller_state") \
        .agg(
            round(sum("price"), 2).alias("total_revenue"),
            countDistinct("order_id").alias("total_orders"),
            round(avg("price"), 2).alias("avg_item_price")
        ) \
        .orderBy(col("total_revenue").desc())

    df_seller_perf.createOrReplaceTempView("gold_seller_performance")

    # ─────────────────────────────────────────────────────────
    # 7. REVIEW INSIGHTS
    # "Which categories get the best/worst reviews?"
    # ─────────────────────────────────────────────────────────
    logger.info("📊 [7/7] Aggregating Review Insights...")
    df_reviews = spark.table("reviews_silver")

    df_review_insights = df_reviews.join(df_orders, "order_id") \
        .join(df_items, "order_id") \
        .join(df_products, "product_id") \
        .groupBy("category_name") \
        .agg(
            round(avg("review_score"), 2).alias("avg_review_score"),
            count("review_id").alias("total_reviews"),
            round(
                count(when(col("review_score") >= 4, 1)) / count("*") * 100, 2
            ).alias("positive_review_pct")
        ) \
        .orderBy(col("avg_review_score").desc())

    df_review_insights.createOrReplaceTempView("gold_review_insights")


    logger.info(
        "✅ Gold Views Created: gold_logistics_performance, gold_monthly_sales, "
        "gold_product_performance, gold_customer_segments, gold_payment_analysis, "
        "gold_seller_performance, gold_review_insights"
    )