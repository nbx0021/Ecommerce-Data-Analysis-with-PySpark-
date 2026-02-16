# src/gold/aggregate.py
from pyspark.sql.functions import (
    col, datediff, avg, sum, count, round, lit, 
    max, current_date, date_trunc, when, countDistinct
)

def aggregate_gold_layer(spark):
    print("\n--- 🏆 GOLD LAYER (Advanced Analytics) ---")

    # ---------------------------------------------------------
    # 1. DELIVERY PERFORMANCE (Logistics)
    # Question: "Are we delivering late? What is the average delay?"
    # ---------------------------------------------------------
    print("📊 [1/4] Aggregating Delivery Metrics...")
    df_orders = spark.table("orders_silver")
    
    # Filter only delivered orders
    df_delivered = df_orders.filter(col("order_delivered_customer_date").isNotNull())
    
    # Calculate Days
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
        count("*").alias("total_delivered_orders")
    )
    
    df_gold_delivery.createOrReplaceTempView("gold_logistics_performance")

    # ---------------------------------------------------------
    # 2. MONTHLY SALES TREND (Finance)
    # Question: "Is the business growing?"
    # ---------------------------------------------------------
    print("📊 [2/4] Aggregating Monthly Sales Trends...")
    df_items = spark.table("order_items_silver")
    df_orders = spark.table("orders_silver")
    
    # Join Orders + Items to get Date + Price
    df_trend = df_orders.join(df_items, "order_id") \
        .withColumn("month", date_trunc("month", col("order_purchase_timestamp"))) \
        .groupBy("month") \
        .agg(
            round(sum("price"), 2).alias("total_revenue"),
            countDistinct("order_id").alias("total_orders")
        ) \
        .orderBy("month")
        
    df_trend.createOrReplaceTempView("gold_monthly_sales")

    # ---------------------------------------------------------
    # 3. SALES BY CATEGORY (Product)
    # Question: "Which categories drive the most revenue?"
    # ---------------------------------------------------------
    print("📊 [3/4] Aggregating Product Performance...")
    df_products = spark.table("products_silver")
    # (Reusing df_items from above)
    
    df_cat_sales = df_items.join(df_products, "product_id") \
        .groupBy("category_name") \
        .agg(
            round(sum("price"), 2).alias("total_revenue"),
            count("order_id").alias("total_items_sold"),
            round(avg("price"), 2).alias("avg_item_price")
        ) \
        .orderBy(col("total_revenue").desc())
        
    df_cat_sales.createOrReplaceTempView("gold_product_performance")

    # ---------------------------------------------------------
    # 4. RFM SEGMENTATION (Marketing)
    # Question: "Who are our Champions vs. At-Risk customers?"
    # ---------------------------------------------------------
    print("📊 [4/4] Calculating Customer RFM Segments...")
    df_customers = spark.table("customers_bronze") # Need unique IDs from here
    
    # Base RFM Table: Join Orders -> Items -> Customers
    rfm_base = df_orders.join(df_items, "order_id") \
        .join(df_customers, "customer_id") \
        .groupBy("customer_unique_id") \
        .agg(
            max("order_purchase_timestamp").alias("last_purchase_date"),
            countDistinct("order_id").alias("frequency"),
            sum("price").alias("monetary")
        ) \
        .withColumn("recency_days", datediff(current_date(), col("last_purchase_date")))

    # RFM Scoring Logic (Simple Rule-Based)
    # Champion: Bought recently (<90 days) AND frequently (>1 order)
    # Loyal: Bought frequently but not recently
    # Big Spender: Spent a lot (> $500)
    # New: Bought recently, but only once
    # Lost: Bought long ago (> 90 days)
    
    rfm_segmented = rfm_base.withColumn(
        "customer_segment",
        when((col("recency_days") < 90) & (col("frequency") >= 2), "Champion")
        .when((col("monetary") >= 500), "Big Spender")
        .when((col("recency_days") < 90), "New Customer")
        .when((col("frequency") >= 2), "Loyal - At Risk")
        .otherwise("Lost / Hibernating")
    )
    
    # Aggregate counts per segment for the final report
    df_rfm_summary = rfm_segmented.groupBy("customer_segment") \
        .agg(
            count("customer_unique_id").alias("customer_count"),
            round(avg("monetary"), 2).alias("avg_spend")
        ) \
        .orderBy(col("avg_spend").desc())

    df_rfm_summary.createOrReplaceTempView("gold_customer_segments")

    print("✅ Gold Views Created: gold_logistics_performance, gold_monthly_sales, gold_product_performance, gold_customer_segments")