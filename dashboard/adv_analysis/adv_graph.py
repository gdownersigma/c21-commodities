import pandas as pd
from psycopg2 import connect
from os import environ as ENV
from dotenv import load_dotenv
import streamlit as st

import plotly.graph_objects as go
from plotly.subplots import make_subplots


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


def fetch_data(query):
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    conn = get_conn()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


SQL_QUERY = f"""
SELECT * FROM market_records
JOIN commodities AS c
USING (commodity_id)
WHERE commodity_id={st.session_state.analysis_commodity_id}
  AND recorded_at >= CURRENT_DATE - INTERVAL '1 month'
  AND previous_close IS NULL;"""

df = fetch_data(SQL_QUERY)

df_chart = df.copy()
df_chart = df_chart.sort_values('recorded_at', ascending=False)
df_chart.set_index('recorded_at', inplace=True)

# Calculate support and resistance levels
resistance = df_chart['day_high'].max()
support = df_chart['day_low'].min()
pivot = (resistance + support + df_chart['price'].iloc[-1]) / 3

# Calculate moving averages (adaptive to data size)
n = len(df_chart)
ma_short = max(5, n // 10)
ma_mid = max(10, n // 5)
ma_long = max(20, n // 3)

df_chart['MA_short'] = df_chart['price'].rolling(window=ma_short).mean()
df_chart['MA_mid'] = df_chart['price'].rolling(window=ma_mid).mean()
df_chart['MA_long'] = df_chart['price'].rolling(window=ma_long).mean()

# Calculate RSI
rsi_period = max(5, n // 6)
delta = df_chart['price'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
rs = gain / loss
df_chart['RSI'] = 100 - (100 / (1 + rs))

# Calculate MACD
macd_fast = max(4, n // 8)
macd_slow = max(8, n // 4)
macd_signal = max(3, n // 10)

exp_fast = df_chart['price'].ewm(span=macd_fast, adjust=False).mean()
exp_slow = df_chart['price'].ewm(span=macd_slow, adjust=False).mean()
df_chart['MACD'] = exp_fast - exp_slow
df_chart['MACD_signal'] = df_chart['MACD'].ewm(
    span=macd_signal, adjust=False).mean()
df_chart['MACD_hist'] = df_chart['MACD'] - df_chart['MACD_signal']

# Create figure with subplots: Price+Volume, RSI, MACD
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.6, 0.2, 0.2],
    specs=[[{"secondary_y": True}], [
        {"secondary_y": False}], [{"secondary_y": False}]]
)

# ========== ROW 1: CANDLESTICK + VOLUME ==========
fig.add_trace(
    go.Candlestick(
        x=df_chart.index,
        open=df_chart['open_price'],
        high=df_chart['day_high'],
        low=df_chart['day_low'],
        close=df_chart['price'],
        name='GCUSD',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ),
    row=1, col=1, secondary_y=False
)

# Volume bars
vol_colors = ['#26a69a' if df_chart['price'].iloc[i] >= df_chart['open_price'].iloc[i]
              else '#ef5350' for i in range(len(df_chart))]
fig.add_trace(
    go.Bar(
        x=df_chart.index,
        y=df_chart['volume'],
        name='Volume',
        marker_color=vol_colors,
        opacity=0.4
    ),
    row=1, col=1, secondary_y=True
)

# Moving averages
fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['MA_short'],
        mode='lines', name=f'MA {ma_short}',
        line=dict(color='#FFA500', width=2),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['MA_mid'],
        mode='lines', name=f'MA {ma_mid}',
        line=dict(color='#00CED1', width=2),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['MA_long'],
        mode='lines', name=f'MA {ma_long}',
        line=dict(color='#FF69B4', width=2),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

# Resistance/Support/Pivot lines
fig.add_trace(
    go.Scatter(
        x=[df_chart.index.min(), df_chart.index.max()],
        y=[resistance, resistance],
        mode='lines', name='Resistance',
        line=dict(color='red', width=2, dash='dash'),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

fig.add_trace(
    go.Scatter(
        x=[df_chart.index.min(), df_chart.index.max()],
        y=[support, support],
        mode='lines', name='Support',
        line=dict(color='green', width=2, dash='dash'),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

fig.add_trace(
    go.Scatter(
        x=[df_chart.index.min(), df_chart.index.max()],
        y=[pivot, pivot],
        mode='lines', name='Pivot',
        line=dict(color='yellow', width=1.5, dash='dot'),
        visible='legendonly'
    ),
    row=1, col=1, secondary_y=False
)

# ========== ROW 2: RSI ==========
fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['RSI'],
        mode='lines', name=f'RSI ({rsi_period})',
        line=dict(color='#9370DB', width=2)
    ),
    row=2, col=1
)

# RSI overbought/oversold lines
fig.add_hline(y=70, line_dash="dash", line_color="red",
              opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green",
              opacity=0.5, row=2, col=1)
fig.add_hline(y=50, line_dash="dot", line_color="gray",
              opacity=0.3, row=2, col=1)

# ========== ROW 3: MACD ==========
fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['MACD'],
        mode='lines', name='MACD',
        line=dict(color='#1E90FF', width=2)
    ),
    row=3, col=1
)

fig.add_trace(
    go.Scatter(
        x=df_chart.index, y=df_chart['MACD_signal'],
        mode='lines', name='Signal',
        line=dict(color='#FFA500', width=2)
    ),
    row=3, col=1
)

# MACD histogram
macd_colors = ['#26a69a' if v >=
               0 else '#ef5350' for v in df_chart['MACD_hist']]
fig.add_trace(
    go.Bar(
        x=df_chart.index, y=df_chart['MACD_hist'],
        name='MACD Hist',
        marker_color=macd_colors,
        opacity=0.6
    ),
    row=3, col=1
)

fig.add_hline(y=0, line_dash="solid", line_color="gray",
              opacity=0.5, row=3, col=1)

# ========== ANNOTATIONS ==========
fig.add_annotation(
    x=0.01, xref='paper', y=resistance, yref='y',
    text=f" R: ${resistance:.2f} ",
    showarrow=False, xanchor='left', yanchor='middle',
    font=dict(color='white', size=11, family='Arial Black'),
    bgcolor='rgba(255,0,0,0.8)', bordercolor='red', borderwidth=1, borderpad=2
)

fig.add_annotation(
    x=0.01, xref='paper', y=support, yref='y',
    text=f" S: ${support:.2f} ",
    showarrow=False, xanchor='left', yanchor='middle',
    font=dict(color='white', size=11, family='Arial Black'),
    bgcolor='rgba(0,128,0,0.8)', bordercolor='green', borderwidth=1, borderpad=2
)

fig.add_annotation(
    x=0.01, xref='paper', y=pivot, yref='y',
    text=f" P: ${pivot:.2f} ",
    showarrow=False, xanchor='left', yanchor='middle',
    font=dict(color='black', size=11, family='Arial Black'),
    bgcolor='rgba(255,255,0,0.9)', bordercolor='yellow', borderwidth=1, borderpad=2
)

# ========== LAYOUT ==========
fig.update_layout(
    title={'text': f"📊 {df_chart['commodity_name'].iloc[0]} ({df_chart['symbol'].iloc[0]}) - 1 Month", 'x': 0.5,
           'font': {'size': 20, 'color': '#FFD700'}},
    xaxis3_title='Date',
    xaxis_rangeslider_visible=False,
    height=900,
    template='plotly_dark',
    hovermode='x unified',
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        bgcolor="rgba(0,0,0,0.7)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=10)
    ),
    margin=dict(r=150, t=80)
)

# Y-axis labels
fig.update_yaxes(title_text="Price (USD)", row=1, col=1, secondary_y=False)
fig.update_yaxes(title_text="Volume", row=1, col=1, secondary_y=True,
                 range=[0, df_chart['volume'].max() * 4])
fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
fig.update_yaxes(title_text="MACD", row=3, col=1)

# Range selector
fig.update_xaxes(
    rangeselector=dict(
        buttons=[
            dict(count=1, label="1D", step="day", stepmode="backward"),
            dict(count=7, label="1W", step="day", stepmode="backward"),
            dict(count=14, label="2W", step="day", stepmode="backward"),
            dict(step="all", label="ALL")
        ],
        bgcolor="rgba(50,50,50,0.8)",
        font=dict(color="white"),
        activecolor="rgba(100,100,100,0.9)",
        x=0, y=1.05
    ),
    row=1, col=1
)

# Enable zoom/pan
fig.update_xaxes(fixedrange=False)
fig.update_yaxes(fixedrange=False)

# Crosshair
fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor',
                 spikedash='solid', spikecolor='rgba(255,215,0,0.6)', spikethickness=1)
fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor',
                 spikedash='solid', spikecolor='rgba(255,215,0,0.6)', spikethickness=1)

# Config
config = {
    'scrollZoom': True,
    'displaylogo': False,
    'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
}

fig.show(config=config)
