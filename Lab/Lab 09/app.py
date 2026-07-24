"""
Lab 09 - E-Commerce Dashboard Project
app.py — Interactive Dashboard (Tasks 4-8)

Reads the CLEANED csv produced by Lab9.py (Task 3).
Run with:  streamlit run app.py

Folder assumption (same as Lab9.py):
    Data Vis/
    ├── archive/
    │   └── online_retail_cleaned.csv
    └── Lab/
        └── Lab 09/
            ├── Lab9.py
            └── app.py   <-- this file
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(page_title="E-Commerce Performance Dashboard", layout="wide")

DATA_PATH = "../../archive/online_retail_cleaned.csv"


# ----------------------------------------------------------------------
# LOAD DATA (cached so it doesn't reload on every interaction)
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=["InvoiceDate"])
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


df_raw = load_data(DATA_PATH)

# ----------------------------------------------------------------------
# SESSION STATE (needed for cross-filtering and drill-down to persist
# across reruns — every Streamlit interaction reruns the whole script)
# ----------------------------------------------------------------------
if "highlight_country" not in st.session_state:
    st.session_state.highlight_country = None       # cross-filter (Executive Overview)
if "drill_country" not in st.session_state:
    st.session_state.drill_country = None            # drill-down level 1 (Detailed Investigation)
if "drill_customer" not in st.session_state:
    st.session_state.drill_customer = None            # drill-down level 2


def reset_all_filters():
    st.session_state.highlight_country = None
    st.session_state.drill_country = None
    st.session_state.drill_customer = None


# ----------------------------------------------------------------------
# SIDEBAR — GLOBAL FILTERS (Interactive Feature 1: category filtering,
# Feature 2: time-range filtering, Feature: multi-select filter)
# ----------------------------------------------------------------------
st.sidebar.title("Filters")

min_date, max_date = df_raw["InvoiceDate"].min().date(), df_raw["InvoiceDate"].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

all_countries = sorted(df_raw["Country"].unique())
selected_countries = st.sidebar.multiselect(
    "Country (leave empty = all)", options=all_countries, default=[]
)

price_tiers = sorted(df_raw["Price_Tier"].dropna().unique())
selected_tiers = st.sidebar.multiselect(
    "Price tier (leave empty = all)", options=price_tiers, default=[]
)

order_sizes = sorted(df_raw["Order_Size_Category"].unique())
selected_sizes = st.sidebar.multiselect(
    "Order size (leave empty = all)", options=order_sizes, default=[]
)

exclude_outliers = st.sidebar.checkbox("Exclude flagged outliers (Price/Quantity)", value=False)
exclude_returns = st.sidebar.checkbox("Exclude returns/cancellations", value=False)

product_search = st.sidebar.text_input("Search product (Description contains)", "")

if st.sidebar.button("Reset all filters"):
    reset_all_filters()
    st.rerun()

# ----------------------------------------------------------------------
# APPLY GLOBAL FILTERS
# ----------------------------------------------------------------------
df = df_raw.copy()

if len(date_range) == 2:
    start, end = date_range
    df = df[(df["InvoiceDate"].dt.date >= start) & (df["InvoiceDate"].dt.date <= end)]

if selected_countries:
    df = df[df["Country"].isin(selected_countries)]

if selected_tiers:
    df = df[df["Price_Tier"].isin(selected_tiers)]

if selected_sizes:
    df = df[df["Order_Size_Category"].isin(selected_sizes)]

if exclude_outliers:
    df = df[~df["Price_Outlier"] & ~df["Quantity_Outlier"]]

if exclude_returns:
    df = df[~df["IsReturn"]]

if product_search:
    df = df[df["Description"].str.contains(product_search, case=False, na=False)]

# Show active filter state clearly (assignment requirement)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Visible records:** {len(df):,} / {len(df_raw):,}")
active_filters = []
if selected_countries:
    active_filters.append(f"Country: {', '.join(selected_countries)}")
if selected_tiers:
    active_filters.append(f"Price tier: {', '.join(selected_tiers)}")
if selected_sizes:
    active_filters.append(f"Order size: {', '.join(selected_sizes)}")
if exclude_outliers:
    active_filters.append("Outliers excluded")
if exclude_returns:
    active_filters.append("Returns excluded")
if product_search:
    active_filters.append(f"Search: '{product_search}'")
st.sidebar.markdown("**Active filters:** " + ("; ".join(active_filters) if active_filters else "None"))


# ----------------------------------------------------------------------
# KPI CALCULATION HELPERS (Task 4)
# ----------------------------------------------------------------------
def compute_kpis(data, full_data):
    total_revenue = data["Revenue"].sum()
    avg_order_value = data.groupby("Invoice")["Revenue"].sum().mean()
    return_rate = data["IsReturn"].mean() * 100
    overall_avg_order_value = full_data.groupby("Invoice")["Revenue"].sum().mean()
    top_country = (
        data.groupby("Country")["Revenue"].sum().idxmax() if len(data) else "N/A"
    )
    top_country_share = (
        data.groupby("Country")["Revenue"].sum().max() / total_revenue * 100
        if total_revenue else 0
    )
    return {
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "overall_avg_order_value": overall_avg_order_value,
        "return_rate": return_rate,
        "top_country": top_country,
        "top_country_share": top_country_share,
    }


# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.title("E-Commerce Performance Dashboard")
st.caption(
    "Domain: E-Commerce (UK-based online gift retailer, UCI Online Retail II dataset) | "
    "Problem: Converting two years of raw transaction data into actionable insight on "
    "revenue drivers, market concentration, and transaction risk."
)
st.caption(f"Last data update: {df_raw['InvoiceDate'].max().strftime('%d %B %Y')}")

tab1, tab2, tab3 = st.tabs(
    ["📊 Executive Overview", "🔍 Exploratory Analysis", "🔎 Detailed Investigation"]
)

# ========================================================================
# VIEW 1: EXECUTIVE OVERVIEW
# ========================================================================
with tab1:
    st.subheader("Executive Overview")

    # Apply cross-filter highlight (Cross-Filtering Challenge) on top of
    # the global sidebar filters, scoped only to this view's charts/KPIs
    exec_df = df.copy()
    if st.session_state.highlight_country:
        exec_df = exec_df[exec_df["Country"] == st.session_state.highlight_country]
        st.info(
            f"Cross-filter active: showing data for **{st.session_state.highlight_country}** "
            f"only. Click the button below to clear it."
        )
        if st.button("Clear country cross-filter"):
            st.session_state.highlight_country = None
            st.rerun()

    kpi = compute_kpis(exec_df, df)

    # --- KPI CARDS (Task 4: at least 4, at least 2 with calculation/comparison) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"£{kpi['total_revenue']:,.0f}")
    c2.metric(
        "Avg Order Value",
        f"£{kpi['avg_order_value']:,.2f}",
        delta=f"{kpi['avg_order_value'] - kpi['overall_avg_order_value']:+.2f} vs overall avg",
    )
    c3.metric("Return / Cancellation Rate", f"{kpi['return_rate']:.1f}%")
    c4.metric(
        "Top Country Share",
        f"{kpi['top_country']}",
        delta=f"{kpi['top_country_share']:.1f}% of visible revenue",
    )

    st.markdown("---")

    col_a, col_b = st.columns(2)

    # --- TIME-BASED VISUALIZATION (Task 5, 7.2) ---
    with col_a:
        st.markdown("**Monthly Revenue Trend**")
        monthly = exec_df.groupby("YearMonth")["Revenue"].sum().reset_index()
        fig_trend = px.line(monthly, x="YearMonth", y="Revenue", markers=True)
        fig_trend.update_layout(xaxis_title="Month", yaxis_title="Revenue (£)")
        st.plotly_chart(fig_trend, use_container_width=True)

    # --- COMPARISON VISUALIZATION (Task 5, 7.1) with cross-filter click ---
    with col_b:
        st.markdown("**Top 10 Countries by Revenue** (click a bar to cross-filter)")
        top10 = (
            df.groupby("Country")["Revenue"].sum().sort_values(ascending=False).head(10).reset_index()
        )
        fig_bar = px.bar(top10, x="Revenue", y="Country", orientation="h")
        fig_bar.update_layout(yaxis=dict(autorange="reversed"))
        event = st.plotly_chart(
            fig_bar, use_container_width=True, on_select="rerun", key="country_bar"
        )
        if event and event.get("selection", {}).get("points"):
            clicked_country = event["selection"]["points"][0]["y"]
            if clicked_country != st.session_state.highlight_country:
                st.session_state.highlight_country = clicked_country
                st.rerun()

    # --- KEY FINDING / WARNING (dynamic, based on real thresholds) ---
    st.markdown("---")
    if kpi["return_rate"] > 5:
        st.warning(
            f"⚠️ Return/cancellation rate is {kpi['return_rate']:.1f}%, which is elevated. "
            f"Investigate in the Detailed Investigation tab."
        )
    elif kpi["top_country_share"] > 80:
        st.warning(
            f"⚠️ {kpi['top_country']} accounts for {kpi['top_country_share']:.1f}% of visible "
            f"revenue — high market concentration risk."
        )
    else:
        st.success("✅ No major risk threshold triggered for the current filter selection.")

    # --- DATA QUALITY SUMMARY PANEL (Task 3 requirement, shown here) ---
    with st.expander("Data Quality Summary"):
        dq1, dq2, dq3 = st.columns(3)
        dq1.metric("Missing Customer ID", f"{(~df_raw['Has_Customer_ID']).mean()*100:.1f}%")
        dq2.metric("Price Outliers Flagged", f"{df_raw['Price_Outlier'].mean()*100:.1f}%")
        dq3.metric("Quantity Outliers Flagged", f"{df_raw['Quantity_Outlier'].mean()*100:.1f}%")
        st.caption(
            f"Cleaned dataset: {len(df_raw):,} rows | {df_raw['Country'].nunique()} countries | "
            f"{df_raw['StockCode'].nunique():,} unique products | "
            f"date range {df_raw['InvoiceDate'].min().date()} to {df_raw['InvoiceDate'].max().date()}"
        )

# ========================================================================
# VIEW 2: EXPLORATORY ANALYSIS
# ========================================================================
with tab2:
    st.subheader("Exploratory Analysis")

    col_c, col_d = st.columns(2)

    # --- RELATIONSHIP VISUALIZATION (Task 5, 7.3) ---
    with col_c:
        st.markdown("**Price vs Quantity per Transaction** (colored by Price Tier, sized by Revenue)")
        sample = df.sample(min(5000, len(df)), random_state=1) if len(df) else df
        sample = sample.copy()
        sample["Revenue_Abs"] = sample["Revenue"].abs()  # size can't be negative; magnitude only
        fig_scatter = px.scatter(
            sample, x="Price", y="Quantity", color="Price_Tier", size="Revenue_Abs",
            hover_data=["Description", "Country"], opacity=0.6
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- DISTRIBUTION VISUALIZATION (Task 5, 7.4) ---
    with col_d:
        st.markdown("**Revenue Distribution by Order Size Category**")
        st.caption("Box plot chosen over histogram because it directly compares spread and "
                   "median across categories, and clearly exposes outliers per group.")
        fig_box = px.box(df, x="Order_Size_Category", y="Revenue", points="outliers")
        st.plotly_chart(fig_box, use_container_width=True)

    col_e, col_f = st.columns(2)

    # --- COMPOSITION VISUALIZATION (Task 5, 7.5) ---
    with col_e:
        st.markdown("**Revenue Composition: Country → Order Size**")
        treemap_data = df.groupby(["Country", "Order_Size_Category"])["Revenue"].sum().reset_index()
        treemap_data = treemap_data[treemap_data["Revenue"] > 0]
        fig_tree = px.treemap(
            treemap_data, path=["Country", "Order_Size_Category"], values="Revenue"
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    # --- ADVANCED VIZ 1: HEATMAP (Task 6) ---
    with col_f:
        st.markdown("**Advanced: Revenue Heatmap (Weekday × Hour)**")
        heat_data = df.groupby(["Weekday", "Hour"])["Revenue"].sum().reset_index()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat_pivot = heat_data.pivot(index="Weekday", columns="Hour", values="Revenue").reindex(weekday_order)
        fig_heat = px.imshow(heat_pivot, aspect="auto", color_continuous_scale="Blues")
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(
            "Why a heatmap: answers 'when do sales happen' across two dimensions (day AND hour) "
            "at once — a bar or line chart can only show one dimension clearly, and would need "
            "7 separate charts to show the same information."
        )

    # --- ADVANCED VIZ 2: SUNBURST (Task 6) ---
    st.markdown("**Advanced: Sunburst — Country → Price Tier → Order Size**")
    sun_data = (
        df.groupby(["Country", "Price_Tier", "Order_Size_Category"])["Revenue"]
        .sum().reset_index()
    )
    sun_data = sun_data[sun_data["Revenue"] > 0]
    top_countries_for_sunburst = df.groupby("Country")["Revenue"].sum().nlargest(8).index
    sun_data = sun_data[sun_data["Country"].isin(top_countries_for_sunburst)]
    fig_sun = px.sunburst(
        sun_data, path=["Country", "Price_Tier", "Order_Size_Category"], values="Revenue"
    )
    st.plotly_chart(fig_sun, use_container_width=True)
    st.caption(
        "Why a sunburst: shows a 3-level hierarchy (country → price tier → order size) in one "
        "view with proportional sizing, letting a user click into a country and instantly see "
        "its price/order-size mix — a stacked bar chart could not show 3 nested levels this cleanly."
    )

# ========================================================================
# VIEW 3: DETAILED INVESTIGATION (Task 8: Drill-Down)
# ========================================================================
with tab3:
    st.subheader("Detailed Investigation")

    # --- ADVANCED VIZ 3: GEOGRAPHIC MAP (Task 6) ---
    st.markdown("**Advanced: Revenue by Country (Map)**")
    geo_data = df.groupby("Country")["Revenue"].sum().reset_index()
    fig_map = px.choropleth(
        geo_data, locations="Country", locationmode="country names",
        color="Revenue", color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(
        "Why a map: geographic concentration is inherently spatial — a bar chart ranks countries "
        "but a map shows regional clustering (e.g. Western Europe) at a glance. Note: a few labels "
        "like 'Eire' and 'Channel Islands' won't render on the map due to naming mismatches with "
        "standard country names — a known limitation, documented in the report."
    )

    st.markdown("---")
    st.markdown("### Drill-Down: Country → Customer")

    if st.session_state.drill_country is None:
        # LEVEL 1: pick a country
        country_options = sorted(df["Country"].unique())
        chosen = st.selectbox("Select a country to drill into:", options=["-- Select --"] + country_options)
        if chosen != "-- Select --":
            st.session_state.drill_country = chosen
            st.rerun()
    else:
        st.markdown(f"**Level 1 → Country: {st.session_state.drill_country}**")
        if st.button("⬅ Back to country selection"):
            st.session_state.drill_country = None
            st.session_state.drill_customer = None
            st.rerun()

        country_df = df[df["Country"] == st.session_state.drill_country]

        if st.session_state.drill_customer is None:
            # LEVEL 2: pick a customer within that country
            cust_summary = (
                country_df.dropna(subset=["Customer_ID"])
                .groupby("Customer_ID")["Revenue"].sum()
                .sort_values(ascending=False).head(20).reset_index()
            )
            st.markdown("**Top 20 customers in this country by revenue:**")
            st.dataframe(cust_summary, use_container_width=True)

            cust_options = cust_summary["Customer_ID"].tolist()
            chosen_cust = st.selectbox(
                "Select a customer to drill into:", options=["-- Select --"] + cust_options
            )
            if chosen_cust != "-- Select --":
                st.session_state.drill_customer = chosen_cust
                st.rerun()
        else:
            # LEVEL 2 detail view
            st.markdown(f"**Level 2 → Customer ID: {st.session_state.drill_customer}**")
            if st.button("⬅ Back to customer list"):
                st.session_state.drill_customer = None
                st.rerun()

            cust_df = country_df[country_df["Customer_ID"] == st.session_state.drill_customer]
            country_avg_order = country_df.groupby("Invoice")["Revenue"].sum().mean()
            cust_avg_order = cust_df.groupby("Invoice")["Revenue"].sum().mean()

            m1, m2, m3 = st.columns(3)
            m1.metric("Customer Total Revenue", f"£{cust_df['Revenue'].sum():,.2f}")
            m2.metric(
                "Customer Avg Order Value",
                f"£{cust_avg_order:,.2f}",
                delta=f"{cust_avg_order - country_avg_order:+.2f} vs country avg",
            )
            m3.metric("Number of Orders", cust_df["Invoice"].nunique())

            st.markdown("**Order-level detail:**")
            st.dataframe(
                cust_df[["Invoice", "InvoiceDate", "Description", "Quantity", "Price", "Revenue", "IsReturn"]]
                .sort_values("InvoiceDate", ascending=False),
                use_container_width=True,
            )
