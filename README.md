# 🛒 E-Commerce Data Engineering & Analysis Pipeline

## 📌 Project Overview
This project is an end-to-end Data Engineering and Analytics pipeline built using **PySpark** on **Databricks Community Edition**. 

It analyzes the **Olist E-Commerce Public Dataset**, simulating a real-world scenario of ingesting, cleaning, and extracting business insights from a relational database of 100k+ orders. The workflow demonstrates a **Modern Data Stack** approach using a "Hybrid" Free-Tier architecture.

## 🚀 Architecture
- **Source:** Raw CSV data (Static)
- **Version Control:** GitHub (Code & Data Storage)
- **Orchestration:** GitHub Actions (Automated Ingestion - Simulated)
- **Processing:** Apache Spark (PySpark) on Databricks
- **Analysis:** SQL & Python

## 🛠️ Technologies Used
- **Languages:** Python 3.9, SQL
- **Libraries:** PySpark, Pandas, NumPy
- **Platform:** Databricks Community Edition
- **Tools:** GitHub Desktop, Git

## 📊 Key Features Implemented
1.  **Data Ingestion:**
    - Hybrid "Repo-based" ingestion to bypass DBFS limitations.
    - Automated file synchronization via Databricks Repos.
2.  **Data Cleaning:**
    - Schema enforcement using `StructType`.
    - Handling nulls in critical timestamps (Delivery & Approval dates).
    - Text normalization for Reviews and Categories.
3.  **Advanced Analytics:**
    - **Logistics KPIs:** Calculated Delivery Delays and Freight Performance.
    - **Sales Analytics:** Revenue by Product Category.
    - **RFM Segmentation:** Customer classification (Champions, At Risk, Hibernating).

## 📂 Project Structure
```
static-data-analysis/
│
├── data/                   # Raw CSV files (Olist Dataset)
│   ├── olist_orders_dataset.csv
│   ├── olist_customers_dataset.csv
│   └── ...
│
├── notebooks/              # Databricks Notebooks
│   └── Ecommerce-Data-Analysis-with-PySpark-.py    # Main Spark Job (Cleaning + Analysis)
│
└── README.md               # Project Documentation

```

## ⚙️ How to Run

1. **Clone the Repo:**
* In Databricks, go to **Repos** > **Add Repo**.
* Paste the URL of this repository.


2. **Run the Notebook:**
* Open `notebooks/Ecommerce-Data-Analysis-with-PySpark-`.
* Click **"Run All"**.
* *Note: The notebook uses `os.getcwd()` to dynamically locate the data files inside the Repo.*



## 📈 Future Improvements

* Implement **Market Basket Analysis** (FP-Growth) for cross-selling recommendations.
* Integrate **MLflow** to track model experiments.
* Visualize geospatial seller distribution using **Leaflet/Folium**.

```

---

### 2. Data Coverage Report (What we used vs. What is left)

You have successfully utilized about **70% of the dataset** relationships. Here is the breakdown:

| Table | Status | What we did with it |
| :--- | :--- | :--- |
| **`df_orders`** | ✅ **Heavy Use** | Used for delivery delays, cohort analysis, and RFM recency. |
| **`df_order_items`** | ✅ **Heavy Use** | Used for revenue calculation, top products, and RFM monetary value. |
| **`df_customers`** | ✅ **Heavy Use** | Used to map orders to states/regions. |
| **`df_products`** | ✅ **Moderate Use** | Joined to get category names. |
| **`df_reviews`** | ✅ **Moderate Use** | Cleaned null comments (Ready for Sentiment Analysis). |
| **`df_sellers`** | ❌ **Unused** | **Gap:** We haven't analyzed who the *best sellers* are yet. |
| **`df_payments`** | ❌ **Unused** | **Gap:** We haven't analyzed *how* people pay (Credit Card vs. Boleto). |
| **`df_geolocation`** | ⚠️ **Partial** | We discussed cleaning it, but haven't visualized the map yet. |

### 3. Next Step (To reach 100%)
To complete the portfolio, you should add one final analysis section for **Sellers & Payments**.

**Would you like a code snippet to analyze "Seller Performance" (e.g., Which sellers have the most late deliveries) to fill that gap?**
