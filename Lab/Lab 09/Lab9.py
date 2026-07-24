"""
Lab 09 - E-Commerce Dashboard Project
Step 1-2: Load, Explore, and Clean the UCI Online Retail II dataset
Task 3: Data Preparation and Quality Assessment

Adjust the DATA_PATH below to match your folder structure.
This script assumes:
    Data Vis/
    ├── archive/
    │   └── online_retail_II.xlsx
    └── Lab 09/
        └── 01_explore_clean.py   <-- this file
"""

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# 1. LOAD DATA
# ----------------------------------------------------------------------
DATA_PATH = "../../archive/online_retail_II.xlsx"

print("Loading data... this can take a minute for ~1M rows.")
sheet_2009_2010 = pd.read_excel(DATA_PATH, sheet_name="Year 2009-2010")
sheet_2010_2011 = pd.read_excel(DATA_PATH, sheet_name="Year 2010-2011")

df = pd.concat([sheet_2009_2010, sheet_2010_2011], ignore_index=True)

print("\n--- RAW DATA OVERVIEW ---")
print("Shape:", df.shape)
print("\nColumn dtypes:\n", df.dtypes)
print("\nFirst rows:\n", df.head())

# Standardize column names (handles minor naming differences between sheets)
df.columns = [c.strip().replace(" ", "_") for c in df.columns]
print("\nStandardized columns:", list(df.columns))

# ----------------------------------------------------------------------
# 2. DATA QUALITY ASSESSMENT (Task 3)
# ----------------------------------------------------------------------
quality_report = {}

# --- 2a. Missing values ---
missing_counts = df.isnull().sum()
missing_pct = (missing_counts / len(df) * 100).round(2)
missing_summary = pd.DataFrame({"missing_count": missing_counts, "missing_pct": missing_pct})
missing_summary = missing_summary[missing_summary["missing_count"] > 0]
print("\n--- MISSING VALUES ---")
print(missing_summary)
quality_report["missing_values"] = missing_summary.to_dict()

# Customer_ID is commonly missing (~20-25%) in this dataset.
# Decision: keep rows with missing Customer_ID for revenue/product analysis,
# but flag them, since dropping them would remove a meaningful chunk of
# legitimate sales data (guest/unregistered checkouts).
df["Has_Customer_ID"] = df["Customer_ID"].notnull()

# Description missing in a small number of rows -> not usable for product-level
# analysis, so we drop only rows missing BOTH Description and StockCode context.
before_drop = len(df)
df = df.dropna(subset=["Description"])
after_drop = len(df)
print(f"\nDropped {before_drop - after_drop} rows with missing Description "
      f"(product name required for category-level analysis).")

# --- 2b. Duplicate records ---
dup_count = df.duplicated().sum()
print(f"\n--- DUPLICATES ---\nFound {dup_count} fully duplicated rows.")
df = df.drop_duplicates()
print(f"Removed duplicates. New shape: {df.shape}")
quality_report["duplicates_removed"] = int(dup_count)

# --- 2c. Inconsistent category names ---
# Country names sometimes have inconsistent casing/spacing or placeholder values.
df["Country"] = df["Country"].astype(str).str.strip().str.title()
# Known placeholder/non-country values in this dataset worth flagging (not deleting
# outright, since "Unspecified" may still represent a real sale):
unclear_countries = ["Unspecified", "European Community"]
print("\n--- COUNTRY VALUE CHECK ---")
print(df["Country"].value_counts().head(15))

# --- 2d. Data type conversions ---
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["Invoice"] = df["Invoice"].astype(str)
df["StockCode"] = df["StockCode"].astype(str)
df["Customer_ID"] = df["Customer_ID"].astype("Int64")  # nullable integer

# --- 2e. Extract date components ---
df["Year"] = df["InvoiceDate"].dt.year
df["Month"] = df["InvoiceDate"].dt.month
df["MonthName"] = df["InvoiceDate"].dt.strftime("%b")
df["Weekday"] = df["InvoiceDate"].dt.day_name()
df["Hour"] = df["InvoiceDate"].dt.hour
df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

# --- 2f. Identify returns / cancellations ---
# Invoice numbers starting with "C" indicate a cancellation (per dataset documentation)
df["IsReturn"] = df["Invoice"].str.startswith("C")

# --- 2g. Identify outliers (IQR method) on Price and Quantity ---
def iqr_outlier_bounds(series):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

