"""
Advanced Technical Analysis Graph Module

This module provides functions for creating interactive technical analysis charts
with indicators like RSI, MACD, Moving Averages, and Support/Resistance levels.
"""

from contextlib import contextmanager
from typing import Optional
import pandas as pd
from psycopg2 import connect, sql
from os import environ as ENV
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ==================== CONSTANTS ====================

# Colors
COLOR_BULLISH = '#26a69a'
COLOR_BEARISH = '#ef5350'
COLOR_MA_SHORT = '#FFA500'
COLOR_MA_MID = '#00CED1'
COLOR_MA_LONG = '#FF69B4'
COLOR_RSI = '#9370DB'
COLOR_MACD = '#1E90FF'
COLOR_SIGNAL = '#FFA500'
COLOR_RESISTANCE = 'red'
COLOR_SUPPORT = 'green'
COLOR_PIVOT = 'yellow'
COLOR_CROSSHAIR = 'rgba(255,215,0,0.6)'

# RSI Thresholds
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_NEUTRAL = 50

# Chart Layout
CHART_HEIGHT = 900
ROW_HEIGHTS = [0.6, 0.2, 0.2]
VERTICAL_SPACING = 0.03

# Minimum data points required for analysis
MIN_DATA_POINTS = 5


# ==================== DATABASE FUNCTIONS ====================

@contextmanager
def get_db_connection():
    """Context manager that yields a PostgreSQL database connection and ensures cleanup."""
    conn = None
    try:
        conn = connect(
            dbname=ENV.get("DB_NAME"),
            user=ENV.get("DB_USER"),
            password=ENV.get("DB_PASSWORD"),
            host=ENV.get("DB_HOST"),
            port=ENV.get("DB_PORT"),
        )
        yield conn
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")
    finally:
        if conn is not None:
            conn.close()


@st.cache_data(ttl=300)
def fetch_market_data(commodity_id: int, interval: str = '1 month') -> pd.DataFrame:
    """Fetches market data for a specific commodity using parameterized queries."""
    query = """
        SELECT * FROM market_records
        JOIN commodities AS c
        USING (commodity_id)
        WHERE commodity_id = %s
        AND recorded_at >= CURRENT_DATE - INTERVAL %s
        AND previous_close IS NULL;
    """

    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=(commodity_id, interval))

    if df.empty:
        raise ValueError(
            f"No market data found for commodity ID: {commodity_id}")

    return df


# ==================== INDICATOR CALCULATIONS ====================

def calculate_support_resistance(df: pd.DataFrame) -> tuple[float, float, float]:
    """Calculates and returns support, resistance, and pivot levels from price data."""
    resistance = df['day_high'].max()
    support = df['day_low'].min()
    pivot = (resistance + support + df['price'].iloc[-1]) / 3
    return resistance, support, pivot


