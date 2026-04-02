# src/config.py
"""
Centralized configuration for the E-Commerce pipeline.
All dataset paths, table names, and quality thresholds in one place.
"""
from pathlib import Path
import os

# ─── Project Root Detection ────────────────────────────────
def get_project_root() -> Path:
    """Detect project root — works in both Databricks Repos and local."""
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return Path(os.getcwd())

PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data"

# ─── Dataset Registry ──────────────────────────────────────
DATASETS = {
    "customers":            (DATA_DIR / "olist_customers_dataset.csv").as_posix(),
    "orders":               (DATA_DIR / "olist_orders_dataset.csv").as_posix(),
    "order_items":          (DATA_DIR / "olist_order_items_dataset.csv").as_posix(),
    "order_payments":       (DATA_DIR / "olist_order_payments_dataset.csv").as_posix(),
    "order_reviews":        (DATA_DIR / "olist_order_reviews_dataset.csv").as_posix(),
    "products":             (DATA_DIR / "olist_products_dataset.csv").as_posix(),
    "sellers":              (DATA_DIR / "olist_sellers_dataset.csv").as_posix(),
    "geolocation":          (DATA_DIR / "olist_geolocation_dataset.csv").as_posix(),
    "category_translation": (DATA_DIR / "product_category_name_translation.csv").as_posix(),
}

# ─── Data Quality Thresholds ────────────────────────────────
DQ_NULL_THRESHOLD = 0.05        # Warn if null rate exceeds 5%
DQ_MIN_ROWS = 1                 # Minimum rows per view

# ─── Spark Tuning for Databricks CE ─────────────────────────
SPARK_SHUFFLE_PARTITIONS = 8    # Default 200 is overkill for ~100k rows
SPARK_AQE_ENABLED = True        # Adaptive Query Execution

# ─── Layer View Naming Convention ────────────────────────────
def bronze_view(name: str) -> str:
    return f"{name}_bronze"

def silver_view(name: str) -> str:
    return f"{name}_silver"

def gold_view(name: str) -> str:
    return f"gold_{name}"
