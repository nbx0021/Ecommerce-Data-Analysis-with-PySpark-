from pyspark.sql.functions import current_timestamp, input_file_name, lit
import os
import pandas as pd

def ingest_to_bronze(spark, source_path, table_name):
    """
    Reads CSV and saves as Delta to the /FileStore (Writable) location.
    """
    try:
        print(f"⏳ Ingesting {table_name}...")
        
        # --- 1. READ (Pandas Bridge for CE) ---
        if "DATABRICKS_RUNTIME_VERSION" in os.environ and "/Workspace/" in source_path:
            print(f"   ⚠️ Community Edition detected. Reading via Pandas...")
            
            clean_path = source_path.replace("file:", "")
            # Read with Pandas
            pdf = pd.read_csv(clean_path)
            # Convert to Spark
            df = spark.createDataFrame(pdf)
            
            # Add metadata manually
            df_enriched = (df
                           .withColumn("ingestion_timestamp", current_timestamp())
                           .withColumn("source_file", lit(clean_path))
            )
            
        else:
            # Standard Read (Local/Prod)
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

        # --- 2. WRITE (The Fix) ---
        # 🛑 OLD PATH (Blocked): dbfs:/user/hive/warehouse/...
        # ✅ NEW PATH (Allowed): dbfs:/FileStore/tables/...
        
        if "DATABRICKS_RUNTIME_VERSION" in os.environ:
            # We create a specific folder for your project in FileStore
            save_path = f"dbfs:/FileStore/tables/ecommerce_lakehouse/{table_name}_bronze"
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