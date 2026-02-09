import streamlit as st
import pandas as pd
from psycopg2 import connect
from os import environ as ENV
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots

load_dotenv()

st.set_page_config(page_title="Commodity Chart", layout="wide")


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    return conn


@st.cache_data(ttl=300)
def fetch_data(query):
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    conn = get_conn()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


SQL_QUERY = """
SELECT * FROM market_records
JOIN commodities AS c
USING (commodity_id)
WHERE commodity_id=10"""

df = fetch_data(SQL_QUERY)

# Prepare data for candlestick chart
df_chart = df.copy()
df_chart = df_chart.sort_values('recorded_at', ascending=True)

# Resample mixed granularity data to daily OHLC candles
df_daily = df_chart.resample('D', on='recorded_at').agg({
    'open_price': 'first',
    'day_high': 'max',
    'day_low': 'min',
    'price': 'last',
    'volume': 'last',
    'commodity_name': 'first',
    'symbol': 'first'
}).dropna()

# Calculate Moving Averages
df_daily['MA_7'] = df_daily['price'].rolling(window=7).mean()
df_daily['MA_14'] = df_daily['price'].rolling(window=14).mean()
df_daily['MA_20'] = df_daily['price'].rolling(window=20).mean()

# Title
commodity_name = df_daily['commodity_name'].iloc[0] if 'commodity_name' in df_daily.columns else "Commodity"
symbol = df_daily['symbol'].iloc[0] if 'symbol' in df_daily.columns else ""
st.title(f"📈 {commodity_name} ({symbol}) - Daily Chart")

# Sidebar controls
st.sidebar.header("Chart Settings")
show_volume = st.sidebar.checkbox("Show Volume", value=True)

# Create subplots
row_heights = [0.7, 0.3] if show_volume else [1.0]
rows = 2 if show_volume else 1

fig = make_subplots(
    rows=rows, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=row_heights,
    subplot_titles=('Price', 'Volume') if show_volume else ('Price',)
)

# Candlestick chart
fig.add_trace(
    go.Candlestick(
        x=df_daily.index,
        open=df_daily['open_price'],
        high=df_daily['day_high'],
        low=df_daily['day_low'],
        close=df_daily['price'],
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350',
        name='Price'
    ),
    row=1, col=1
)

# Moving Averages (toggle via Plotly legend)
fig.add_trace(
    go.Scatter(
        x=df_daily.index,
        y=df_daily['MA_7'],
        mode='lines',
        name='MA 7',
        line=dict(color='#FFA500', width=1.5)
    ),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(
        x=df_daily.index,
        y=df_daily['MA_14'],
        mode='lines',
        name='MA 14',
        line=dict(color='#00CED1', width=1.5)
    ),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(
        x=df_daily.index,
        y=df_daily['MA_20'],
        mode='lines',
        name='MA 20',
        line=dict(color='#FF69B4', width=1.5)
    ),
    row=1, col=1
)

# Volume bars
if show_volume:
    vol_colors = ['#26a69a' if df_daily['price'].iloc[i] >= df_daily['open_price'].iloc[i]
                  else '#ef5350' for i in range(len(df_daily))]

    fig.add_trace(
        go.Bar(
            x=df_daily.index,
            y=df_daily['volume'],
            marker_color=vol_colors,
            name='Volume',
            showlegend=False
        ),
        row=2, col=1
    )
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

# Update layout
fig.update_layout(
    template='plotly_dark',
    xaxis_rangeslider_visible=False,
    height=700,
    hovermode='x unified',
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='left',
        x=0
    )
)

fig.update_yaxes(title_text="Price", row=1, col=1)

# Display chart in Streamlit
st.plotly_chart(fig, use_container_width=True)

# Stats section
col1, col2, col3, col4 = st.columns(4)
latest_price = df_daily['price'].iloc[-1]
prev_price = df_daily['price'].iloc[-2] if len(df_daily) > 1 else latest_price
price_change = latest_price - prev_price
price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0

col1.metric("Latest Price", f"${latest_price:.2f}",
            f"{price_change_pct:+.2f}%")
col2.metric("Day High", f"${df_daily['day_high'].iloc[-1]:.2f}")
col3.metric("Day Low", f"${df_daily['day_low'].iloc[-1]:.2f}")
col4.metric("Volume", f"{df_daily['volume'].iloc[-1]:,.0f}")
