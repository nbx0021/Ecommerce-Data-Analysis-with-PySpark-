# 🛒 E-Commerce Data Pipeline (In-Memory Lakehouse)

## 📌 Project Overview

This project transforms a static analysis notebook into a **production-grade Data Engineering Pipeline**. It processes the **Olist E-Commerce Public Dataset** (100k+ orders) using a modular **Medallion Architecture (Bronze → Silver → Gold)**.

**Key Highlight:** Designed specifically for **Databricks Community Edition**, this pipeline implements a custom **"In-Memory Lakehouse"** architecture. It overcomes the platform's "No-Write" storage limitations by utilizing Spark Temporary Views for data persistence across the ETL lifecycle, simulating a real-world Lakehouse without physical storage costs.

## 🔄 What Makes This Industry-Grade

| Feature | Description |
| --- | --- |
| **Architecture** | Modular `src/` package with Medallion layers |
| **Schema Enforcement** | Explicit `StructType` schemas at Bronze ingestion |
| **Data Quality** | Automated null-rate checks, row-count validation, quality reports |
| **Testing** | 16 unit tests across Bronze/Silver/Gold with `pytest` |
| **Structured Logging** | Python `logging` module with timestamp + level + layer format |
| **Performance** | DataFrame caching, AQE, optimized shuffle partitions |
| **7 Gold KPIs** | Logistics, Sales, Products, RFM, Payments, Sellers, Reviews |

## 🏗️ Architecture & Data Flow

### The "Community Edition" Challenge

Databricks Community Edition (Free Tier) has strictly disabled writing to DBFS (`/FileStore`) and Local Disk (`/local_disk0`).

* **Problem:** Standard ETL jobs fail because they cannot save Parquet/Delta files.
* **Solution:** An **In-Memory Pipeline** where data moves through Bronze, Silver, and Gold layers as **Spark Temporary Views** within the active session.

### Medallion Layers

* **🥉 Bronze Layer (Ingestion):**
  * Pandas bridge ingestion (required — `spark.read.csv()` errors on CE)
  * Explicit schema enforcement via `StructType` registry
  * Audit columns: `ingestion_timestamp`, `source_file`
  * Row-count logging for observability

* **🥈 Silver Layer (Cleaning & Transformation):**
  * **7 cleaned tables**: orders, order_items, products, customers, payments, sellers, reviews
  * Timestamp casting, NULL handling with business logic
  * Customer deduplication by `customer_unique_id`
  * Payment type validation against known values
  * Category enrichment with English translations
  * Data quality gates (null rate + row count checks)

* **🥇 Gold Layer (Business Aggregations):**
  * **Logistics:** Avg delivery time, delay vs estimate, on-time delivery %
  * **Sales:** Monthly revenue trends with average order value
  * **Products:** Revenue by category with freight costs
  * **RFM Segmentation:** Champion / Big Spender / New / Loyal / Lost customers
  * **Payments:** Payment method distribution, avg installments
  * **Sellers:** Top sellers by revenue and order count
  * **Reviews:** Avg review score by category, positive review %

## 📂 Project Structure

```
Ecommerce-Data-Analysis-with-PySpark/
│
├── data/                      # Raw CSV datasets (Olist, ~125MB)
├── src/                       # Source Code
│   ├── config.py              # Centralized configuration
│   ├── bronze/
│   │   ├── ingest.py          # Pandas bridge ingestion + schema enforcement
│   │   └── schemas.py         # StructType schemas for all 9 datasets
│   ├── silver/
│   │   └── clean.py           # Cleaning for all 7 tables + data quality
│   ├── gold/
│   │   └── aggregate.py       # 7 business KPI aggregations
│   └── utils/
│       ├── spark_utils.py     # SparkSession factory (CE-optimized)
│       ├── logger.py          # Structured logging
│       └── data_quality.py    # Null checks, row count validation
│
├── tests/                     # Unit Tests (16 tests)
│   ├── conftest.py            # Shared SparkSession fixture
│   ├── test_bronze.py         # Ingestion tests
│   ├── test_silver.py         # Cleaning & quality tests
│   └── test_gold.py           # Aggregation tests
│
├── main_pipeline.py           # Orchestrator with timing & error handling
├── trigger_pipeline.ipynb     # Notebook for Databricks scheduling
├── dashboard_visuals.ipynb    # Interactive executive dashboard
└── README.md
```

## 🛠️ How to Run

### On Databricks CE
1. **Clone the Repo** into Databricks Repos
2. Open **`trigger_pipeline`** notebook
3. Click **Run All**
4. **View Dashboard:** Switch to "Dashboard" view in `dashboard_visuals.ipynb`

### Locally
```bash
pip install pyspark pandas pytest
python main_pipeline.py
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific layer
python -m pytest tests/test_silver.py -v
```

## ⚙️ Performance Tuning

| Setting | Value | Reason |
| --- | --- | --- |
| `spark.sql.shuffle.partitions` | 8 | Default 200 is overkill for ~100k rows |
| `spark.sql.adaptive.enabled` | true | AQE for dynamic partition optimization |
| DataFrame caching | orders, items | Shared across multiple Gold aggregations |

## 🛑 Limitations of Databricks Community Edition

1. **Persistent Storage:** Cannot save `.parquet` or `.delta` files. All data is lost when the cluster terminates.
2. **Continuous Automation:** Community Cluster auto-terminates after 2 hours of inactivity.
3. **CI/CD Integration:** Cannot connect GitHub Actions runners to the Community Workspace.

## 📊 Key Insights Generated

* **Logistics:** Average delivery ~12.5 days, with on-time delivery rate tracked
* **Sales:** Top revenue categories are `health_beauty` and `watches_gifts`
* **Segmentation:** Identified high-value "Champion" customers for VIP retention
* **Payments:** Credit card dominates, with avg 3-4 installments
* **Reviews:** Category-level sentiment tracking with positive review %
