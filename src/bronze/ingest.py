# src/bronze/ingest.py
from pyspark.sql.functions import current_timestamp, input_file_name
import os

def ingest_to_bronze(spark, source_path, table_name):
    """
    Reads any CSV and saves it as a raw Delta table.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # Read CSV with "Failfast" schema inference (good for Bronze)
        df = (spark.read
              .format("csv")
              .option("header", "true")
              .option("inferSchema", "true") # Let Spark guess types for now
              .load(source_path)
        )
        
        # Add Audit Columns (Best Practice)
        df_enriched = (df
                       .withColumn("ingestion_timestamp", current_timestamp())
                       .withColumn("source_file", input_file_name())
        )

        # Define Storage Path (DBFS on Cloud, Local Folder on PC)
        if "DATABRICKS_RUNTIME_VERSION" in os.environ:
            save_path = f"dbfs:/user/hive/warehouse/{table_name}_bronze"
        else:
            save_path = f"spark-warehouse/{table_name}_bronze"

        # Write to Delta
        (df_enriched.write
         .format("delta")
         .mode("overwrite")     # Overwrite for full refresh (or 'append' for incremental)
         .option("mergeSchema", "true") # Auto-evolve if CSV changes
         .save(save_path)
        )
        
        print(f"✅ Success: {table_name} -> {save_path}")
        
    except Exception as e:
        print(f"❌ Error ingesting {table_name}: {str(e)}")