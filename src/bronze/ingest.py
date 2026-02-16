from pyspark.sql.functions import current_timestamp
import os
import shutil
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
        
        # Add Metadata Columns in Pandas
        pdf['ingestion_timestamp'] = pd.Timestamp.now()
        pdf['source_file'] = clean_path

        # 2. WRITE (System /tmp - The Nuclear Option)
        # We use standard /tmp which is world-writable on Linux.
        # We write PARQUET because it is robust and Spark loves it.
        
        # Define a clean path in /tmp
        LAKEHOUSE_ROOT = Path("/tmp/ecommerce_lakehouse")
        output_dir = LAKEHOUSE_ROOT / f"{table_name}_bronze"
        
        # Force cleanup if it exists (to avoid permission conflicts from previous runs)
        if output_dir.exists():
            try:
                shutil.rmtree(output_dir)
            except OSError:
                pass # Ignore if we can't delete, we'll try to write anyway
        
        # Create directory
        output_dir.mkdir(parents=True, exist_ok=True)
            
        # Save as Parquet using Pandas
        save_path = output_dir / "data.parquet"
        pdf.to_parquet(save_path, index=False)
        
        # 3. REGISTER (Connect Spark to the Data)
        # Spark is allowed to READ from /tmp, just not WRITE to it.
        # We read the Parquet file we just made and register it as a view.
        
        df_spark = spark.read.parquet(f"file:{save_path}")
        df_spark.createOrReplaceGlobalTempView(f"{table_name}_bronze")
        
        print(f"✅ Success: {table_name} -> {save_path} (View: global_temp.{table_name}_bronze)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Print permissions to debug if it fails again
        try:
            print(f"   Permissions for /tmp: {oct(os.stat('/tmp').st_mode)[-3:]}")
        except:
            pass
        raise e