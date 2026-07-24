import pandas as pd
import streamlit as st
import altair as alt

DATA_PATH = (
    r"C:\Users\User\Documents\Final 2nd\Data Vis\archive\Sample - Superstore.csv"
)

STATE_COORDS = {
    "Alabamas": (32.806671, -86.791130),
    "Alaska": (61.370716, -152.404419),
    "Arizona": (33.729759, -111.431221),
    "Arkansas": (34.969704, -92.373123),
    "California": (36.116203, -119.681564),
    "Colorado": (39.059811, -105.311104),
    "Connecticut": (41.597782, -72.755371),
    "Delaware": (39.318523, -75.507141),
    "District of Columbia": (38.897438, -77.026817),
    "Florida": (27.766279, -81.686783),
    "Georgia": (33.040619, -83.643074),
    "Hawaii": (21.094318, -157.498337),
    "Idaho": (44.240459, -114.478828),
    "Illinois": (40.349457, -88.986137),
    "Indiana": (39.849426, -86.258278),
    "Iowa": (42.011539, -93.210526),
    "Kansas": (38.526600, -96.726486),
    "Kentucky": (37.668140, -84.670067),
    "Louisiana": (31.169546, -91.867805),
    "Maine": (44.693947, -69.381927),
    "Maryland": (39.063946, -76.802101),
    "Massachusetts": (42.230171, -71.530106),
    "Michigan": (43.326618, -84.536095),
    "Minnesota": (45.694454, -93.900192),
    "Mississippi": (32.741646, -89.678696),
    "Missouri": (38.456085, -92.288368),
    "Montana": (46.921925, -110.454353),
    "Nebraska": (41.125370, -98.268082),
    "Nevada": (38.313515, -117.055374),
    "New Hampshire": (43.452492, -71.563896),
    "New Jersey": (40.298904, -74.521011),
    "New Mexico": (34.840515, -106.248482),
    "New York": (42.165726, -74.948051),
    "North Carolina": (35.630066, -79.806419),
    "North Dakota": (47.528912, -99.784012),
    "Ohio": (40.388783, -82.764915),
    "Oklahoma": (35.565342, -96.928917),
    "Oregon": (44.572021, -122.070938),
    "Pennsylvania": (40.590752, -77.209755),
    "Rhode Island": (41.680893, -71.511780),
    "South Carolina": (33.856892, -80.945007),
    "South Dakota": (44.299782, -99.438828),
    "Tennessee": (35.747845, -86.692345),
    "Texas": (31.054487, -97.563461),
    "Utah": (40.150032, -111.862434),
    "Vermont": (44.045876, -72.710686),
    "Virginia": (37.769337, -78.169968),
    "Washington": (47.400902, -121.490494),
    "West Virginia": (38.491226, -80.954453),
    "Wisconsin": (44.268543, -89.616508),
    "Wyoming": (42.755966, -107.302490)
}


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, encoding="latin1")
    data["Order Date"] = pd.to_datetime(data["Order Date"], errors="coerce")
    data["Ship Date"] = pd.to_datetime(data["Ship Date"], errors="coerce")
    data["Unit Price"] = data["Sales"] / data["Quantity"]
    coords = data["State"].map(STATE_COORDS)
    data["Latitude"] = coords.apply(lambda value: value[0] if isinstance(value, tuple) else None)
    data["Longitude"] = coords.apply(lambda value: value[1] if isinstance(value, tuple) else None)
    return data


st.set_page_config(page_title="Superstore Dashboard", layout="wide", page_icon="📊")


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def style_chart(chart: alt.Chart) -> alt.Chart:
    return chart.configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        grid=True,
        domain=False
    ).configure_legend(
        labelFontSize=12,
        titleFontSize=13
    )


data = load_data(DATA_PATH)

st.markdown("# Lab 1 — Superstore Sales Dashboard")
st.markdown("#### Ameer Edzzad Shah — 22005680")
st.markdown("---")

