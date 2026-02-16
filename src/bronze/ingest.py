from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd

def ingest_to_bronze(spark, source_path, table_name):
    """
    Ingests data from CSV to Spark Memory (Global Temp View).
    Bypasses Community Edition storage restrictions by avoiding disk writes.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # 1. READ (Using Pandas, exactly like your Notebook)
        clean_path = source_path.replace("file:", "")
        
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Data missing at: {clean_path}")

        # Read as String first to ensure no schema crashes
        # (This mimics your notebook's safe approach)
        pdf = pd.read_csv(clean_path, dtype=str)
        
        # 2. CONVERT TO SPARK
        df = spark.createDataFrame(pdf)
        
        # Add Audit Columns
        df_enriched = df.withColumn("ingestion_timestamp", current_timestamp())

        # 3. REGISTER (The "In-Memory" Write)
        # Instead of writing to disk (Blocked), we save it to the Global Temp Database.
        # This makes it accessible across notebooks as 'global_temp.customers_bronze'
        view_name = f"{table_name}_bronze"
        df_enriched.createOrReplaceGlobalTempView(view_name)
        
        print(f"✅ Success: {table_name} -> Loaded to 'global_temp.{view_name}' (In-Memory)")
        
    except Exception as e:
        print(f"❌ Error ingesting {table_name}: {str(e)}")
        raise e