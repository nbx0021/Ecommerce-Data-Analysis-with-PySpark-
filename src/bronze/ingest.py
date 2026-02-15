from pyspark.sql.functions import current_timestamp, lit
import os
import pandas as pd

def ingest_to_bronze(spark, source_path, table_name):
    """
    Reads CSV and saves as Delta to Local Temporary Storage.
    Explicitly creates the directory structure if it doesn't exist.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # --- 1. READ (Pandas Bridge for CE) ---
        if "DATABRICKS_RUNTIME_VERSION" in os.environ and "/Workspace/" in source_path:
            print(f"   ⚠️ Community Edition detected. Reading via Pandas...")
            clean_path = source_path.replace("file:", "")
            pdf = pd.read_csv(clean_path)
            df = spark.createDataFrame(pdf)
            
            df_enriched = (df
                           .withColumn("ingestion_timestamp", current_timestamp())
                           .withColumn("source_file", lit(clean_path))
            )
        else:
            # Standard Read for Local or Pro Databricks
            df = (spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(source_path))
            df_enriched = df.withColumn("ingestion_timestamp", current_timestamp())

        # --- 2. THE FIX: CREATE DIRECTORY & WRITE ---
        if "DATABRICKS_RUNTIME_VERSION" in os.environ:
            # Define the local path on the driver node
            local_dir = "/tmp/ecommerce_lakehouse"
            save_path = f"file:{local_dir}/{table_name}_bronze"
            
            # 🚀 NEW: Create the folder if it doesn't exist
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
                print(f"   📂 Created directory: {local_dir}")
        else:
            save_path = f"spark-warehouse/{table_name}_bronze"

        # Write to Delta
        (df_enriched.write
         .format("delta")
         .mode("overwrite")
         .option("mergeSchema", "true")
         .save(save_path)
        )
        
        print(f"✅ Success: {table_name} -> {save_path}")
        
    except Exception as e:
        print(f"❌ Error ingesting {table_name}: {str(e)}")