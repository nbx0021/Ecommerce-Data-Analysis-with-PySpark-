# tests/test_bronze.py
"""
Unit tests for Bronze Layer ingestion logic.
Tests schema enforcement, audit columns, and error handling.
"""
import os
import pytest
import tempfile
import csv


class TestBronzeIngestion:
    """Tests for ingest_to_bronze()."""

    def test_ingest_creates_temp_view(self, spark, tmp_path):
        """Verify that ingestion creates a named temp view."""
        # Create a mock CSV
        csv_path = str(tmp_path / "test_orders.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "customer_id", "order_status"])
            writer.writerow(["o1", "c1", "delivered"])

        from src.bronze.ingest import ingest_to_bronze
        ingest_to_bronze(spark, csv_path, "test_orders")

        # Verify view exists
        views = [row.viewName for row in spark.sql("SHOW VIEWS").collect()]
        assert "test_orders_bronze" in views

    def test_audit_columns_added(self, spark, tmp_path):
        """Verify ingestion_timestamp and source_file audit columns are added."""
        csv_path = str(tmp_path / "test_audit.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seller_id", "seller_city"])
            writer.writerow(["s1", "sao paulo"])

        from src.bronze.ingest import ingest_to_bronze
        ingest_to_bronze(spark, csv_path, "test_audit")

        df = spark.table("test_audit_bronze")
        columns = df.columns
        assert "ingestion_timestamp" in columns
        assert "source_file" in columns

    def test_row_count_returned(self, spark, tmp_path):
        """Verify the function returns the correct row count."""
        csv_path = str(tmp_path / "test_count.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id"])
            writer.writerow(["p1"])
            writer.writerow(["p2"])
            writer.writerow(["p3"])

        from src.bronze.ingest import ingest_to_bronze
        row_count = ingest_to_bronze(spark, csv_path, "test_count")
        assert row_count == 3

    def test_file_not_found_raises_error(self, spark):
        """Verify FileNotFoundError for missing CSV."""
        from src.bronze.ingest import ingest_to_bronze
        with pytest.raises(FileNotFoundError):
            ingest_to_bronze(spark, "/nonexistent/path.csv", "missing")
