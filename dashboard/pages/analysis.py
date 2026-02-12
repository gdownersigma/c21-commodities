"""Page for commodity pivot point analysis."""

# pylint: disable=import-error

import streamlit as st

from menu import menu_with_redirect
from dashboard_items import (display_title,
                             logout_button)
from adv_analysis.adv_graph import adv_graph

st.set_page_config(
    layout="wide"
)

st.session_state.last_page = "analysis"

if __name__ == "__main__":

    menu_with_redirect()
    logout_button()

    display_title()

    adv_graph(st.session_state.analysis_commodity_id)
