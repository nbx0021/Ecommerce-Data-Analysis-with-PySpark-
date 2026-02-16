from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd

def ingest_to_bronze(spark, source_path, table_name):
    """
    Ingests data to a Standard Temporary View (Session Scoped).
    This mimics exactly how a Notebook cell works.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # 1. READ (Pandas Bridge)
        clean_path = source_path.replace("file:", "")
        
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Data missing at: {clean_path}")

        pdf = pd.read_csv(clean_path, dtype=str)
        df = spark.createDataFrame(pdf)
        
        # Add Audit Columns
        df_enriched = df.withColumn("ingestion_timestamp", current_timestamp())

        # 2. REGISTER (Standard Temp View)
        # 🛑 OLD: createOrReplaceGlobalTempView (Blocked on Serverless)
        # ✅ NEW: createOrReplaceTempView (Supported everywhere)
        view_name = f"{table_name}_bronze"
        df_enriched.createOrReplaceTempView(view_name)
        
        print(f"✅ Success: Loaded '{view_name}' to Memory")
        
    except Exception as e:
        print(f"❌ Error ingesting {table_name}: {str(e)}")
        raise e