def calculate_moving_averages(df: pd.DataFrame, n: int) -> tuple[pd.Series, pd.Series, pd.Series, int, int, int]:
    """Calculates adaptive short, mid, and long moving averages based on data size."""
    # Ensure windows don't exceed data length
    ma_short_period = min(max(2, n // 10), n - 1)
    ma_mid_period = min(max(5, n // 5), n - 1)
    ma_long_period = min(max(10, n // 3), n - 1)

    ma_short = df['price'].rolling(
        window=ma_short_period, min_periods=1).mean()
    ma_mid = df['price'].rolling(window=ma_mid_period, min_periods=1).mean()
    ma_long = df['price'].rolling(window=ma_long_period, min_periods=1).mean()

    return ma_short, ma_mid, ma_long, ma_short_period, ma_mid_period, ma_long_period


def calculate_rsi(prices: pd.Series, n: int) -> tuple[pd.Series, int]:
    """Calculates the Relative Strength Index (RSI) with adaptive period."""
    period = min(max(2, n // 6), n - 1)
    delta = prices.diff()

    gain = delta.where(delta > 0, 0).rolling(
        window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)
            ).rolling(window=period, min_periods=1).mean()

    # Avoid division by zero
    rs = gain / loss.replace(0, float('inf'))
    rsi = 100 - (100 / (1 + rs))

    # Handle edge cases where loss is 0 (RSI should be 100)
    rsi = rsi.fillna(50)  # Neutral when undefined

    return rsi, period


def calculate_macd(prices: pd.Series, n: int) -> tuple[pd.Series, pd.Series, pd.Series, int, int, int]:
    """Calculates MACD line, signal line, and histogram with adaptive periods."""
    fast_period = min(max(2, n // 8), n - 1)
    slow_period = min(max(4, n // 4), n - 1)
    signal_period = min(max(2, n // 10), n - 1)

    exp_fast = prices.ewm(span=fast_period, adjust=False, min_periods=1).mean()
    exp_slow = prices.ewm(span=slow_period, adjust=False, min_periods=1).mean()

    macd = exp_fast - exp_slow
    signal = macd.ewm(span=signal_period, adjust=False, min_periods=1).mean()
    histogram = macd - signal

    return macd, signal, histogram, fast_period, slow_period, signal_period


def calculate_all_indicators(df: pd.DataFrame) -> dict:
    """Calculates all technical indicators and returns them in a dictionary."""
    n = len(df)

    resistance, support, pivot = calculate_support_resistance(df)
    ma_short, ma_mid, ma_long, ma_short_p, ma_mid_p, ma_long_p = calculate_moving_averages(
        df, n)
    rsi, rsi_period = calculate_rsi(df['price'], n)
    macd, macd_signal, macd_hist, macd_fast, macd_slow, macd_sig_p = calculate_macd(
        df['price'], n)

    return {
        'resistance': resistance,
        'support': support,
        'pivot': pivot,
        'ma_short': ma_short,
        'ma_mid': ma_mid,
        'ma_long': ma_long,
        'ma_short_period': ma_short_p,
        'ma_mid_period': ma_mid_p,
        'ma_long_period': ma_long_p,
        'rsi': rsi,
        'rsi_period': rsi_period,
        'macd': macd,
        'macd_signal': macd_signal,
        'macd_hist': macd_hist,
    }


# ==================== CHART CREATION ====================

def create_figure() -> go.Figure:
    """Creates the base Plotly figure with subplots for price, RSI, and MACD."""
    return make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=VERTICAL_SPACING,
        row_heights=ROW_HEIGHTS,
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": False}],
            [{"secondary_y": False}]
        ]
    )


def add_candlestick_trace(fig: go.Figure, df: pd.DataFrame) -> None:
    """Adds candlestick chart to the figure."""
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open_price'],
            high=df['day_high'],
            low=df['day_low'],
            close=df['price'],
            name='Price',
            increasing_line_color=COLOR_BULLISH,
            decreasing_line_color=COLOR_BEARISH
        ),
        row=1, col=1, secondary_y=False
    )


def add_volume_trace(fig: go.Figure, df: pd.DataFrame) -> None:
    """Adds volume bars to the figure."""
    vol_colors = [
        COLOR_BULLISH if df['price'].iloc[i] >= df['open_price'].iloc[i] else COLOR_BEARISH
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker_color=vol_colors,
            opacity=0.4
        ),
        row=1, col=1, secondary_y=True
    )


def add_moving_average_traces(fig: go.Figure, df: pd.DataFrame, indicators: dict) -> None:
    """Adds moving average lines to the figure."""
    ma_configs = [
        ('ma_short', 'ma_short_period', COLOR_MA_SHORT),
        ('ma_mid', 'ma_mid_period', COLOR_MA_MID),
        ('ma_long', 'ma_long_period', COLOR_MA_LONG),
    ]

    for ma_key, period_key, color in ma_configs:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=indicators[ma_key],
                mode='lines',
                name=f'MA {indicators[period_key]}',
                line=dict(color=color, width=2),
                visible='legendonly'
            ),
            row=1, col=1, secondary_y=False
        )


def add_support_resistance_traces(fig: go.Figure, df: pd.DataFrame, indicators: dict) -> None:
    """Adds support, resistance, and pivot lines to the figure."""
    lines = [
        ('resistance', COLOR_RESISTANCE, 'dash', 2, 'Resistance'),
        ('support', COLOR_SUPPORT, 'dash', 2, 'Support'),
        ('pivot', COLOR_PIVOT, 'dot', 1.5, 'Pivot'),
    ]

    for key, color, dash, width, name in lines:
        fig.add_trace(
            go.Scatter(
                x=[df.index.min(), df.index.max()],
                y=[indicators[key], indicators[key]],
                mode='lines',
                name=name,
                line=dict(color=color, width=width, dash=dash),
                visible='legendonly'
            ),
            row=1, col=1, secondary_y=False
        )


def add_rsi_trace(fig: go.Figure, df: pd.DataFrame, indicators: dict) -> None:
    """Adds RSI indicator to the figure."""
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=indicators['rsi'],
            mode='lines',
            name=f'RSI ({indicators["rsi_period"]})',
            line=dict(color=COLOR_RSI, width=2)
        ),
        row=2, col=1
    )

    # RSI threshold lines
    fig.add_hline(y=RSI_OVERBOUGHT, line_dash="dash",
                  line_color=COLOR_RESISTANCE, opacity=0.5, row=2, col=1)
    fig.add_hline(y=RSI_OVERSOLD, line_dash="dash",
                  line_color=COLOR_SUPPORT, opacity=0.5, row=2, col=1)
    fig.add_hline(y=RSI_NEUTRAL, line_dash="dot",
                  line_color="gray", opacity=0.3, row=2, col=1)


def add_macd_traces(fig: go.Figure, df: pd.DataFrame, indicators: dict) -> None:
    """Adds MACD indicator to the figure."""
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=indicators['macd'],
            mode='lines',
            name='MACD',
            line=dict(color=COLOR_MACD, width=2)
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=indicators['macd_signal'],
            mode='lines',
            name='Signal',
            line=dict(color=COLOR_SIGNAL, width=2)
        ),
        row=3, col=1
    )

    # MACD histogram
    macd_colors = [COLOR_BULLISH if v >=
                   0 else COLOR_BEARISH for v in indicators['macd_hist']]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=indicators['macd_hist'],
            name='MACD Hist',
            marker_color=macd_colors,
            opacity=0.6
        ),
        row=3, col=1
    )

    fig.add_hline(y=0, line_dash="solid", line_color="gray",
                  opacity=0.5, row=3, col=1)


