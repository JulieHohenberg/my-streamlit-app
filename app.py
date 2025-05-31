import streamlit as st
import altair as alt
import pandas as pd

st.title("Inside Airbnb Dashboard (Streamlit + Altair)")

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

# Sidebar filters

st.sidebar.header("Filters")
neighb = st.sidebar.selectbox(
    "Neighbourhood",
    ["All"] + sorted(df_all["neighbourhood_cleansed"].dropna().unique())
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
df = df[df["price"].between(price_min, price_max)]


# charts!

# Scatter: Price vs. Minimum Nights
scatter = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x="price",
        y="minimum_nights",
        color="room_type",
        tooltip=["name", "price", "minimum_nights", "room_type"]
    )
    .interactive()   # from toolkit example
)

# Bar: Listings by Room Type
bar_data = (
    df.groupby("room_type").size().reset_index(name="count")
)
bar = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        y=alt.Y("room_type:N", sort="-x"),
        x="count:Q",
        tooltip=["room_type", "count"]
    )
)

# Histogram: Distribution of Prices
hist = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("price", bin=alt.Bin(maxbins=30), title="Price ($)"),
        y="count()",
        tooltip=["count()"]
    )
)

# Layout
st.altair_chart(scatter, use_container_width=True)
col1, col2 = st.columns(2)
with col1:
    st.altair_chart(bar, use_container_width=True)
with col2:
    st.altair_chart(hist, use_container_width=True)
