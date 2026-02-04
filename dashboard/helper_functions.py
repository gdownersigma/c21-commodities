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


def clean_input(field_input: dict) -> dict:
    """Return clean input without leading or trailing spaces."""

    for key, val in field_input.items():
        if field_input is not None and field_input != "":
            field_input[key] = val.strip()

    return field_input


def authenticate_field(field_input: str) -> bool:
    """Return True if the field is populated."""
    
    return not (field_input is None or field_input == "")


def authenticate_user_input(user: dict) -> bool:
    """Return True if all user fields are populated."""

    for value in user.values():
        if not authenticate_field(value):
            return False
    return True
