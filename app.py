import streamlit as st
import altair as alt
import pandas as pd

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

# Histogram: Distribution of Prices
hist = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("price:Q",
                bin=alt.Bin(maxbins=30),
                title="Nightly Price ($)"),
        y=alt.Y("count()", title="Number of Listings"),
        tooltip=[alt.Tooltip("count()", title="Listings")],
        color=room_color,
    )
)

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
    df.groupby("neighbourhood_cleansed")
      .agg(
          count=("neighbourhood_cleansed", "size"),
          avg_price=("price", "mean"),
          avg_min_nights=("minimum_nights", "mean"),
      )
      .reset_index()
      .nlargest(10, "count")                 # keep 10 busiest neighbourhoods
      .sort_values("count", ascending=False) # sort for display
)

bars = (
    alt.Chart(bar_data)
    .mark_bar(size=16)
    .encode(
        y=alt.Y("neighbourhood_cleansed:N",
                sort="-x",
                title="Neighbourhood"),
        x=alt.X("count:Q",
                title="Number of Listings"),
        color=alt.Color("avg_price:Q",
                        title="Avg. Nightly Price ($)",
                        scale=alt.Scale(scheme="blues")),
        tooltip=[
            "neighbourhood_cleansed:N",
            alt.Tooltip("count:Q", title="Listings"),
            alt.Tooltip("avg_price:Q", format="$.0f", title="Avg. Price"),
            alt.Tooltip("avg_min_nights:Q",
                        format=".1f", title="Avg. Min Nights"),
        ],
    )
)

# Add text labels for counts
labels = (
    bars.mark_text(
        align="left",
        baseline="middle",
        dx=3, color="black"
    ).encode(text="count:Q")
)

bar = (bars + labels).properties(height=alt.Step(22))

# Boxplot: Nightly-Price Distribution by Room Type
# base box-and-whisker 
box = (
    alt.Chart(df)
    .mark_boxplot(extent="min-max")
    .encode(
        y=alt.Y("room_type:N", sort="-x", title="Room Type"),
        x=alt.X("price:Q", title="Nightly Price ($)"),
        color=room_color,
    )
)

# invisible dot holding the full summary for the tooltip
stats = (
    alt.Chart(df)
    .transform_aggregate(
        median_price="median(price)",
        q1_price="q1(price)",
        q3_price="q3(price)",
        min_price="min(price)",
        max_price="max(price)",
        groupby=["room_type"],
    )
    .mark_circle(size=0, opacity=0)            
    .encode(
        y="room_type:N",
        x="median_price:Q",                     
        tooltip=[
            "room_type:N",
            alt.Tooltip("median_price:Q", format="$.0f", title="Median"),
            alt.Tooltip("q1_price:Q", format="$.0f", title="1st Quartile"),
            alt.Tooltip("q3_price:Q", format="$.0f", title="3rd Quartile"),
            alt.Tooltip("min_price:Q", format="$.0f", title="Min"),
            alt.Tooltip("max_price:Q", format="$.0f", title="Max"),
        ],
    )
)

# layer boxplot + invisible tooltip layer
boxplot = (
    (box + stats)
    .properties(height=alt.Step(28))
)

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
    st.subheader("Price Distribution by Room Type")
    st.altair_chart(boxplot, use_container_width=True)
   
