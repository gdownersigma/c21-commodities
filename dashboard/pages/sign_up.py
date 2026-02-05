"""Page for user sign up."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st
from bcrypt import hashpw, gensalt

from menu import menu
from query_data import get_connection
from dashboard_items import (build_form,
                             page_redirect)
from helper_functions import fill_user_commodities
from query_data import (get_user_count_by_email,
                        create_user,
                        create_commodity_connections)

st.set_page_config(
    layout="centered"
)


def handle_signup(conn, field_input):
    """Handle signup logic."""
    user_count = get_user_count_by_email(
        conn, field_input["email"])

    if user_count != 0:
        st.error("An account with this email already exists. Please log in.")
    else:
        field_input["hashed_password"] = hashpw(
            field_input["password"].encode('utf-8'), gensalt())
        field_input["hashed_password"] = field_input["password"]

        user_id = create_user(conn, field_input)

        user = {
            "user_id": user_id,
            "user_name": field_input["name"],
            "email": field_input["email"]
        }

        st.success(f"Welcome, {user['user_name']}!")

        comm_data = []

        for comm_id in [10, 18, 40]:
            comm_data.append({
                "user_id": user_id,
                "commodity_id": comm_id,
                "buy_price": 0.0,
                "sell_price": 0.0
            })

        create_commodity_connections(
            conn,
            comm_data
        )

        fill_user_commodities(conn, user_id)

        st.session_state.user = user
        st.session_state.num_commodities = 1
        st.session_state.selected_commodities = {}
        st.switch_page("dashboard.py")


def handle_cancel():
    """Handle cancel button logic."""

    st.switch_page("dashboard.py")


if __name__ == "__main__":

    menu()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    st.header("Sign Up", text_alignment="center")

    conn = get_connection(ENV)

    build_form(
        conn=conn,
        field_labels={
            "name": "default",
            "email": "default",
            "password": "password",
        },
        form_name="Sign up",
        form_key="sign_up_form",
        cancel_name="Back to Dashboard",
        on_submit=handle_signup,
        on_cancel=handle_cancel
    )

    conn.close()

    page_redirect("Already have an account? Log in",
                  "pages/log_in.py")
