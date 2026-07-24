import json
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Lab 4 - Malaysia Population Map",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = PROJECT_ROOT / "archive" / "my.json"

IMAGINARY_STATES = pd.DataFrame(
    [
        {"State": "Pulau Data", "Latitude": 3.7, "Longitude": 104.6},
        {"State": "Cyberjaya Islands", "Latitude": 2.95, "Longitude": 101.66},
    ]
)


@st.cache_data
def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_malaysia_states(geojson_data: dict) -> list[str]:
    states = [
        feature["properties"]["name"]
        for feature in geojson_data["features"]
        if "name" in feature.get("properties", {})
    ]
    return sorted(states)


def generate_population_data(states: list[str], low: int, high: int, seed: int) -> pd.DataFrame:
    np.random.seed(seed)
    population = np.random.randint(low, high + 1, size=len(states))
    return pd.DataFrame({"State": states, "Population": population})


def generate_gdp_data(states: list[str], low: int, high: int, seed: int) -> pd.DataFrame:
    np.random.seed(seed)
    gdp = np.random.randint(low, high + 1, size=len(states))
    return pd.DataFrame({"State": states, "GDP": gdp})


def format_value(value: int, data_type: str) -> str:
    if data_type == "Population":
        return f"{value:,} people"
    return f"RM {value:,} million"


def make_choropleth_map(
    geojson_data: dict,
    data: pd.DataFrame,
    value_column: str,
    color_scheme: str,
    show_imaginary_states: bool,
) -> folium.Map:
    malaysia_map = folium.Map(
        location=[4.2, 109.5],
        zoom_start=6,
        tiles="OpenStreetMap",
    )

    folium.Choropleth(
        geo_data=geojson_data,
        name=f"{value_column} Distribution",
        data=data,
        columns=["State", value_column],
        key_on="feature.properties.name",
        fill_color=color_scheme,
        fill_opacity=0.78,
        line_opacity=0.8,
        line_color="black",
        legend_name=f"{value_column} Distribution",
        nan_fill_color="lightgray",
    ).add_to(malaysia_map)

    lookup = data.set_index("State")[value_column].to_dict()
    for feature in geojson_data["features"]:
        state_name = feature["properties"]["name"]
        value = lookup.get(state_name)
        feature["properties"]["DisplayValue"] = (
            format_value(int(value), value_column) if value is not None else "No data"
        )

    folium.GeoJson(
        geojson_data,
        name="State labels",
        style_function=lambda feature: {
            "fillOpacity": 0,
            "color": "black",
            "weight": 0.8,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "DisplayValue"],
            aliases=["State", value_column],
            localize=True,
            sticky=True,
        ),
    ).add_to(malaysia_map)

    if show_imaginary_states:
        for row in IMAGINARY_STATES.itertuples(index=False):
            folium.Marker(
                location=[row.Latitude, row.Longitude],
                popup=f"{row.State} is an imaginary state marker.",
                tooltip=row.State,
                icon=folium.Icon(color="purple", icon="info-sign"),
            ).add_to(malaysia_map)

    folium.LayerControl().add_to(malaysia_map)
    return malaysia_map


try:
    geojson = load_geojson(GEOJSON_PATH)
except FileNotFoundError:
    st.error(f"Malaysia GeoJSON not found at: {GEOJSON_PATH}")
    st.stop()

malaysia_states = get_malaysia_states(geojson)

st.sidebar.title("Week 6 Lab")
st.sidebar.subheader("5.1 Experiment with the Data")

data_type = st.sidebar.radio("Dataset to display", ["Population", "GDP"])
color_scheme = st.sidebar.selectbox(
    "Map color scheme",
    ["YlOrRd", "BuGn", "Blues", "Greens"],
)
show_imaginary_states = st.sidebar.checkbox("Add imaginary state markers", value=False)
seed = st.sidebar.slider("Random seed", min_value=1, max_value=100, value=42)

if data_type == "Population":
    low_value, high_value = st.sidebar.slider(
        "Population range",
        min_value=100_000,
        max_value=20_000_000,
        value=(1_000_000, 10_000_000),
        step=100_000,
    )
    map_data = generate_population_data(malaysia_states, low_value, high_value, seed)
else:
    low_value, high_value = st.sidebar.slider(
        "GDP range, in RM millions",
        min_value=10_000,
        max_value=200_000,
        value=(10_000, 100_000),
        step=5_000,
    )
    map_data = generate_gdp_data(malaysia_states, low_value, high_value, seed)

st.title("Malaysia Choropleth Map")
st.markdown("#### Ameer Edzzad Shah - 22005680")
st.caption(
    "Generate population or GDP data and display it using Malaysia state boundaries."
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Dataset", data_type)
metric_2.metric("Regions", len(map_data))
metric_3.metric("Minimum value", f"{map_data[data_type].min():,}")
metric_4.metric("Maximum value", f"{map_data[data_type].max():,}")

malaysia_map = make_choropleth_map(
    geojson,
    map_data,
    data_type,
    color_scheme,
    show_imaginary_states,
)
st_folium(malaysia_map, width=1000, height=620)

st.subheader("Generated Data")
st.dataframe(
    map_data.sort_values(data_type, ascending=False),
    width="stretch",
    hide_index=True,
)

st.markdown("---")
st.caption(f"GeoJSON source file: {GEOJSON_PATH}")
