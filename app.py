from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="CSV Data Explorer", page_icon="📊", layout="wide")

SAMPLE_FILE = Path(__file__).parent / "data" / "sample_sales.csv"
REQUIRED_COLUMNS = ["Date", "Category", "Product", "City", "Quantity", "UnitPrice"]


def clean_data(df):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df = df.dropna(subset=REQUIRED_COLUMNS)
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] >= 0)]
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df


st.title("📊 CSV Data Explorer")
st.write("Explore sales data with Python, Pandas and Streamlit.")

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    st.caption("No file? The app uses included sample data.")

try:
    if uploaded_file is None:
        data = pd.read_csv(SAMPLE_FILE)
        st.info("Showing example sales data. You can also upload your own CSV.")
    else:
        data = pd.read_csv(uploaded_file)
except (OSError, UnicodeError, pd.errors.ParserError) as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
if missing_columns:
    st.error("Missing columns: " + ", ".join(missing_columns))
    st.write("Required columns:", ", ".join(REQUIRED_COLUMNS))
    st.stop()

row_count = len(data)
data = clean_data(data)
if data.empty:
    st.warning("No valid rows found. Check dates, quantities and prices.")
    st.stop()

if len(data) < row_count:
    st.warning(f"Skipped {row_count - len(data)} rows with missing or invalid values.")

with st.sidebar:
    st.header("Filters")
    cities = st.multiselect("City", sorted(data["City"].unique()))
    categories = st.multiselect("Category", sorted(data["Category"].unique()))

filtered = data.copy()
if cities:
    filtered = filtered[filtered["City"].isin(cities)]
if categories:
    filtered = filtered[filtered["Category"].isin(categories)]

if filtered.empty:
    st.warning("No data matches these filters.")
    st.stop()

revenue = filtered["Revenue"].sum()
orders = len(filtered)
units = filtered["Quantity"].sum()
average_order = revenue / orders

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total revenue", f"€{revenue:,.2f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Units sold", f"{units:,.0f}")
c4.metric("Average order", f"€{average_order:,.2f}")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Revenue by month")
    monthly = filtered.copy()
    monthly["Month"] = monthly["Date"].dt.to_period("M").astype(str)
    monthly = monthly.groupby("Month")["Revenue"].sum().sort_index()
    st.line_chart(monthly)

with right:
    st.subheader("Revenue by category")
    by_category = filtered.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
    st.bar_chart(by_category)

st.subheader("Revenue by city")
by_city = filtered.groupby("City")["Revenue"].sum().sort_values(ascending=False)
st.bar_chart(by_city)

st.subheader("Filtered data")
st.dataframe(filtered.sort_values("Date", ascending=False), use_container_width=True)

csv_data = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", csv_data, "filtered_sales.csv", "text/csv")
st.caption("Demo dataset is synthetic and is included only for testing.")
