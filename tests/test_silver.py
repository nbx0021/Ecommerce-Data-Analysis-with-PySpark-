# tests/test_silver.py
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from src.silver.clean import clean_silver_layer

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("Test").getOrCreate()

def test_clean_orders_fills_nulls(spark):
    # 1. SETUP: Create Mock Bronze Data
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("order_purchase_timestamp", StringType(), True),
        StructField("order_approved_at", StringType(), True), # <--- This contains NULL
        StructField("order_delivered_customer_date", StringType(), True),
        StructField("order_estimated_delivery_date", StringType(), True)
    ])
    
    data = [
        ("ord1", "2023-01-01 10:00:00", None, "2023-01-05 10:00:00", "2023-01-06 10:00:00"),
        ("ord2", "2023-01-02 10:00:00", "2023-01-02 10:05:00", "2023-01-05 10:00:00", "2023-01-06 10:00:00")
    ]
    
    df_mock = spark.createDataFrame(data, schema)
    df_mock.createOrReplaceTempView("orders_bronze") # Register mock view
    
    # Mock other required views to avoid errors
    spark.createDataFrame([], schema=StructType([])).createOrReplaceTempView("order_items_bronze")
    spark.createDataFrame([], schema=StructType([])).createOrReplaceTempView("products_bronze")
    spark.createDataFrame([], schema=StructType([])).createOrReplaceTempView("category_translation_bronze")

    # 2. EXECUTE: Run your actual Cleaning Logic
    clean_silver_layer(spark)
    
    # 3. VERIFY: Check if logic worked
    # The logic says: If approved_at is NULL, use purchase_timestamp
    result = spark.sql("SELECT order_approved_at FROM orders_silver WHERE order_id = 'ord1'").collect()[0][0]
    
    # It should NOT be None anymore, it should match purchase date
    assert result is not None
    assert str(result) == "2023-01-01 10:00:00"
    print("✅ test_clean_orders_fills_nulls PASSED")

