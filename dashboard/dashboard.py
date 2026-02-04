"""Dashboard to display Commodity Prices and Trends."""

from os import environ as ENV
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from menu import menu
from helper_functions import (add_commodity,
                              remove_commodity)
from dashboard_items import (add_commodity_selector,
                             build_commodity_data)
from query_data import (get_connection,
                        get_commodity_data_by_ids)

st.set_page_config(
    layout="wide"
)

if "user" not in st.session_state:
    st.session_state.user = {}

if "num_commodities" not in st.session_state:
    st.session_state.num_commodities = 1

if "selected_commodities" not in st.session_state:
    st.session_state.selected_commodities = {}

if "subscribed_commodities" not in st.session_state:
    st.session_state.subscribed_commodities = [10, 18, 40]


def build_sidebar(df: pd.DataFrame):
    """Build the sidebar with filters."""

    if st.session_state.user:
        if st.sidebar.button("Log out",
                             key="logout_btn"):
            st.session_state.user = {}
            st.session_state.subscribed_commodities = [10, 18, 40]
            st.session_state.selected_commodities = {}
            st.session_state.num_commodities = 1
            st.rerun()

    st.sidebar.divider()

    st.sidebar.header("Filters")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
                                   key="start_date_input")
    with col2:
        end_date = st.date_input("End Date",
                                 key="end_date_input")

    st.sidebar.divider()

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

    return start_date, end_date


def display_key_metrics(df: pd.DataFrame):
    """Display key metrics in the dashboard."""

    st.header("Key Metrics")

    with st.container(horizontal=True):
        st.metric(label="No. Subscribed Commodities",
                        value=len(st.session_state.subscribed_commodities))
        st.metric(label="Average Price Change (%)",
                        value=1.5)

        st.metric("My metric", 42, 2)


def display_combined_graph(df: pd.DataFrame):
    """Display combined graph of selected commodities."""
    st.subheader("Price Trends")
    build_commodity_data(df)


def display_individual_graphs(df: pd.DataFrame):
    """Display individual graphs for each selected commodity."""

    for i in range(st.session_state.num_commodities):
        comm_id = st.session_state.selected_commodities[f"commodity_{i}"][0]
        filtered_df = df[df["commodity_id"] == comm_id]

        st.subheader(f"{filtered_df['commodity_name'].iloc[0]}")
        build_commodity_data(filtered_df)


if __name__ == "__main__":

    load_dotenv()

    conn = get_connection(ENV)

    df = get_commodity_data_by_ids(
        conn,
        st.session_state.subscribed_commodities
    )

    conn.close()

    menu()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    start_date, end_date = build_sidebar(df)

    display_key_metrics(df)

    if st.session_state.num_commodities > 1:
        display_combined_graph(df)

    display_individual_graphs(df)
