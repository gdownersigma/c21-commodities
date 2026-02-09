"""Page for commodity pivot point analysis."""

# pylint: disable=import-error
import streamlit as st

from menu import menu_with_redirect
from adv_analysis.adv_graph import adv_graph

st.set_page_config(
    layout="wide"
)

st.session_state.last_page = "analysis"

if __name__ == "__main__":

    menu_with_redirect()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("images/pivot_point.png", width='stretch')

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    fig = adv_graph(st.session_state.analysis_commodity_id)
    if fig:
        st.plotly_chart(fig, width='stretch')