price_low, price_high = iqr_outlier_bounds(df["Price"])
qty_low, qty_high = iqr_outlier_bounds(df["Quantity"])

df["Price_Outlier"] = ~df["Price"].between(price_low, price_high)
df["Quantity_Outlier"] = ~df["Quantity"].between(qty_low, qty_high)

print(f"\n--- OUTLIERS (IQR method) ---")
print(f"Price outlier bounds: [{price_low:.2f}, {price_high:.2f}] "
      f"-> {df['Price_Outlier'].sum()} rows flagged")
print(f"Quantity outlier bounds: [{qty_low:.2f}, {qty_high:.2f}] "
      f"-> {df['Quantity_Outlier'].sum()} rows flagged")

# Decision: outliers are FLAGGED, not removed. Bulk wholesale orders (very high
# Quantity) are legitimate business activity for this retailer (many customers
# are wholesalers per the dataset description), so removing them would distort
# revenue analysis. They are kept but visible in the dashboard as a filter.

# Remove clearly invalid rows: zero or negative price on non-return transactions,
# since a sale can't have a real price of 0 or less unless it's a cancellation/return.
before_invalid = len(df)
df = df[~((df["Price"] <= 0) & (~df["IsReturn"]))]
after_invalid = len(df)
print(f"\nRemoved {before_invalid - after_invalid} rows with Price <= 0 "
      f"on non-return transactions (data entry errors).")

# ----------------------------------------------------------------------
# 3. CALCULATED ATTRIBUTES (Task 3 requirement: at least 2)
# ----------------------------------------------------------------------

# 1. Revenue: core measure needed for almost every KPI and chart (total sales,
#    top products, top countries, trend over time).
df["Revenue"] = df["Quantity"] * df["Price"]

# 2. Order_Size_Category: buckets each line item by quantity, useful for
#    distinguishing retail vs wholesale-style purchases in comparison charts.
def order_size_bucket(qty):
    if qty <= 0:
        return "Return/Cancellation"
    elif qty <= 5:
        return "Small (1-5)"
    elif qty <= 20:
        return "Medium (6-20)"
    else:
        return "Large (20+)"

df["Order_Size_Category"] = df["Quantity"].apply(order_size_bucket)

# 3. (Bonus) Revenue_Per_Unit check — sanity attribute, and useful for
#    price-tier segmentation in the distribution/relationship charts.
df["Price_Tier"] = pd.cut(
    df["Price"],
    bins=[-0.01, 1, 5, 20, np.inf],
    labels=["Budget (<£1)", "Low (£1-5)", "Mid (£5-20)", "Premium (£20+)"]
)

print("\n--- CALCULATED ATTRIBUTES ADDED ---")
print("Revenue, Order_Size_Category, Price_Tier, Has_Customer_ID, IsReturn, "
      "Year/Month/Weekday/Hour, Price_Outlier, Quantity_Outlier")

# ----------------------------------------------------------------------
# 4. FINAL DATA QUALITY SUMMARY
# ----------------------------------------------------------------------
print("\n" + "=" * 50)
print("DATA QUALITY SUMMARY")
print("=" * 50)
print(f"Original rows (raw load):        {before_drop}")
print(f"Rows after cleaning:              {len(df)}")
print(f"Rows dropped (missing Description): {before_drop - after_drop}")
print(f"Duplicate rows removed:            {dup_count}")
print(f"Rows dropped (invalid price):       {before_invalid - after_invalid}")
print(f"Missing Customer_ID (kept, flagged): {(~df['Has_Customer_ID']).sum()} "
      f"({(~df['Has_Customer_ID']).mean()*100:.1f}%)")
print(f"Price outliers flagged (kept):      {df['Price_Outlier'].sum()}")
print(f"Quantity outliers flagged (kept):   {df['Quantity_Outlier'].sum()}")
print(f"Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
print(f"Countries represented: {df['Country'].nunique()}")
print(f"Unique products: {df['StockCode'].nunique()}")
print(f"Unique customers: {df['Customer_ID'].nunique()}")

# ----------------------------------------------------------------------
# 5. SAVE CLEANED DATA FOR STREAMLIT APP
# ----------------------------------------------------------------------
OUTPUT_PATH = "../../archive/online_retail_cleaned.csv"
df.to_csv(OUTPUT_PATH, index=False)
print(f"\nCleaned dataset saved to: {OUTPUT_PATH}")
print(f"Final shape: {df.shape}")
