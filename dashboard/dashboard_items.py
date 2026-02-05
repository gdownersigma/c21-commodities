"""File to hold functions to create items in the dashboard."""

import streamlit as st
import pandas as pd
from psycopg2.extensions import connection

from helper_functions import (clean_input,
                              authenticate_user_input)


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


def build_form(conn: connection,
               field_labels: dict,
               form_name: str,
               form_key: str,
               cancel_name: str,
               on_submit,
               on_cancel,
               field_values: dict = None):
    """Build a form for log in and sign up pages."""

    with st.form(key=form_key):

        # st.header(body=form_name,
        #           text_alignment="center")

        # st.divider()

        field_input = {}
        for label, input_type in field_labels.items():
            field_input[label] = st.text_input(label.capitalize(),
                                               value=field_values.get(
                                                   label, "") if field_values else "",
                                               type=input_type,
                                               key=label)

        col1, col2 = st.columns(2)
        with col1:
            with st.container(horizontal_alignment="center"):
                submitted = st.form_submit_button(form_name)
        with col2:
            with st.container(horizontal_alignment="center"):
                cancelled = st.form_submit_button(cancel_name)

        if submitted:
            field_input = clean_input(field_input)

            if not authenticate_user_input(field_input):
                st.error("Please fill in all fields correctly.")
            elif on_submit:
                on_submit(conn, field_input)

        if cancelled:
            on_cancel()


def page_redirect(msg: str, page: str, alignment: str = "center"):
    """Create a redirect button for account entry pages."""

    with st.container(horizontal_alignment=alignment):
        if st.button(msg):
            st.switch_page(page)


def display_markdown_title(title: str, alignment: str = "center", size: int = 21, weight: int = 600):
    """Display page title."""
    st.markdown(f"""
            <div style='text-align: {alignment}; font-size: {size}px; font-weight: {weight};'>
                {title}
            </div>
        """, unsafe_allow_html=True)


def build_single_commodity_edit(comm: dict) -> dict:
    """Build display for a single commodity."""

    col1, col2, col3, col4, col5, col6 = st.columns(
        [3, 2, 2, 2, 3, 3],
        vertical_alignment="center")

    commodity_data = {"name": comm["name"]}

    with col1:
        display_markdown_title(
            comm['name'], alignment="left", size=18, weight=600)

    with col2:
        with st.container(horizontal_alignment="center"):
            commodity_data["track"] = st.checkbox(
                "Track",
                value=comm.get("track", False),
                key=f"track_{comm["id"]}")

    with col3:
        with st.container(horizontal_alignment="center"):
            commodity_data["buy"] = st.checkbox(
                "Buy",
                value=comm["buy"],
                key=f"buy_{comm["id"]}_alert",
                disabled=not commodity_data["track"])

    with col4:
        with st.container(horizontal_alignment="center"):
            commodity_data["sell"] = st.checkbox(
                "Sell",
                value=comm["sell"],
                key=f"sell_{comm["id"]}_alert",
                disabled=not commodity_data["track"])

    with col5:
        with st.container(horizontal_alignment="center"):
            commodity_data["buy_price"] = st.number_input(
                "Buy Price",
                value=comm["buy_price"],
                min_value=0.0,
                max_value=1000000.0,
                step=0.01,
                format="%.2f",
                key=f"buy_price_{comm["id"]}",
                disabled=not commodity_data["buy"])

    with col6:
        with st.container(horizontal_alignment="center"):
            commodity_data["sell_price"] = st.number_input(
                "Sell Price",
                value=float(comm["sell_price"]),
                min_value=0.0,
                max_value=1000000.0,
                step=0.01,
                format="%.2f",
                key=f"sell_price_{comm["id"]}",
                disabled=not commodity_data["sell"])

    return commodity_data
