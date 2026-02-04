"""Page for user log in."""

# pylint: disable=import-error

from os import environ as ENV
import streamlit as st
from bcrypt import hashpw, gensalt

from menu import menu
from query_data import get_connection
from dashboard_items import (build_form,
                             account_entry_redirect)
from query_data import (get_user_by_email_password,
                        get_users_subscribed_commodities)

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

        st.session_state.subscribed_commodities = get_users_subscribed_commodities(
            conn, user["user_id"])
        st.session_state.user = user

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

    account_entry_redirect("Don't have an account? Sign up",
                           "pages/sign_up.py")
