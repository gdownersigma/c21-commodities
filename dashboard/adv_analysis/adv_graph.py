"""Advanced Technical Analysis Graph Module for Commodity Data."""

import streamlit as st
import pandas as pd
from psycopg2 import connect
from os import environ as ENV
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from contextlib import contextmanager


# ==================== CONSTANTS ====================

COLOR_BULLISH = '#26a69a'
COLOR_BEARISH = '#ef5350'
COLOR_MA_7 = '#FFA500'
COLOR_MA_14 = '#00CED1'
COLOR_MA_20 = '#FF69B4'


# ==================== DATABASE FUNCTIONS ====================

@contextmanager
def get_db_connection():
    """Yields a PostgreSQL database connection and ensures cleanup."""
    load_dotenv()
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    try:
        yield conn
    finally:
        conn.close()


@st.cache_data(ttl=300)
def fetch_data(commodity_id: int) -> pd.DataFrame:
    """Fetches market data for a commodity using parameterized queries."""
    query = """
        SELECT * FROM market_records
        JOIN commodities AS c
        USING (commodity_id)
        WHERE commodity_id = %s
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=(commodity_id,))
    return df


# ==================== DATA PROCESSING ====================

def prepare_daily_data(df: pd.DataFrame) -> pd.DataFrame:
    """Resamples data to daily OHLC candles and calculates moving averages."""
    df_chart = df.copy()
    df_chart = df_chart.sort_values('recorded_at', ascending=True)

    df_daily = df_chart.resample('D', on='recorded_at').agg({
        'open_price': 'first',
        'day_high': 'max',
        'day_low': 'min',
        'price': 'last',
        'volume': 'last',
        'commodity_name': 'first',
        'symbol': 'first'
    }).dropna()

    return df_daily


def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates 7, 14, and 20 day moving averages."""
    df['MA_7'] = df['price'].rolling(window=7).mean()
    df['MA_14'] = df['price'].rolling(window=14).mean()
    df['MA_20'] = df['price'].rolling(window=20).mean()
    return df


def get_price_metrics(df: pd.DataFrame) -> dict:
    """Calculates price metrics for display."""
    latest_price = df['price'].iloc[-1]
    prev_price = df['price'].iloc[-2] if len(df) > 1 else latest_price
    price_change = latest_price - prev_price
    price_change_pct = (price_change / prev_price) * \
        100 if prev_price != 0 else 0

    return {
        'latest_price': latest_price,
        'price_change_pct': price_change_pct,
        'day_high': df['day_high'].iloc[-1],
        'day_low': df['day_low'].iloc[-1],
        'volume': df['volume'].iloc[-1]
    }


# ==================== CHART BUILDING ====================

def create_figure(show_volume: bool) -> go.Figure:
    """Creates the base Plotly figure with subplots."""
    row_heights = [0.7, 0.3] if show_volume else [1.0]
    rows = 2 if show_volume else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=('Price', 'Volume') if show_volume else ('Price',)
    )
    return fig


def add_candlestick_trace(fig: go.Figure, df: pd.DataFrame) -> None:
    """Adds candlestick chart to the figure."""
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open_price'],
            high=df['day_high'],
            low=df['day_low'],
            close=df['price'],
            increasing_line_color=COLOR_BULLISH,
            decreasing_line_color=COLOR_BEARISH,
            name='Price'
        ),
        row=1, col=1
    )


def add_moving_average_traces(fig: go.Figure, df: pd.DataFrame) -> None:
    """Adds moving average lines to the figure."""
    ma_configs = [
        ('MA_7', 'MA 7', COLOR_MA_7),
        ('MA_14', 'MA 14', COLOR_MA_14),
        ('MA_20', 'MA 20', COLOR_MA_20),
    ]

    for col, name, color in ma_configs:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode='lines',
                name=name,
                line=dict(color=color, width=1.5)
            ),
            row=1, col=1
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
            marker_color=vol_colors,
            name='Volume',
            showlegend=False
        ),
        row=2, col=1
    )
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)


def configure_layout(fig: go.Figure) -> None:
    """Configures the figure layout and styling."""
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


# ==================== UI COMPONENTS ====================

def render_sidebar() -> dict:
    """Renders sidebar controls and returns user selections."""
    st.sidebar.header("Chart Settings")
    return {
        'show_volume': st.sidebar.checkbox("Show Volume", value=True)
    }


def render_title(df: pd.DataFrame) -> None:
    """Renders the page title with commodity name and symbol."""
    commodity_name = df['commodity_name'].iloc[0] if 'commodity_name' in df.columns else "Commodity"
    symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else ""
    st.title(f"📈 {commodity_name} ({symbol}) - Daily Chart")


def render_metrics(metrics: dict) -> None:
    """Renders the price metrics in columns."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Price", f"${metrics['latest_price']:.2f}",
                f"{metrics['price_change_pct']:+.2f}%")
    col2.metric("Day High", f"${metrics['day_high']:.2f}")
    col3.metric("Day Low", f"${metrics['day_low']:.2f}")
    col4.metric("Volume", f"{metrics['volume']:,.0f}")


# ==================== MAIN FUNCTIONS ====================

def build_chart(df: pd.DataFrame, settings: dict) -> go.Figure:
    """Builds the complete chart with all traces and configuration."""
    fig = create_figure(settings['show_volume'])
    add_candlestick_trace(fig, df)
    add_moving_average_traces(fig, df)
    if settings['show_volume']:
        add_volume_trace(fig, df)
    configure_layout(fig)
    return fig


def adv_graph(commodity_id: int = None) -> go.Figure:
    """Creates an advanced technical analysis graph for a commodity."""
    if commodity_id is None:
        commodity_id = st.session_state.get('analysis_commodity_id')
        if commodity_id is None:
            st.error("No commodity selected for analysis.")
            return None

    df = fetch_data(commodity_id)
    if df.empty:
        st.error("No data found for the selected commodity.")
        return None

    df_daily = prepare_daily_data(df)
    df_daily = calculate_moving_averages(df_daily)

    settings = render_sidebar()
    render_title(df_daily)

    fig = build_chart(df_daily, settings)
    st.plotly_chart(fig, use_container_width=True)

    metrics = get_price_metrics(df_daily)
    render_metrics(metrics)

    return fig


def main() -> None:
    """Entry point for running the chart as a standalone Streamlit page."""
    st.set_page_config(page_title="Commodity Chart", layout="wide")
    adv_graph()


if __name__ == "__main__":
    main()
