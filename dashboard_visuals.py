# dashboard_visuals.py
"""
Executive Dashboard — Industry-Grade Visualizations.
Displays all 7 Gold-layer KPIs using Databricks native display().

USAGE ON DATABRICKS:
  1. Run the pipeline first (trigger_pipeline notebook)
  2. Create a NEW notebook, paste the content of this file
  3. Run All
  4. Switch to "Dashboard" view to see the visualizations

Each display() call creates a separate panel that can be
configured in Databricks' built-in visualization editor.
"""
import sys
import os

# ─── Deep Reload for fresh imports ──────────────────────────
repo_root = os.getcwd()
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

for mod in [k for k in list(sys.modules.keys()) if k.startswith('src') or k == 'main_pipeline']:
    del sys.modules[mod]

import main_pipeline
main_pipeline.run_pipeline()

print("--- 🚀 EXECUTIVE DASHBOARD ---")

# =============================================================
# VISUAL 1: KPI Summary — Key Business Metrics
# Best Visual: Counter / Big Number
# =============================================================
print("\n📊 1. Logistics KPIs")
df_logistics = spark.sql("""
    SELECT 
        avg_delivery_days, 
        avg_estimated_days, 
        avg_delay_vs_estimate,
        on_time_delivery_pct,
        total_delivered_orders
    FROM gold_logistics_performance
""")
display(df_logistics)
# 🎨 Plot Setup:
# - Visualization Type: Counter
# - Value: avg_delivery_days
# - Target: avg_estimated_days
# - Label: "Avg Delivery Days"

# =============================================================
# VISUAL 2: Monthly Revenue & Orders Trend (Dual Axis)
# Best Visual: Line Chart (dual Y-axis)
# =============================================================
print("\n📊 2. Monthly Revenue & Orders Trend")
df_trend = spark.sql("""
    SELECT 
        month,
        total_revenue,
        total_orders,
        avg_order_value,
        total_freight
    FROM gold_monthly_sales 
    ORDER BY month
""")
display(df_trend)
# 🎨 Plot Setup:
# - Visualization Type: Line Chart
# - X Column: month
# - Y Columns: total_revenue (Left Y), total_orders (Right Y)
# - This shows revenue growth AND order volume on same chart

# =============================================================
# VISUAL 3: Customer Segments (RFM) — Distribution
# Best Visual: Pie Chart or Stacked Bar
# =============================================================
print("\n📊 3. Customer Segments (RFM Analysis)")
df_rfm = spark.sql("""
    SELECT 
        customer_segment,
        customer_count,
        avg_spend,
        avg_recency_days,
        avg_frequency
    FROM gold_customer_segments 
    ORDER BY avg_spend DESC
""")
display(df_rfm)
# 🎨 Plot Setup:
# - Visualization Type: Pie Chart
# - Values: customer_count
# - Group By: customer_segment
# - Alt: Bar Chart with customer_segment on X, customer_count on Y

# =============================================================
# VISUAL 4: Top 10 Product Categories by Revenue
# Best Visual: Horizontal Bar Chart
# =============================================================
print("\n📊 4. Top Product Categories by Revenue")
df_products = spark.sql("""
    SELECT 
        category_name,
        total_revenue,
        total_items_sold,
        avg_item_price,
        total_freight_cost
    FROM gold_product_performance 
    LIMIT 10
""")
display(df_products)
# 🎨 Plot Setup:
# - Visualization Type: Bar Chart (Horizontal)
# - X Column: total_revenue
# - Y Column: category_name
# - Color: Use gradient to highlight top categories

# =============================================================
# VISUAL 5: Payment Method Distribution
# Best Visual: Pie Chart or Donut Chart
# =============================================================
print("\n📊 5. Payment Method Analysis")
df_payments = spark.sql("""
    SELECT 
        payment_type,
        transaction_count,
        total_value,
        avg_value,
        avg_installments
    FROM gold_payment_analysis
    ORDER BY total_value DESC
""")
display(df_payments)
# 🎨 Plot Setup:
# - Visualization Type: Pie Chart / Donut
# - Values: total_value
# - Group By: payment_type
# - Shows: Which payment methods dominate

# =============================================================
# VISUAL 6: Top 15 Sellers by Revenue
# Best Visual: Bar Chart
# =============================================================
print("\n📊 6. Top Sellers by Revenue")
df_sellers = spark.sql("""
    SELECT 
        seller_id,
        seller_city,
        seller_state,
        total_revenue,
        total_orders,
        avg_item_price
    FROM gold_seller_performance
    LIMIT 15
""")
display(df_sellers)
# 🎨 Plot Setup:
# - Visualization Type: Bar Chart
# - X Column: seller_city (or seller_id)
# - Y Column: total_revenue
# - Color By: seller_state

# =============================================================
# VISUAL 7: Review Scores by Category — Sentiment Analysis
# Best Visual: Bar Chart with color gradient
# =============================================================
print("\n📊 7. Category Review Insights")
df_reviews = spark.sql("""
    SELECT 
        category_name,
        avg_review_score,
        total_reviews,
        positive_review_pct
    FROM gold_review_insights
    WHERE total_reviews >= 50
    ORDER BY avg_review_score DESC
    LIMIT 15
""")
display(df_reviews)
# 🎨 Plot Setup:
# - Visualization Type: Bar Chart
# - X Column: category_name
# - Y Column: avg_review_score
# - Color intensity: positive_review_pct
# - Filter: categories with 50+ reviews for statistical significance

# =============================================================
# VISUAL 8: Revenue vs Review Score — Scatter Plot
# Best Visual: Scatter / Bubble Chart
# =============================================================
print("\n📊 8. Revenue vs Customer Satisfaction")
df_rev_review = spark.sql("""
    SELECT 
        p.category_name,
        p.total_revenue,
        p.total_items_sold,
        r.avg_review_score,
        r.positive_review_pct
    FROM gold_product_performance p
    JOIN gold_review_insights r ON p.category_name = r.category_name
    WHERE r.total_reviews >= 30
    ORDER BY p.total_revenue DESC
    LIMIT 20
""")
display(df_rev_review)
# 🎨 Plot Setup:
# - Visualization Type: Scatter Plot / Bubble Chart
# - X Column: total_revenue
# - Y Column: avg_review_score
# - Bubble Size: total_items_sold
# - Labels: category_name
# - Insight: High-revenue + low-review = problem categories to fix

print("\n✅ Dashboard loaded — switch to 'Dashboard' view to see all visualizations")
