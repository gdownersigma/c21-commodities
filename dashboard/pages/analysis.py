"""Page for user log in."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st

from menu import menu
from adv_analysis.adv_graph import adv_graph

st.set_page_config(
    layout="centered"
)

st.session_state.last_page = "analysis"

if __name__ == "__main__":

    menu()

    commodity_id = st.session_state.get("analysis_commodity_id", 18)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("images/pivot_point.png", use_container_width=True)

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    fig = adv_graph(commodity_id)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
