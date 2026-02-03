"""Dashboard to display Commodity Prices and Trends."""

from os import environ as ENV
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from menu import menu
from helper_functions import (add_commodity,
                              remove_commodity)
from dashboard_items import (add_commodity_selector)

st.set_page_config(
    layout="wide"
)

if "current_user" not in st.session_state:
    st.session_state.current_user = {}

# current_user["user_id"]
# current_user["user_name"]
# current_user["email"]
# current_user["hashed_password"]

if "num_commodities" not in st.session_state:
    st.session_state.num_commodities = 1

if "selected_commodities" not in st.session_state:
    st.session_state.selected_commodities = {}


def build_sidebar(df: pd.DataFrame):
    """Build the sidebar with filters."""

    # Add log out button
    if st.session_state.current_user:
        if st.sidebar.button("Log out",
                             key="logout_btn"):
            st.session_state.current_user = {}
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

    commodity_options = df[["commodity_id",
                            "commodity_name"]].drop_duplicates().values.tolist()

    for i in range(st.session_state.num_commodities):
        add_commodity_selector(commodity_options, i)

    st.sidebar.divider()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.button("➕ Add",
                  on_click=add_commodity,
                  disabled=(st.session_state.num_commodities >= 5),
                  use_container_width=True,
                  key="add_commodity_btn")
    with col2:
        st.button("➖ Remove",
                  on_click=remove_commodity,
                  disabled=(st.session_state.num_commodities <= 1),
                  use_container_width=True,
                  key="remove_commodity_btn")

    return start_date, end_date


if __name__ == "__main__":

    menu()

    st.title(body="Website Title",
             text_alignment="center")

    df = pd.DataFrame({
        "commodity_id": [1, 2, 3, 4, 5],
        "commodity_name": ["Gold", "Silver", "Copper", "Oil", "Natural Gas"],
        "buy_price": [2050.25, 28.45, 4.12, 85.30, 3.25],
        "sell_price": [2055.75, 29.10, 4.18, 86.50, 3.35]
    })

    start_date, end_date = build_sidebar(df)

    st.session_state.selected_commodities
