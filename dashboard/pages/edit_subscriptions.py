"""Page for editing user subscriptions."""

# pylint: disable=import-error

import streamlit as st
# import pandas as pd

from menu import menu_with_redirect
from dashboard_items import (display_markdown_title,
                             build_single_commodity_edit)

st.set_page_config(
    layout="wide"
)


def build_commodity_titles():
    """Build commodity title row."""
    col1, col2, col3, col4, col5, col6 = st.columns(
        [2, 2, 2, 2, 3, 3],
        vertical_alignment="center")

    with col1:
        display_markdown_title("Commodity", alignment="left")

    with col2:
        display_markdown_title("Tracked")

    with col3:
        display_markdown_title("Buy Alerts")

    with col4:
        display_markdown_title("Sell Alerts")

    with col5:
        display_markdown_title("Buy Price")

    with col6:
        display_markdown_title("Sell Price")


def build_subscription_table():
    """Build subscription table."""

    build_commodity_titles()

    commodities = [
        {"id": 1, "name": "Gold"},
        {"id": 2, "name": "Silver"},
        {"id": 3, "name": "Crude Oil"},
        {"id": 4, "name": "Natural Gas"},
        {"id": 5, "name": "Copper"},
    ]

    commodity_data = {}

    for comm in commodities:
        commodity_data[comm["id"]] = build_single_commodity_edit(comm)


if __name__ == "__main__":

    menu_with_redirect()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    st.header("Edit Subscriptions", text_alignment="center")

    with st.container(border=True,
                      horizontal_alignment="center",
                      ):
        build_subscription_table()
