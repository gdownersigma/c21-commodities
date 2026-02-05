"""Page for user log in."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st
from bcrypt import hashpw, gensalt

from menu import menu
from query_data import get_connection
from dashboard_items import (build_form,
                             page_redirect)
from helper_functions import fill_user_commodities
from query_data import (get_user_by_email_password)

st.set_page_config(
    layout="centered"
)


def handle_login(conn, field_input):
    """Handle login logic."""

    field_input["hashed_password"] = hashpw(
        field_input["password"].encode('utf-8'), gensalt())

    user = get_user_by_email_password(
        conn, field_input["email"], field_input["password"])

    if not user:
        st.error("Invalid email or password. Please try again.")
    else:
        st.success(f"Welcome back, {user['user_name']}!")

        fill_user_commodities(conn, user["user_id"])

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

    st.header("Log In", text_alignment="center")

    conn = get_connection(ENV)

    build_form(
        conn=conn,
        field_labels={
            "email": "default",
            "password": "password",
        },
        form_name="Log in",
        form_key="log_in_form",
        cancel_name="Back to Dashboard",
        on_submit=handle_login,
        on_cancel=handle_cancel
    )

    conn.close()

    page_redirect("Don't have an account? Sign up",
                  "pages/sign_up.py")
