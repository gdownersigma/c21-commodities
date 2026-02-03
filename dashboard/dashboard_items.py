"""File to hold functions to create items in the dashboard."""

import streamlit as st
import pandas as pd

from helper_functions import (authenticate_user)


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


def build_form(field_labels: dict, form_name: str, form_key: str):
    """"""

    with st.form(key=form_key):

        st.header(body=form_name,
                  text_alignment="center")

        st.divider()

        field_input = {}
        for label, input_type in field_labels.items():
            field_input[label] = st.text_input(label.capitalize(),
                                               type=input_type,
                                               key=label)

        submitted = st.form_submit_button(form_name)

        if submitted:
            if authenticate_user(field_input):
                st.success("Success!")

                # Need to use the database details, not field_input
                st.session_state.current_user = field_input
                st.switch_page("dashboard.py")
            else:
                st.error("Please fill in all fields correctly.")


def account_entry_redirect(msg: str, page: str):
    """"""

    with st.container(horizontal_alignment="center"):
        if st.button(msg):
            st.switch_page(page)
