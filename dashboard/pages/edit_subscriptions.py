"""Page for editing user subscriptions."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st
import pandas as pd

from menu import menu_with_redirect
from dashboard_items import (display_markdown_title,
                             build_single_commodity_edit,
                             page_redirect)
from query_data import (get_connection,
                        create_commodity_connections,
                        delete_user_commodities,
                        update_user_commodities,
                        get_commodities_with_user_subscriptions)

st.set_page_config(
    layout="wide"
)


def build_commodity_titles():
    """Build commodity title row."""
    col1, col2, col3, col4, col5, col6 = st.columns(
        [3, 2, 2, 2, 3, 3],
        vertical_alignment="center")

    with col1:
        display_markdown_title("Commodity", alignment="left")

    with col2:
        display_markdown_title("Track")

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

    comm_data = {}

    for comm_id, orig_data in st.session_state.user_commodities.items():
        comm_data[comm_id] = build_single_commodity_edit({
            "id": comm_id,
            **orig_data
        })

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        with st.container(horizontal_alignment="center"):
            if st.button("Submit"):
                handle_submit(comm_data)
    with col2:
        page_redirect("Cancel",
                      "dashboard.py")


def handle_submit(new_comm):
    """Handle form submission."""

    orig_comm = st.session_state.user_commodities

    create_subscriptions = []
    delete_subscriptions = []
    update_subscriptions = []

    for comm_id, data in new_comm.items():
        orig = orig_comm[comm_id]

        if not data["buy"] and data["buy_price"] != 0.0:
            data["buy_price"] = 0.0

        if not data["sell"] and data["sell_price"] != 0.0:
            data["sell_price"] = 0.0

        if data["track"] and not orig["track"]:
            create_subscriptions.append({
                "user_id": st.session_state.user["user_id"],
                "commodity_id": comm_id,
                "buy_price": data["buy_price"],
                "sell_price": data["sell_price"]
            })

        elif not data["track"] and orig["track"]:
            delete_subscriptions.append(comm_id)

        elif data["track"] and orig["track"]:
            update = {}

            if data["buy_price"] != orig["buy_price"]:
                update["buy_price"] = data["buy_price"]

            if data["sell_price"] != orig["sell_price"]:
                update["sell_price"] = data["sell_price"]

            if update:
                update["user_id"] = st.session_state.user["user_id"]
                update["commodity_id"] = comm_id
                update_subscriptions.append(update)

    if not create_subscriptions and not delete_subscriptions and not update_subscriptions:
        st.error("No changes made.")
    else:
        conn = get_connection(ENV)
        
        if create_subscriptions:
            create_commodity_connections(conn, create_subscriptions)
        
        if delete_subscriptions:
            delete_user_commodities(conn, st.session_state.user["user_id"], delete_subscriptions)
        
        if update_subscriptions:
            update_user_commodities(conn, update_subscriptions)

        conn.close()

        get_commodities_with_user_subscriptions.clear()

        st.success("Subscriptions updated successfully!")
        st.session_state.user_commodities = new_comm

        st.session_state.subscribed_commodities = [
            comm_id for comm_id, data in new_comm.items() if data["track"]]
        
        st.switch_page("dashboard.py")


if __name__ == "__main__":

    menu_with_redirect()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    st.header("Edit Subscriptions", text_alignment="center")

    with st.container(border=True,
                      horizontal_alignment="center"):
        build_subscription_table()
