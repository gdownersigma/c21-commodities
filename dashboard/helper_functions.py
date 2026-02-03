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
