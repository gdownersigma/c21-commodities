"""Page for user log in."""

from os import environ as ENV
import streamlit as st
import pandas as pd
from bcrypt import hashpw, gensalt

from menu import menu
from query_data import (get_connection)
from dashboard_items import (build_form,
                             account_entry_redirect)
from query_data import (get_user_by_email_password)


def handle_login(conn, field_input):
    """Handle login logic."""

    field_input["hashed_password"] = hashpw(
        field_input["password"].encode('utf-8'), gensalt())

    user = get_user_by_email_password(
        conn, field_input["email"], field_input["password"])

    if user:
        st.session_state.current_user = user
        st.success(f"Welcome back, {user['user_name']}!")
        st.switch_page("dashboard.py")
    else:
        st.error("Invalid email or password. Please try again.")


if __name__ == "__main__":
    menu()

    st.title(body="Website Title",
             text_alignment="center")

    conn = get_connection(ENV)

    build_form(
        conn=conn,
        field_labels={
            "email": "default",
            "password": "password",
        },
        form_name="Log in",
        form_key="log_in_form",
        on_submit=handle_login
    )

    conn.close()

    account_entry_redirect("Don't have an account? Sign up",
                           "pages/sign_up.py")
