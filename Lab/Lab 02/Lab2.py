from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Lab 2 - SDG Dashboard",
    layout="wide",
)

DATA_PATH = Path(__file__).resolve().parents[2] / "archive" / "sdg_index_2000-2022.csv"
PERFORMANCE_ORDER = ["Low Performance", "Medium Performance", "High Performance"]
PERFORMANCE_COLORS = ["#d95f59", "#f2b134", "#2a9d8f"]


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data.columns = data.columns.str.strip().str.lower()

    required_columns = {"country", "year", "sdg_index_score", "goal_4_score"}
    missing_columns = sorted(required_columns.difference(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    numeric_columns = ["year", "sdg_index_score"] + [
        column for column in data.columns if column.startswith("goal_")
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(
        subset=["country", "year", "sdg_index_score", "goal_4_score"]
    ).copy()
    data["year"] = data["year"].astype(int)
    data["performance_group"] = pd.cut(
        data["sdg_index_score"],
        bins=[0, 50, 70, 100],
        labels=PERFORMANCE_ORDER,
        include_lowest=True,
    )
    return data


def performance_color(field: str = "performance_group:N") -> alt.Color:
    return alt.Color(
        field,
        title="Performance Group",
        sort=PERFORMANCE_ORDER,
        scale=alt.Scale(
            domain=PERFORMANCE_ORDER,
            range=PERFORMANCE_COLORS,
        ),
    )


def style_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_axis(
            labelFontSize=12,
            titleFontSize=13,
            gridColor="#e8e8e8",
            domain=False,
        )
        .configure_legend(labelFontSize=12, titleFontSize=13)
        .configure_title(fontSize=18, anchor="start")
        .configure_view(strokeWidth=0)
    )


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Unable to load the SDG dataset: {error}")
    st.stop()


st.sidebar.title("Lab 2 - SDG Dashboard")
st.sidebar.caption("Sustainable Development Report, 2000-2022")

page = st.sidebar.radio(
    "Choose a section",
    [
        "1. Exploratory Graphics",
        "2. Presentation Graphics",
        "3. Linked Highlighting",
        "4. SDG Reflection",
    ],
)

years = sorted(df["year"].unique())
selected_year = st.sidebar.slider(
    "Analysis year",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=int(max(years)),
    step=1,
)
year_df = df[df["year"] == selected_year].copy()

st.sidebar.markdown("---")
st.sidebar.success("Archive CSV loaded")
st.sidebar.metric("Records", f"{len(df):,}")
st.sidebar.metric("Countries", f"{df['country'].nunique():,}")
st.sidebar.caption(f"Source: {DATA_PATH.name}")

st.title("Sustainable Development Goals Dashboard")
st.markdown("#### Ameer Edzzad Shah - 22005680")
st.caption(
    "Explore global SDG performance, education outcomes, and changes over time."
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Selected year", selected_year)
metric_2.metric("Countries", f"{year_df['country'].nunique():,}")
metric_3.metric("Average SDG Index", f"{year_df['sdg_index_score'].mean():.1f}")
metric_4.metric("Average SDG 4", f"{year_df['goal_4_score'].mean():.1f}")

st.markdown("---")


if page == "1. Exploratory Graphics":
    st.header("1. Exploratory Graphics")
    st.write(
        "Explore the relationship between quality education and overall SDG "
        f"performance in {selected_year}. Zoom, pan, and inspect countries using "
        "the tooltip."
    )

    groups = st.multiselect(
        "Performance groups",
        PERFORMANCE_ORDER,
        default=PERFORMANCE_ORDER,
    )
    exploratory_df = year_df[
        year_df["performance_group"].astype(str).isin(groups)
    ]

    scatter = (
        alt.Chart(exploratory_df)
        .mark_circle(size=95, opacity=0.78)
        .encode(
            x=alt.X(
                "goal_4_score:Q",
                title="SDG 4: Quality Education Score",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                "sdg_index_score:Q",
                title="Overall SDG Index Score",
                scale=alt.Scale(domain=[30, 90]),
            ),
            color=performance_color(),
            tooltip=[
                alt.Tooltip("country:N", title="Country"),
                alt.Tooltip("goal_4_score:Q", title="SDG 4 Score", format=".1f"),
                alt.Tooltip(
                    "sdg_index_score:Q", title="SDG Index Score", format=".1f"
                ),
                alt.Tooltip("performance_group:N", title="Performance Group"),
            ],
        )
        .properties(height=500, title=f"Education and SDG Performance, {selected_year}")
        .interactive()
    )

    if exploratory_df.empty:
        st.warning("Select at least one performance group to display the chart.")
    else:
        st.altair_chart(style_chart(scatter), width="stretch")

    st.info(
        "The chart generally shows a positive relationship: countries with stronger "
        "education outcomes also tend to achieve higher overall SDG Index scores."
    )


elif page == "2. Presentation Graphics":
    st.header("2. Presentation Graphics")
    st.write(
        "This presentation chart summarizes average SDG achievement by performance "
        f"group for {selected_year}."
    )

    summary = (
        year_df.groupby("performance_group", observed=False)
        .agg(
            average_score=("sdg_index_score", "mean"),
            countries=("country", "nunique"),
        )
        .reset_index()
        .dropna(subset=["average_score"])
    )

    bars = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(
                "performance_group:N",
                title=None,
                sort=PERFORMANCE_ORDER,
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                "average_score:Q",
                title="Average SDG Index Score",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=performance_color(),
            tooltip=[
                alt.Tooltip("performance_group:N", title="Performance Group"),
                alt.Tooltip(
                    "average_score:Q", title="Average Score", format=".1f"
                ),
                alt.Tooltip("countries:Q", title="Countries"),
            ],
        )
    )

    labels = bars.mark_text(dy=-12, fontSize=15, fontWeight="bold").encode(
        text=alt.Text("average_score:Q", format=".1f"),
        color=alt.value("#333333"),
    )

    presentation_chart = (bars + labels).properties(
        height=480,
        title=f"Average SDG Index Score by Performance Group, {selected_year}",
    )
    st.altair_chart(style_chart(presentation_chart), width="stretch")

    best_group = summary.loc[summary["average_score"].idxmax()]
    st.info(
        f"{best_group['performance_group']} records the highest group average "
        f"({best_group['average_score']:.1f}) in {selected_year}."
    )


elif page == "3. Linked Highlighting":
    st.header("3. Linked Highlighting")
    st.write(
        "Hover over a bar or point to highlight the same performance group across "
        "both charts."
    )

    highlight = alt.selection_point(
        name="performance_highlight",
        fields=["performance_group"],
        on="pointerover",
        clear="pointerout",
        empty=True,
    )

    base = alt.Chart(year_df).encode(
        color=alt.condition(
            highlight,
            performance_color(),
            alt.value("#d8d8d8"),
        )
    )

    linked_scatter = base.mark_circle(size=95, opacity=0.8).encode(
        x=alt.X(
            "goal_4_score:Q",
            title="SDG 4: Quality Education Score",
            scale=alt.Scale(domain=[0, 100]),
        ),
        y=alt.Y(
            "sdg_index_score:Q",
            title="Overall SDG Index Score",
            scale=alt.Scale(domain=[30, 90]),
        ),
        tooltip=[
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("goal_4_score:Q", title="SDG 4 Score", format=".1f"),
            alt.Tooltip("sdg_index_score:Q", title="SDG Index", format=".1f"),
            alt.Tooltip("performance_group:N", title="Performance Group"),
        ],
    ).properties(width=590, height=430, title="Country-Level Scores")

    linked_bar = base.mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X(
            "performance_group:N",
            title=None,
            sort=PERFORMANCE_ORDER,
            axis=alt.Axis(labelAngle=-20),
        ),
        y=alt.Y("count():Q", title="Number of Countries"),
        tooltip=[
            alt.Tooltip("performance_group:N", title="Performance Group"),
            alt.Tooltip("count():Q", title="Countries"),
        ],
    ).properties(width=360, height=430, title="Countries per Performance Group")

    linked_chart = (linked_scatter | linked_bar).add_params(highlight)
    st.altair_chart(style_chart(linked_chart), width="stretch")

    st.info(
        "Linked highlighting connects the summary and detail views, making it easier "
        "to see where each performance group appears in the education relationship."
    )


elif page == "4. SDG Reflection":
    st.header("4. SDG Reflection")
    st.write(
        "Compare the long-term SDG 4 progress of selected countries with the global "
        "average."
    )

    latest_country_scores = (
        df[df["year"] == df["year"].max()]
        .sort_values("goal_4_score", ascending=False)["country"]
        .tolist()
    )
    default_countries = [
        country
        for country in ["Malaysia", "Singapore", "Indonesia"]
        if country in latest_country_scores
    ]
    selected_countries = st.multiselect(
        "Countries to compare",
        options=sorted(df["country"].unique()),
        default=default_countries,
        max_selections=8,
    )

    global_average = (
        df.groupby("year", as_index=False)["goal_4_score"]
        .mean()
        .assign(country="Global Average")
    )
    country_history = df[df["country"].isin(selected_countries)][
        ["country", "year", "goal_4_score"]
    ]
    reflection_df = pd.concat(
        [country_history, global_average],
        ignore_index=True,
    )

    line_chart = (
        alt.Chart(reflection_df)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X(
                "year:O",
                title="Year",
                axis=alt.Axis(labelAngle=-45, labelOverlap=True),
            ),
            y=alt.Y(
                "goal_4_score:Q",
                title="SDG 4: Quality Education Score",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color(
                "country:N",
                title="Country",
                scale=alt.Scale(scheme="tableau10"),
            ),
            strokeDash=alt.condition(
                alt.datum.country == "Global Average",
                alt.value([6, 4]),
                alt.value([1, 0]),
            ),
            tooltip=[
                alt.Tooltip("country:N", title="Country"),
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("goal_4_score:Q", title="SDG 4 Score", format=".1f"),
            ],
        )
        .properties(height=500, title="SDG 4 Progress, 2000-2022")
    )
    st.altair_chart(style_chart(line_chart), width="stretch")

    st.subheader("Reflection")
    st.write(
        "SDG 4 focuses on inclusive and equitable quality education. The long-term "
        "trend shows that education outcomes differ substantially across countries, "
        "even when the global average improves. Education supports poverty reduction, "
        "employment, equality, and informed participation in society, so progress in "
        "SDG 4 also strengthens many other Sustainable Development Goals. Countries "
        "below the global average may need targeted investment in school access, "
        "teacher quality, learning resources, and support for disadvantaged learners. "
        "Tracking these scores over time helps identify persistent gaps and shows "
        "whether education policies are producing sustained improvement."
    )
