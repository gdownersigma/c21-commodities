"""Dashboard to display Commodity Prices and Trends."""

from os import environ as ENV
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from menu import menu
from helper_functions import (add_commodity,
                              remove_commodity)
from dashboard_items import (add_commodity_selector,
                             build_single_commodity_graph,
                             build_combined_graph,
                             logout_button)
from query_data import (get_connection,
                        get_commodity_data_by_ids,
                        get_market_data_by_ids)

st.set_page_config(
    layout="wide"
)

if "user" not in st.session_state:
    st.session_state.user = {}

if "num_commodities" not in st.session_state:
    st.session_state.num_commodities = 3

if "selected_commodities" not in st.session_state:
    st.session_state.selected_commodities = {
        "commodity_0": [10, "Brent Crude Oil"],
        "commodity_1": [18, "Gold Futures"],
        "commodity_2": [40, "Silver Futures"]
    }

if "subscribed_commodities" not in st.session_state:
    st.session_state.subscribed_commodities = [10, 18, 40]

if "user_commodities" not in st.session_state:
    st.session_state.user_commodities = {}


def build_sidebar(df: pd.DataFrame):
    """Build the sidebar with filters."""

    if st.session_state.user:
        logout_button()

    if st.session_state.user:
        st.sidebar.header("Select Commodities")

        commodity_options = df[["commodity_id",
                                "commodity_name"]].drop_duplicates().values.tolist()

        for i in range(st.session_state.num_commodities):
            add_commodity_selector(commodity_options, i)

        st.sidebar.divider()

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.button("➕ Add",
                      on_click=add_commodity,
                      disabled=(st.session_state.num_commodities >= min(
                          len(st.session_state.subscribed_commodities), 10)
                      ),
                      use_container_width=True,
                      key="add_commodity_btn")
        with col2:
            st.button("➖ Remove",
                      on_click=remove_commodity,
                      disabled=(st.session_state.num_commodities <= 1),
                      use_container_width=True,
                      key="remove_commodity_btn")


def display_key_metrics(df: pd.DataFrame, conn):
    """Display key metrics in the dashboard."""

    # Get market data to calculate average change
    commodity_ids = df["commodity_id"].unique().tolist()
    market_df = get_market_data_by_ids(conn, commodity_ids)

    # Calculate average change percentage across subscribed commodities
    if not market_df.empty:
        # Get the latest record for each commodity
        latest_per_commodity = market_df.sort_values(
            'recorded_at').groupby('commodity_id').last()
        avg_change = latest_per_commodity['change_percentage'].mean()
    else:
        avg_change = 0.0

    # Determine color and icon based on positive/negative change
    if avg_change >= 0:
        change_color = "#22c55e"
        arrow = "▲"
    else:
        change_color = "#ef4444"
        arrow = "▼"

    num_commodities = len(st.session_state.subscribed_commodities)

    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="margin-bottom: 30px; color: #1e293b;">Key Metrics</h2>
            <div style="display: flex; justify-content: center; gap: 60px;">
                <div style="background: linear-gradient(135deg, #ff801d15 0%, #ff801d30 100%);
                            border: 2px solid #ff801d;
                            border-radius: 15px;
                            padding: 25px 40px;
                            min-width: 200px;">
                    <p style="color: #64748b; font-size: 14px; margin: 0 0 8px 0;">Subscribed Commodities</p>
                    <p style="color: #ff801d; font-size: 42px; font-weight: 700; margin: 0;">{num_commodities}</p>
                </div>
                <div style="background: linear-gradient(135deg, {change_color}15 0%, {change_color}30 100%);
                            border: 2px solid {change_color};
                            border-radius: 15px;
                            padding: 25px 40px;
                            min-width: 200px;">
                    <p style="color: #64748b; font-size: 14px; margin: 0 0 8px 0;">Average Price Change</p>
                    <p style="color: {change_color}; font-size: 42px; font-weight: 700; margin: 0;">
                        {arrow} {'+' if avg_change >= 0 else ''}{avg_change:.2f}%
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def display_combined_graph(df: pd.DataFrame, conn):
    """Display combined graph of selected commodities."""
    st.subheader("Price Trends")
    commodity_ids = df["commodity_id"].unique().tolist()
    market_df = get_market_data_by_ids(conn, commodity_ids)
    build_combined_graph(df, market_df)


def display_individual_graphs(df: pd.DataFrame, conn):
    """Display individual graphs for each selected commodity."""

    for i in range(st.session_state.num_commodities):
        comm_id = st.session_state.selected_commodities[f"commodity_{i}"][0]
        filtered_df = df[df["commodity_id"] == comm_id]
        market_df = get_market_data_by_ids(conn, [comm_id])

        st.subheader(f"{filtered_df['commodity_name'].iloc[0]}")
        build_single_commodity_graph(filtered_df, market_df, graph_index=i)


if __name__ == "__main__":

    load_dotenv()

    conn = get_connection(ENV)

    df = get_commodity_data_by_ids(
        conn,
        st.session_state.subscribed_commodities
    )

    menu()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    build_sidebar(df)

    if st.session_state.user:
        display_key_metrics(df, conn)

        if st.session_state.num_commodities > 1:
            display_combined_graph(df, conn)

    display_individual_graphs(df, conn)

    conn.close()