st.sidebar.title("Dashboard Controls")
st.sidebar.write("Choose a view and update the filters to reshape the analysis.")

view = st.sidebar.radio(
    "View",
    [
        "Basic Analysis",
        "Bar Chart + Scatter Plot",
        "Line Chart + Histogram",
        "Pie Chart + Bar Chart",
        "Map View + Scatter Plot"
    ]
)

sales_min = float(data["Sales"].min())
sales_max = float(data["Sales"].max())
category_options = sorted(data["Category"].dropna().unique())

with st.sidebar.expander("Filters", expanded=True):
    selected_category = st.selectbox("Product Category", ["All"] + category_options)
    sales_range = st.slider(
        "Sales range",
        min_value=sales_min,
        max_value=sales_max,
        value=(sales_min, sales_max),
        format="$%.2f"
    )

filtered = data.copy()
if selected_category != "All":
    filtered = filtered[filtered["Category"] == selected_category]
filtered = filtered[
    (filtered["Sales"] >= sales_range[0]) & (filtered["Sales"] <= sales_range[1])
]

if filtered.empty:
    st.warning("No data matches the current filters. Adjust the filters to continue.")
    st.stop()

st.write("")  # Spacing

if view == "Basic Analysis":
    _, center, _ = st.columns([0.05, 1.3, 0.05])

    bar_chart = alt.Chart(filtered).mark_bar(cornerRadius=3).encode(
        x=alt.X("Category:N", sort="-y", title="Category", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("sum(Sales):Q", title="Total Sales"),
        color=alt.Color("Category:N", legend=None, scale=alt.Scale(scheme="tableau10")),
        tooltip=["Category:N", alt.Tooltip("sum(Sales):Q", format=",.0f")]
    ).properties(height=400, width=350)

    pie_chart = alt.Chart(filtered).mark_arc(innerRadius=70, cornerRadius=3).encode(
        theta=alt.Theta("sum(Sales):Q", title="Sales"),
        color=alt.Color("Category:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["Category:N", alt.Tooltip("sum(Sales):Q", format=",.0f")]
    ).properties(height=400, width=350)

    center.markdown("")
    center.subheader("Sales Analysis")
    center.altair_chart(style_chart(bar_chart | pie_chart), use_container_width=True)
    center.markdown("")

elif view == "Bar Chart + Scatter Plot":
    _, center, _ = st.columns([0.05, 1.3, 0.05])
    center.markdown("")
    center.subheader("Sales by Category & Unit Price Analysis")
    center.caption("Click a category bar to filter the scatter plot")

    category_select = alt.selection_point(fields=["Category"], on="click", empty="all")

    bar_chart = alt.Chart(filtered).mark_bar(cornerRadius=3).encode(
        x=alt.X("Category:N", sort="-y", title="Category"),
        y=alt.Y("sum(Sales):Q", title="Total Sales"),
        color=alt.condition(category_select, "Category:N", alt.value("#e0e0e0")),
        tooltip=["Category:N", alt.Tooltip("sum(Sales):Q", format=",.0f")]
    ).add_params(category_select).properties(height=380, width=350)

    scatter_plot = alt.Chart(filtered).mark_circle(size=80, opacity=0.7).encode(
        x=alt.X("Unit Price:Q", title="Unit Price"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color("Category:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=["Category:N", alt.Tooltip("Unit Price:Q", format=",.2f"), "Quantity:Q"]
    ).transform_filter(category_select).properties(height=380, width=300)

    center.altair_chart(style_chart(bar_chart | scatter_plot), use_container_width=True)
    center.markdown("")

elif view == "Line Chart + Histogram":
    _, center, _ = st.columns([0.05, 1.3, 0.05])
    center.markdown("")
    center.subheader("Sales Trends & Distribution Analysis")
    center.caption("Brush the line chart to filter the histogram")

    time_brush = alt.selection_interval(encodings=["x"], empty="all")

    line_chart = alt.Chart(filtered).mark_line(point=True, size=2.5).encode(
        x=alt.X("Order Date:T", title="Order Date"),
        y=alt.Y("sum(Sales):Q", title="Total Sales"),
        color=alt.value("#1f77b4"),
        tooltip=[alt.Tooltip("Order Date:T", title="Date", format="%b %d, %Y"), alt.Tooltip("sum(Sales):Q", title="Sales", format=",.0f")]
    ).add_params(time_brush).properties(height=380, width=550)

    histogram = alt.Chart(filtered).mark_bar(cornerRadius=2).encode(
        x=alt.X("Quantity:Q", bin=alt.Bin(maxbins=20), title="Quantity"),
        y=alt.Y("count():Q", title="Frequency"),
        color=alt.value("#ff7f0e"),
        tooltip=[alt.Tooltip("count():Q", title="Count")]
    ).transform_filter(time_brush).properties(height=380, width=280)

    center.altair_chart(style_chart(line_chart | histogram), use_container_width=True)
    center.markdown("")

elif view == "Pie Chart + Bar Chart":
    _, center, _ = st.columns([0.05, 1.3, 0.05])
    center.markdown("")
    center.subheader("Category Performance & Regional Distribution")
    center.caption("Click a pie slice to filter by category")

    category_select = alt.selection_point(fields=["Category"], on="click", empty="all")

    pie_chart = alt.Chart(filtered).mark_arc(innerRadius=70, cornerRadius=3).encode(
        theta=alt.Theta("sum(Sales):Q", title="Sales"),
        color=alt.condition(category_select, "Category:N", alt.value("#d3d3d3")),
        tooltip=["Category:N", alt.Tooltip("sum(Sales):Q", format=",.0f")]
    ).add_params(category_select).properties(height=380, width=350)

    bar_chart = alt.Chart(filtered).mark_bar(cornerRadius=3).encode(
        x=alt.X("Region:N", sort="-y", title="Region"),
        y=alt.Y("sum(Sales):Q", title="Total Sales"),
        color=alt.Color("Region:N", scale=alt.Scale(scheme="set2")),
        tooltip=["Region:N", alt.Tooltip("sum(Sales):Q", format=",.0f")]
    ).transform_filter(category_select).properties(height=380, width=400)

    center.altair_chart(style_chart(pie_chart | bar_chart), use_container_width=True)
    center.markdown("")

elif view == "Map View + Scatter Plot":
    _, center, _ = st.columns([0.05, 1.3, 0.05])
    center.markdown("")
    center.subheader("Geographic Sales Analysis")
    center.caption("Click a state to filter by location")

    map_data = filtered.dropna(subset=["Latitude", "Longitude"])
    map_agg = map_data.groupby(["State", "Latitude", "Longitude"], as_index=False)["Sales"].sum()

    state_select = alt.selection_point(fields=["State"], on="click", empty="all")

    map_view = alt.Chart(map_agg).mark_circle(opacity=0.8).encode(
        longitude=alt.Longitude("Longitude:Q"),
        latitude=alt.Latitude("Latitude:Q"),
        size=alt.Size("Sales:Q", scale=alt.Scale(range=[50, 800]), title="Sales"),
        color=alt.condition(state_select, "State:N", alt.value("#d3d3d3")),
        tooltip=["State:N", alt.Tooltip("Sales:Q", format=",.0f")]
    ).add_params(state_select).properties(height=450)

    scatter_plot = alt.Chart(map_data).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X("Sales:Q", title="Sales"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color("State:N", scale=alt.Scale(scheme="category20"), legend=None),
        tooltip=["State:N", alt.Tooltip("Sales:Q", format=",.0f"), "Quantity:Q"]
    ).transform_filter(state_select).properties(height=450, width=300)

    center.altair_chart(style_chart(map_view & scatter_plot), use_container_width=True)
    center.markdown("")