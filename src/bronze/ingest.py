from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd
from pathlib import Path

def ingest_to_bronze(spark, source_path, table_name):
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # 1. READ (Dynamic Source)
        clean_path = source_path.replace("file:", "")
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Data missing at: {clean_path}")

        # Read with Pandas
        pdf = pd.read_csv(clean_path, dtype=str)
        
        # Add Timestamp (in Pandas to avoid converting back and forth)
        pdf['ingestion_timestamp'] = pd.Timestamp.now()
        pdf['source_file'] = clean_path

        # 2. WRITE (Using Python to Bypass Spark Security Lock)
        # We use /local_disk0/tmp because Python allows writing there.
        # We switch to PARQUET because it's a robust binary format (Delta is based on it).
        
        LAKEHOUSE_ROOT = Path("/local_disk0/tmp/ecommerce_lakehouse")
        output_dir = LAKEHOUSE_ROOT / f"{table_name}_bronze"
        
        # Create directory (Python is allowed to do this)
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        # Save as Parquet using Pandas/PyArrow
        save_path = output_dir / "data.parquet"
        pdf.to_parquet(save_path, index=False)
        
        # 3. REGISTER (So Spark knows about it)
        # We read it back immediately to register a Temp View for the next steps
        df_spark = spark.read.parquet(f"file:{save_path}")
        df_spark.createOrReplaceGlobalTempView(f"{table_name}_bronze")
        
        print(f"✅ Success: {table_name} -> {save_path} (Registered as Global View)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise e