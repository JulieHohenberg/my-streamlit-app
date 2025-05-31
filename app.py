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
bar_data = (
    df.groupby("room_type")
      .agg(count=("room_type", "size"),
           avg_price=("price", "mean"),
           avg_min_nights=("minimum_nights", "mean"))
      .reset_index()
)

bars = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        y=alt.Y("room_type:N", sort="-x", title="Room Type"),
        x=alt.X("count:Q", title="Number of Listings"),
        color=alt.Color("avg_price:Q",
                        scale=alt.Scale(scheme="blues"),
                        title="Avg. Nightly Price ($)"),
        tooltip=[
            "room_type:N",
            alt.Tooltip("count:Q", title="Listings"),
            alt.Tooltip("avg_price:Q", format="$.0f", title="Avg. Price"),
            alt.Tooltip("avg_min_nights:Q", format=".1f", title="Avg. Min Nights"),
        ],
    )
)

# Text overlay with the exact count
labels = (
    bars.mark_text(
        align="left",
        baseline="middle",
        dx=3,  # nudges text right of bar
        color="black"
    ).encode(text=alt.Text("count:Q"))
)

bar = (bars + labels).properties(height=alt.Step(28))

# Histogram: Distribution of Prices
hist = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X(
            "price:Q",
            bin=alt.Bin(maxbins=30),
            title="Nightly Price ($)"
        ),
        y=alt.Y("count()", title="Number of Listings"),
        # Tooltip expects either a list of field names or individual Tooltip objects
        tooltip=[alt.Tooltip("count()", title="Number of Listings")],
        color=room_color,   # fine if you want bars colored by room_type
    )
)

# Map: Albany basemap + listing dots

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
    st.subheader("Listing Locations")
    # Streamlit’s built-in map (PyDeck under the hood)
    st.map(df[["latitude", "longitude"]], zoom=11)
