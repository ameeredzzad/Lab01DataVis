import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Lab 3 - High Dimensional Visualization",
    layout="wide"
)

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_data():
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "archive" / "Sample - Superstore.csv"
    df = pd.read_csv(csv_path, encoding="latin1")

    # Convert date columns
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    return df

df = load_data()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Lab 3")
st.sidebar.subheader("High-Dimensional Visualization")

section = st.sidebar.selectbox(
    "Choose Visualization",
    [
        "2.1 Mosaic Plot",
        "2.2 Trellis Display",
        "2.3 Heatmap",
        "2.4 Multivariate Scatter Plot",
        "2.5 Parallel Coordinate Plot",
        "2.6 Grand Tour (3D Scatter)",
        "3. Additional Visualization"
    ]
)

# =====================================================
# DATA PREVIEW
# =====================================================

with st.expander("Dataset Preview"):
    st.write(df.head())
    st.write("Rows:", len(df))
    st.write("Columns:", len(df.columns))

# =====================================================
# 2.1 MOSAIC PLOT
# =====================================================

if section == "2.1 Mosaic Plot":

    st.title("Mosaic Plot")
    st.subheader("Sales Distribution by Category and Segment")

    mosaic_data = (
        df.groupby(["Category", "Segment"])["Sales"]
        .sum()
        .reset_index()
    )

    fig = px.treemap(
        mosaic_data,
        path=["Category", "Segment"],
        values="Sales",
        color="Sales",
        color_continuous_scale="Tealgrn",
        title="Sales Contribution by Category and Segment"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Purpose:** Displays the proportional contribution of sales across product categories and customer segments.

    **Insight:** Larger rectangles indicate segments that contribute more sales revenue. Technology products often dominate sales volume.
    """)

# =====================================================
# 2.2 TRELLIS DISPLAY
# =====================================================

elif section == "2.2 Trellis Display":

    st.title("Trellis Display")
    st.subheader("Sales vs Profit by Product Category")

    chart = alt.Chart(df).mark_circle(
        size=80,
        opacity=0.7
    ).encode(
        x=alt.X("Sales:Q", title="Sales"),
        y=alt.Y("Profit:Q", title="Profit"),
        color=alt.Color(
            "Category:N",
            scale=alt.Scale(
                domain=["Furniture", "Office Supplies", "Technology"],
                range=["#E76F51", "#2A9D8F", "#5E60CE"]
            )
        ),
        tooltip=[
            "Category",
            "Sub-Category",
            "Sales",
            "Profit"
        ]
    ).properties(
        width=300,
        height=300
    ).facet(
        column="Category:N"
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("""
    **Purpose:** Trellis displays split data into multiple smaller charts for comparison.

    **Insight:** Technology generally shows higher profits, while Furniture exhibits larger variation and occasional losses.
    """)

# =====================================================
# 2.3 HEATMAP
# =====================================================

elif section == "2.3 Heatmap":

    st.title("Heatmap")
    st.subheader("Average Sales by Region and Category")

    heatmap_data = (
        df.groupby(["Region", "Category"])["Sales"]
        .mean()
        .reset_index()
    )

    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X("Region:N"),
        y=alt.Y("Category:N"),
        color=alt.Color(
            "Sales:Q",
            scale=alt.Scale(scheme="viridis")
        ),
        tooltip=[
            "Region",
            "Category",
            "Sales"
        ]
    ).properties(
        width=600,
        height=300
    )

    st.altair_chart(heatmap, use_container_width=True)

    st.markdown("""
    **Purpose:** Uses color intensity to represent average sales values.

    **Insight:** Darker cells indicate regions and categories with higher average sales.
    """)

# =====================================================
# 2.4 MULTIVARIATE SCATTER
# =====================================================

elif section == "2.4 Multivariate Scatter Plot":

    st.title("Multivariate Scatter Plot")

    scatter = px.scatter(
        df,
        x="Sales",
        y="Profit",
        color="Segment",
        color_discrete_sequence=px.colors.qualitative.Set2,
        size="Quantity",
        hover_data=[
            "Category",
            "Sub-Category",
            "Region"
        ],
        title="Sales vs Profit by Customer Segment"
    )

    st.plotly_chart(scatter, use_container_width=True)

    st.markdown("""
    **Purpose:** Displays multiple variables simultaneously.

    **Insight:** Higher sales generally produce higher profits, although some orders generate losses despite large sales.
    """)

# =====================================================
# 2.5 PARALLEL COORDINATES
# =====================================================

elif section == "2.5 Parallel Coordinate Plot":

    st.title("Parallel Coordinates Plot")

    sample_df = df.sample(
        min(500, len(df)),
        random_state=42
    )

    fig = px.parallel_coordinates(
        sample_df,
        dimensions=[
            "Sales",
            "Profit",
            "Quantity",
            "Discount"
        ],
        color="Sales",
        color_continuous_scale=px.colors.sequential.Sunset
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Purpose:** Displays relationships across several numerical variables simultaneously.

    **Insight:** Orders with higher sales often correspond to larger quantities, although discounts can significantly impact profitability.
    """)

# =====================================================
# 2.6 GRAND TOUR (3D SCATTER)
# =====================================================

elif section == "2.6 Grand Tour (3D Scatter)":

    st.title("Grand Tour (3D Scatter Plot)")

    fig = px.scatter_3d(
        df,
        x="Sales",
        y="Profit",
        z="Quantity",
        color="Category",
        color_discrete_sequence=["#F4A261", "#2A9D8F", "#457B9D"],
        opacity=0.7,
        hover_data=[
            "Sub-Category",
            "Region"
        ],
        title="3D Visualization of Sales, Profit and Quantity"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Purpose:** Explores multidimensional relationships in three-dimensional space.

    **Insight:** Technology products often form clusters with higher sales and profits, while several outliers become easier to identify.
    """)

# =====================================================
# 3 ADDITIONAL VISUALIZATION
# =====================================================

elif section == "3. Additional Visualization":

    st.title("Additional Visualization")
    st.subheader("Box Plot of Sales by Category")

    fig = px.box(
        df,
        x="Category",
        y="Sales",
        color="Category",
        color_discrete_sequence=["#E9C46A", "#06D6A0", "#118AB2"],
        title="Sales Distribution by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Purpose:** Box plots summarize distributions and identify outliers.

    **Insight:** Technology products tend to have higher median sales, while Furniture contains several extreme sales outliers.
    """)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("Ameer Edzzad Shah (22005680)- Data Visualization Lab 3")
