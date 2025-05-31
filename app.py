import streamlit as st
import altair as alt
import pandas as pd
from vega_datasets import data  # for the map!

st.set_page_config(page_title="Inside Albany Airbnbs", layout="wide")
st.title("Inside Albany’s Airbnbs")

# load data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, compression="gzip")
    df["price"] = (
        df["price"]
        .astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .astype(float)
    )
    return df

df_all = load_data("listings.csv.gz")

# sidebar filters
st.sidebar.header("Filters")

neighb = st.sidebar.selectbox(
    "Neighbourhood",
    ["All"] + sorted(df_all["neighbourhood_cleansed"].dropna().unique()),
)

room_opts = sorted(df_all["room_type"].dropna().unique())
room_sel = st.sidebar.multiselect(
    "Room Type (affects all charts)",
    room_opts,
    default=room_opts,
)

price_min, price_max = st.sidebar.slider(
    "Nightly Price ($)",
    float(df_all["price"].min()),
    float(df_all["price"].max()),
    (float(df_all["price"].min()), float(df_all["price"].max())),
)

# Apply filters
df = df_all.copy()
if neighb != "All":
    df = df[df["neighbourhood_cleansed"] == neighb]
df = df[df["room_type"].isin(room_sel)]
df = df[df["price"].between(price_min, price_max)]

# Common color encoding
room_color = alt.Color("room_type:N", title="Room Type",
                       scale=alt.Scale(scheme="dark2"))

# charts!

# Scatter: Price vs. Minimum Nights
scatter = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x=alt.X("price:Q", title="Nightly Price ($)"),
        y=alt.Y("minimum_nights:Q", title="Minimum Nights"),
        color=room_color,
        tooltip=["name:N", "price:Q", "minimum_nights:Q", "room_type:N"],
    )
    .interactive()
)

# Bar: Listings by Room Type
bar_data = df.groupby("room_type").size().reset_index(name="count")
bar = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        y=alt.Y("room_type:N", sort="-x", title="Room Type"),
        x=alt.X("count:Q", title="Number of Listings"),
        color=room_color,
        tooltip=["room_type:N", "count:Q"],
    )
)

# Histogram: Distribution of Prices
hist = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("price:Q",
                bin=alt.Bin(maxbins=30),
                title="Nightly Price ($)"),
        y=alt.Y("count()", title="Number of Listings"),
        tooltip=["count()"],
        color=room_color,
    )
)

# Map – Albany basemap + listing dots
counties = alt.topo_feature(data.us_10m.url, "counties")

albany_map = (
    alt.Chart(counties)
    .mark_geoshape(fill="whitesmoke", stroke="gainsboro")
    .transform_filter(
        alt.datum.id == 36001  # FIPS code for Albany County, NY
    )
    .project(type="mercator")
)

zoom = alt.selection_interval(bind="scales")  # drag / scroll to zoom

dots = (
    alt.Chart(df)
    .mark_circle(size=40, opacity=0.8)
    .encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        color=room_color,
        tooltip=["name:N", "price:Q", "room_type:N"],
    )
    .add_params(zoom)
)

map_chart = (albany_map + dots).properties(height=400)

# 2x2 grid layout
c1, c2 = st.columns(2)
with c1:
    st.altair_chart(scatter, use_container_width=True)
with c2:
    st.altair_chart(bar, use_container_width=True)

d1, d2 = st.columns(2)
with d1:
    st.altair_chart(hist, use_container_width=True)
with d2:
    st.altair_chart(map_chart, use_container_width=True)
