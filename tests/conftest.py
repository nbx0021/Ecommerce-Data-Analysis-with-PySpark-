# tests/conftest.py
"""
Shared pytest fixtures for all test modules.
Provides a single SparkSession scoped to the test session.
"""
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Session-scoped SparkSession for all tests."""
    session = (SparkSession.builder
        .master("local[1]")
        .appName("PipelineTests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
