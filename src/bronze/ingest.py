
from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd
from pathlib import Path

def ingest_to_bronze(spark, source_path, table_name):
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # --- 1. READ (Source is Dynamic) ---
        # The source_path comes from main_pipeline.py and is already absolute.
        # We strip 'file:' just in case, as Pandas expects a clean path.
        clean_path = source_path.replace("file:", "")
        
        # Verify file exists before trying to read (Good Engineering Practice)
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Could not find data file at: {clean_path}")

        # Read with Pandas (Bridge for CE restrictions)
        pdf = pd.read_csv(clean_path, dtype=str)
        df = spark.createDataFrame(pdf)
        
        df_enriched = df.withColumn("ingestion_timestamp", current_timestamp())

        # --- 2. WRITE (Destination is Fixed by Platform) ---
        # We use /local_disk0 because it's the specific writable area on Databricks CE.
        # This isn't "hardcoding" user data; it's configuring the infrastructure.
        LAKEHOUSE_ROOT = Path("/local_disk0/ecommerce_lakehouse")
        
        # Create the directory structure if missing
        output_dir = LAKEHOUSE_ROOT / f"{table_name}_bronze"
        if not output_dir.exists():
            # parents=True creates any missing parent folders (like 'ecommerce_lakehouse')
            output_dir.mkdir(parents=True, exist_ok=True)
            
        # Save as Delta
        save_path = f"file:{output_dir.as_posix()}"
        
        (df_enriched.write
         .format("delta")
         .mode("overwrite")
         .option("mergeSchema", "true")
         .save(save_path)
        )
        
        print(f"✅ Success: {table_name} -> {save_path}")
        
    except Exception as e:
        print(f"❌ Error ingesting {table_name}: {str(e)}")
        # Raise the error so the pipeline knows it failed
        raise e