def add_annotations(fig: go.Figure, indicators: dict) -> None:
    """Adds price level annotations to the figure."""
    annotations = [
        (indicators['resistance'], 'R',
         'rgba(255,0,0,0.8)', COLOR_RESISTANCE, 'white'),
        (indicators['support'], 'S',
         'rgba(0,128,0,0.8)', COLOR_SUPPORT, 'white'),
        (indicators['pivot'], 'P',
         'rgba(255,255,0,0.9)', COLOR_PIVOT, 'black'),
    ]

    for value, label, bgcolor, bordercolor, fontcolor in annotations:
        fig.add_annotation(
            x=0.01, xref='paper',
            y=value, yref='y',
            text=f" {label}: ${value:.2f} ",
            showarrow=False,
            xanchor='left',
            yanchor='middle',
            font=dict(color=fontcolor, size=11, family='Arial Black'),
            bgcolor=bgcolor,
            bordercolor=bordercolor,
            borderwidth=1,
            borderpad=2
        )


def configure_layout(fig: go.Figure, df: pd.DataFrame, interval: str) -> None:
    """Configures the figure layout and styling."""
    commodity_name = df['commodity_name'].iloc[0]
    symbol = df['symbol'].iloc[0]

    fig.update_layout(
        title={
            'text': f"📊 {commodity_name} ({symbol}) - {interval}",
            'x': 0.5,
            'font': {'size': 20, 'color': '#FFD700'}
        },
        xaxis3_title='Date',
        xaxis_rangeslider_visible=False,
        height=CHART_HEIGHT,
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
    fig.update_yaxes(
        title_text="Volume",
        row=1, col=1,
        secondary_y=True,
        range=[0, df['volume'].max() * 4]
    )
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
    fig.update_xaxes(
        showspikes=True, spikemode='across', spikesnap='cursor',
        spikedash='solid', spikecolor=COLOR_CROSSHAIR, spikethickness=1
    )
    fig.update_yaxes(
        showspikes=True, spikemode='across', spikesnap='cursor',
        spikedash='solid', spikecolor=COLOR_CROSSHAIR, spikethickness=1
    )


def get_chart_config() -> dict:
    """Returns the Plotly chart configuration."""
    return {
        'scrollZoom': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
    }


# ==================== MAIN FUNCTION ====================

def adv_graph(
    commodity_id: Optional[int] = None,
    interval: str = '1 month',
    show_chart: bool = False
) -> Optional[go.Figure]:
    """Creates an advanced technical analysis graph with RSI, MACD, and moving averages."""
    # Get commodity ID from parameter or session state
    if commodity_id is None:
        commodity_id = st.session_state.get('analysis_commodity_id')
        if commodity_id is None:
            st.error("No commodity selected for analysis.")
            return None

    try:
        # Fetch and prepare data
        df = fetch_market_data(commodity_id, interval)

        if len(df) < MIN_DATA_POINTS:
            st.warning(
                f"Insufficient data points ({len(df)}). Need at least {MIN_DATA_POINTS}.")
            return None

        df_chart = df.copy()
        df_chart = df_chart.sort_values('recorded_at')
        df_chart.set_index('recorded_at', inplace=True)

        # Calculate indicators
        indicators = calculate_all_indicators(df_chart)

        # Create figure
        fig = create_figure()

        # Add all traces
        add_candlestick_trace(fig, df_chart)
        add_volume_trace(fig, df_chart)
        add_moving_average_traces(fig, df_chart, indicators)
        add_support_resistance_traces(fig, df_chart, indicators)
        add_rsi_trace(fig, df_chart, indicators)
        add_macd_traces(fig, df_chart, indicators)
        add_annotations(fig, indicators)

        # Configure layout
        configure_layout(fig, df_chart, interval)

        if show_chart:
            fig.show(config=get_chart_config())
            return None

        return fig

    except ConnectionError as e:
        st.error(f"Database connection error: {e}")
        return None
    except ValueError as e:
        st.error(str(e))
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None
