from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd
from pathlib import Path

def ingest_to_bronze(spark, source_path, table_name):
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # 1. READ
        clean_path = source_path.replace("file:", "")
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Data missing at: {clean_path}")

        # Read with Pandas (Bridge)
        pdf = pd.read_csv(clean_path, dtype=str)
        df = spark.createDataFrame(pdf)
        df_enriched = df.withColumn("ingestion_timestamp", current_timestamp())

        # 2. WRITE (Corrected Path for Permissions)
        # 🛑 OLD: /local_disk0/ecommerce_lakehouse (Permission Denied)
        # ✅ NEW: /local_disk0/tmp/ecommerce_lakehouse (Writable)
        LAKEHOUSE_ROOT = Path("/local_disk0/tmp/ecommerce_lakehouse")
        
        output_dir = LAKEHOUSE_ROOT / f"{table_name}_bronze"
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        save_path = f"file:{output_dir.as_posix()}"
        
        (df_enriched.write
         .format("delta")
         .mode("overwrite")
         .option("mergeSchema", "true")
         .save(save_path)
        )
        
        print(f"✅ Success: {table_name} -> {save_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise e