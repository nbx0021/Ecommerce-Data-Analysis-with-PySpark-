# 🛒 E-Commerce Data Pipeline (In-Memory Lakehouse)

## 📌 Project Overview

This project transforms a static analysis notebook into a production-grade **Data Engineering Pipeline**. It processes the **Olist E-Commerce Public Dataset** (100k+ orders) using a modular **Medallion Architecture (Bronze  Silver  Gold)**.

**Key Highlight:** Designed specifically for **Databricks Community Edition**, this pipeline implements a custom **"In-Memory Lakehouse"** architecture. It overcomes the platform's strict "No-Write" storage limitations by utilizing Spark Temporary Views for data persistence across the ETL lifecycle, simulating a real-world Lakehouse without physical storage costs.

## 🔄 Project Evolution: What We Upgraded

We transitioned from a monolithic notebook to a modular software project.

| Feature | ❌ Previous Version | ✅ Current Version (Upgraded) |
| --- | --- | --- |
| **Architecture** | Monolithic (`.ipynb` file) | **Modular** (`src/` package structure) |
| **Data Flow** | Raw CSV  Charts | **Medallion** (Bronze/Silver/Gold Layers) |
| **Storage** | Pandas DataFrames | **Spark In-Memory Lakehouse** (Global/Temp Views) |
| **Data Quality** | Manual Checks | **Unit Tests** (`pytest`) & Schema Enforcement |
| **Automation** | Manual "Run All" | **Scheduled Job** (Daily at 12:51 PM) |
| **Visualization** | Static Tables | **Interactive Executive Dashboard** |

## 🏗️ Architecture & Data Flow

### 1. The "Community Edition" Challenge

Databricks Community Edition (Free Tier) has strictly disabled writing to DBFS (`/FileStore`) and Local Disk (`/local_disk0`).

* **Problem:** Standard ETL jobs fail because they cannot save Parquet/Delta files.
* **Solution:** I engineered an **In-Memory Pipeline**. The data moves through Bronze, Silver, and Gold layers as **Spark Temporary Views** within the active session. This allows full SQL transformation capabilities without triggering file system permission errors.

### 2. Medallion Layers

* **🥉 Bronze Layer (Ingestion):**
* Dynamic path detection using `pathlib`.
* Ingests raw CSVs via a Pandas bridge (to bypass Spark read locks).
* Registers raw data as `orders_bronze`, `customers_bronze`, etc.


* **🥈 Silver Layer (Cleaning & Transformation):**
* **Casting:** Converts string inputs to proper `Timestamp` and `Double` types.
* **Data Quality:** Handles NULLs in `order_approved_at` using business logic (coalesce with purchase date).
* **Enrichment:** Joins Product IDs with English Category translations.


* **🥇 Gold Layer (Business Aggregations):**
* **Logistics:** Calculates Average Delivery Time & Delay vs. Estimates.
* **Sales:** Monthly Revenue Trends.
* **Marketing:** **RFM Segmentation** (Recency, Frequency, Monetary) to identify "Champion" vs. "Lost" customers.



## 📂 Project Structure

```bash
Ecommerce-Data-Analysis-with-PySpark/
│
├── data/                  # Raw CSV datasets (Olist)
├── src/                   # Source Code
│   ├── bronze/            # Ingestion logic
│   │   └── ingest.py
│   ├── silver/            # Cleaning & Quality logic
│   │   └── clean.py
│   ├── gold/              # Aggregation & Business logic
│   │   └── aggregate.py
│   └── utils/             # Spark session helpers
│
├── tests/                 # Unit Tests
│   └── test_silver.py     # Tests for NULL handling logic
│
├── main_pipeline.py       # Orchestrator (Entry Point)
├── trigger_pipeline.ipynb # Notebook for Scheduling
└── README.md              # Documentation

```

## 🤖 Automation & Scheduling

This pipeline is automated using the native **Databricks Job Scheduler**.

* **Schedule:** Runs every day at **12:51 PM**.
* **Trigger:** The `trigger_pipeline` notebook invokes `main_pipeline.py`.
* **Action:**
1. Spins up the compute cluster.
2. Executes the full ETL flow (Ingest  Clean  Aggregate).
3. Refreshes the Dashboard visuals.



## 🛑 Limitations of Databricks Community Edition

This project pushes the boundaries of the Free Tier. Here is what is **NOT** possible due to platform restrictions:

1. **Persistent Storage:** We cannot save `.parquet` or `.delta` files. All data is lost when the cluster terminates.
2. **Continuous Automation:** While we have a "Schedule," the Community Cluster auto-terminates after 2 hours of inactivity. If the cluster is off at 12:51 PM, the job will fail to start (unlike Paid Databricks, which spins up new clusters automatically).
3. **CI/CD Integration:** We cannot connect GitHub Actions runners directly to the Community Workspace to trigger tests on push.

## 🛠️ How to Run

1. **Clone the Repo** into Databricks Repos.
2. Open **`trigger_pipeline`** notebook.
3. Click **Run All**.
4. **View Dashboard:** Switch the view from "Standard" to "Dashboard" to see the visualizations for:
* Logistics Performance (Counter)
* Revenue Trends (Line Chart)
* Customer Segments (Pie Chart)



## 🧪 Testing

Unit tests are implemented using `pytest` to ensure data quality logic is sound.
To run tests:

```python
import pytest
# Run specific test for Silver Layer logic
import tests.test_silver
tests.test_silver.test_clean_orders_fills_nulls(spark)

```

## 📊 Key Insights Generated

* **Logistics:** Average delivery time is ~12.5 days, with avg_delay_vs_estimate -11.88.
* **Sales:** Top revenue categories are `health_beauty` and `watches_gifts`.
* **Segmentation:** Identified ~500 high-value "Champion" customers requiring VIP retention strategies.

  
  #### Customer Segments (RFM Analysis):
  
| customer_segment | customer_count | vg_spend |
| --- | --- | --- |
| **Big Spender** |3777  | 930.58  |
| **Loyal - At Risk** |2620 | 191.4  |
| **Lost / Hibernating** |89023  | 107.56  |
