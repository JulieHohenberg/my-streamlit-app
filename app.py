import streamlit as st
import altair as alt
import pandas as pd

st.title("Inside Airbnb Dashboard by Julie Hohenberg - CSCI3311 Discussion 6.7")

# Load data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, compression="gzip")
    # clean price "$123.00" → 123.0
    df["price"] = (
        df["price"]
        .astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .astype(float)
    )
    return df

df_all = load_data("listings.csv.gz")

# 2 sidebar filters
st.sidebar.header("Filters")

neighb = st.sidebar.selectbox(
    "Neighbourhood",
    ["All"] + sorted(df_all["neighbourhood_cleansed"].dropna().unique())
)

room_opts = sorted(df_all["room_type"].dropna().unique())
room_sel = st.sidebar.multiselect(
    "Room Type (affects all charts)",
    room_opts,
    default=room_opts        # start with every room type selected
)

price_min, price_max = st.sidebar.slider(
    "Nightly Price Range ($)",
    float(df_all["price"].min()),
    float(df_all["price"].max()),
    (float(df_all["price"].min()), float(df_all["price"].max())),
)

# apply filters
df = df_all.copy()
if neighb != "All":
    df = df[df["neighbourhood_cleansed"] == neighb]

df = df[df["room_type"].isin(room_sel)]
df = df[df["price"].between(price_min, price_max)]

# charts!

# Scatter: Price vs. Minimum Nights
scatter = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x=alt.X("price:Q", title="Nightly Price ($)"),
        y=alt.Y("minimum_nights:Q", title="Minimum Nights"),
        color="room_type",
        tooltip=["name", "price", "minimum_nights", "room_type"]
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
        tooltip=["room_type", "count"]
    )
)

# Histogram: Distribution of Prices
hist = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("price:Q", bin=alt.Bin(maxbins=30), title="Nightly Price ($)"),
        y=alt.Y("count()", title="Number of Listings"),
        tooltip=["count()"]
    )
)

# Map of Listings (circles at lat/long)
map_chart = (
    alt.Chart(df)
    .mark_circle(size=30)
    .encode(
        longitude=alt.Longitude("longitude:Q", title=None),
        latitude=alt.Latitude("latitude:Q", title=None),
        color="room_type:N",
        tooltip=["name:N", "price:Q", "room_type:N"]
    )
    .properties(height=400)
)

# Layout
st.altair_chart(scatter, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(bar, use_container_width=True)
with col2:
    st.altair_chart(hist, use_container_width=True)

st.subheader("Listing Locations")
st.altair_chart(map_chart, use_container_width=True)
