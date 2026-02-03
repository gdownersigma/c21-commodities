"""File to hold functions to create items in the dashboard."""

import streamlit as st
import pandas as pd


def add_commodity_selector(commodity_options: list, i: int):
    """Add dynamic commodity selector to the sidebar."""

    st.session_state.selected_commodities[f"commodity_{i}"] = st.sidebar.selectbox(
        label=f"Select Commodity {i + 1}",
        options=commodity_options,
        format_func=lambda x: x[1],
        key=f"commodity_select_{i}"
    )


def build_commodity_data(df: pd.DataFrame):
    """Build a design for each commodity's data display."""

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("Display graph here...")

    with col2:
        st.write("Display statistics here...")

    st.divider()
