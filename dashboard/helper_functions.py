"""File to hold helper functions for the dashboard."""

import streamlit as st
import pandas as pd


def add_commodity():
    """Add a new commodity slot."""
    st.session_state.num_commodities += 1


def remove_commodity():
    """Remove the last commodity slot."""
    if st.session_state.num_commodities > 1:
        st.session_state.num_commodities -= 1

        key = f"commodity_{st.session_state.num_commodities}"
        if key in st.session_state.selected_commodities:
            del st.session_state.selected_commodities[key]


def authenticate_field(field_input: str) -> bool:
    """Return True if the field is populated."""

    return field_input and field_input.strip() != ""


def authenticate_user(user: dict) -> bool:
    """Return True if all user fields are populated."""

    for value in user.values():
        if not authenticate_field(value):
            return False
    return True
