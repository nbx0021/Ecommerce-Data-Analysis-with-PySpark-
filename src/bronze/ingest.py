# src/bronze/ingest.py
from pyspark.sql.functions import current_timestamp, input_file_name, lit
import os
import pandas as pd

def ingest_to_bronze(spark, source_path, table_name):
    """
    Reads CSV and saves as Delta.
    Includes a 'Pandas Bridge' for Databricks Community Edition restrictions.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # 🛡️ THE PANDAS BRIDGE 🛡️
        if "DATABRICKS_RUNTIME_VERSION" in os.environ and "/Workspace/" in source_path:
            print(f"   ⚠️ Community Edition detected. Using Pandas Bridge for {table_name}...")
            
            # 1. Read using Pandas (Allowed)
            clean_path = source_path.replace("file:", "")
            pdf = pd.read_csv(clean_path)
            
            # 2. Convert to Spark (The Handover)
            # 🛑 REMOVED: The Arrow config line caused the security error.
            # We will use the standard conversion instead (it works fine for this data size).
            df = spark.createDataFrame(pdf)
            
            # 3. Add Audit Columns
            df_enriched = (df
                           .withColumn("ingestion_timestamp", current_timestamp())
                           .withColumn("source_file", lit(clean_path))
            )
            
        else:
            # Standard Spark Read (Local or Professional Databricks)
            df = (spark.read
                  .format("csv")
                  .option("header", "true")
                  .option("inferSchema", "true")
                  .load(source_path)
            )
            
            df_enriched = (df
                           .withColumn("ingestion_timestamp", current_timestamp())
                           .withColumn("source_file", input_file_name())
            )

        # Define Storage Path
        if "DATABRICKS_RUNTIME_VERSION" in os.environ:
            save_path = f"dbfs:/user/hive/warehouse/{table_name}_bronze"
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
        print(f"   Attempted Path: {source_path}")