import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style="dark")


# ============================================================

def create_monthly_orders_df(df):
    """Menyiapkan dataframe jumlah pesanan & revenue per bulan."""
    monthly_orders_df = df.resample(rule="ME", on="order_purchase_timestamp").agg({
        "order_id": "nunique",
        "payment_value": "sum"
    })
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df = monthly_orders_df.rename(columns={
        "order_purchase_timestamp": "order_date",
        "order_id": "order_count",
        "payment_value": "revenue"
    })
    return monthly_orders_df


def create_sum_category_revenue_df(df):
    """Menyiapkan dataframe revenue per kategori produk (harga + ongkir)."""
    sum_category_revenue_df = df.groupby("product_category_name_english").agg({
        "price": "sum",
        "freight_value": "sum"
    })
    sum_category_revenue_df["revenue"] = (sum_category_revenue_df["price"]
                                          + sum_category_revenue_df["freight_value"])
    sum_category_revenue_df = sum_category_revenue_df.sort_values(
        by="revenue", ascending=False).reset_index()
    return sum_category_revenue_df


def create_bystate_df(df):
    """Menyiapkan dataframe jumlah pesanan per negara bagian."""
    bystate_df = df.groupby(by="customer_state").order_id.nunique().reset_index()
    bystate_df = bystate_df.rename(columns={"order_id": "order_count"})
    bystate_df = bystate_df.sort_values(by="order_count", ascending=False)
    return bystate_df


def create_rfm_df(df):
    """Menyiapkan dataframe RFM (Recency, Frequency, Monetary) per pelanggan."""
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max",  # tanggal order terakhir
        "order_id": "nunique",              # frequency
        "payment_value": "sum"              # monetary
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(
        lambda x: (recent_date - x).days)
    rfm_df = rfm_df.drop(columns=["max_order_timestamp"])
    return rfm_df


# Load data hasil pembersihan dari notebook
all_df = pd.read_csv("main_data.csv")

datetime_columns = ["order_purchase_timestamp"]
all_df = all_df.sort_values(by="order_purchase_timestamp")
all_df = all_df.reset_index(drop=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])


# Filter data (sidebar)
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) &
                 (all_df["order_purchase_timestamp"] <= str(end_date))]

# Menyiapkan berbagai dataframe
monthly_orders_df = create_monthly_orders_df(main_df)
sum_category_revenue_df = create_sum_category_revenue_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# Dashboard utama
st.header("Brazilian E-Commerce (Olist) Dashboard :sparkles:")


# Performa bulanan
st.subheader("Monthly Orders & Revenue")

col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_revenue = format_currency(
        monthly_orders_df.revenue.sum(), "BRL", locale="es_CO")
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(
    monthly_orders_df["order_date"],
    monthly_orders_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9"
)
ax.plot(
    monthly_orders_df["order_date"],
    monthly_orders_df["revenue"] / monthly_orders_df["revenue"].max()
    * monthly_orders_df["order_count"].max(),
    marker="s",
    linewidth=2,
    color="#4C72B0",
    alpha=0.5
)
ax.set_title("Number of Orders per Month (revenue di-skala untuk perbandingan)",
             loc="center", fontsize=18)
ax.set_ylabel("Number of Orders", fontsize=14)
ax.tick_params(axis="x", labelsize=12, rotation=45)
ax.tick_params(axis="y", labelsize=12)
ax.grid(alpha=0.3)
st.pyplot(fig)


# Performa kategori produk
st.subheader("Best & Worst Performing Product Category")

total_revenue_all = sum_category_revenue_df["revenue"].sum()
sum_category_revenue_df["contribution_pct"] = (
    sum_category_revenue_df["revenue"] / total_revenue_all * 100)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="revenue",
    y="product_category_name_english",
    data=sum_category_revenue_df.head(5),
    palette=colors,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Revenue (BRL)", fontsize=30)
ax[0].set_title("Best Performing Category", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=35)
ax[0].tick_params(axis="x", labelsize=30)

worst_df = sum_category_revenue_df.sort_values(by="revenue", ascending=True).head(5)
sns.barplot(
    x="revenue",
    y="product_category_name_english",
    data=worst_df,
    palette=colors,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Revenue (BRL)", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Category", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=35)
ax[1].tick_params(axis="x", labelsize=30)

st.pyplot(fig)

# Demografi pelanggan per wilayah
st.subheader("Customer Demographics")

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9"] + ["#D3D3D3"] * (len(bystate_df) - 1)

sns.barplot(
    x="order_count",
    y="customer_state",
    data=bystate_df,
    palette=colors,
    ax=ax
)
ax.set_title("Number of Orders by Customer State", loc="center", fontsize=30)
ax.set_ylabel("State", fontsize=20)
ax.set_xlabel("Number of Orders", fontsize=20)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=15)

st.pyplot(fig)

# RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale="es_CO")
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(
    y="recency",
    x="customer_unique_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    palette=colors,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_unique_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=30)
ax[0].tick_params(axis="x", labelsize=20, rotation=45)

sns.barplot(
    y="frequency",
    x="customer_unique_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    palette=colors,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_unique_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=30)
ax[1].tick_params(axis="x", labelsize=20, rotation=45)

sns.barplot(
    y="monetary",
    x="customer_unique_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    palette=colors,
    ax=ax[2]
)
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_unique_id", fontsize=30)
ax[2].set_title("By Monetary (BRL)", loc="center", fontsize=50)
ax[2].tick_params(axis="y", labelsize=30)
ax[2].tick_params(axis="x", labelsize=20, rotation=45)

st.pyplot(fig)

st.caption("Data Source: E-Commerce Public Dataset (Olist)")
