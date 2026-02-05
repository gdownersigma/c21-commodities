"""Page for editing user details."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st

from menu import menu
from query_data import get_connection
from dashboard_items import build_form

st.set_page_config(
    layout="centered"
)


def handle_edit_account(conn, field_input):
    """Handle edit account logic."""

    # Check if any details have changed
    # If not, throw error message
    # If yes, either:
    # Update all details regardless of change
    # Or update only changed details

    if False:  # Placeholder for change detection logic
        st.error(
            "No details have been changed. Please update at least one field to save changes.")
    else:

        st.switch_page("pages/account_settings.py")


def handle_cancel():
    """Handle cancel button logic."""

    st.switch_page("pages/account_settings.py")


if __name__ == "__main__":

    menu()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    st.header("Edit Account", text_alignment="center")

    conn = get_connection(ENV)

    build_form(
        conn=conn,
        field_labels={
            "name": "default",
            "email": "default",
            "password": "password",
        },
        field_values={
            "name": st.session_state.user["user_name"],
            "email": st.session_state.user["email"],
        },
        form_name="Edit Account",
        form_key="edit_account_form",
        cancel_name="Back",
        on_submit=handle_edit_account,
        on_cancel=handle_cancel
    )

    conn.close()
