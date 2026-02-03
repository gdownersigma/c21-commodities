"""Page for user sign up."""

from os import environ as ENV
import streamlit as st
import pandas as pd
from bcrypt import hashpw, gensalt

from menu import menu
from query_data import (get_connection)
from dashboard_items import (build_form,
                             account_entry_redirect)
from query_data import (get_user_count_by_email,
                        create_user)


def handle_signup(conn, field_input):
    """Handle signup logic."""
    user_count = get_user_count_by_email(
        conn, field_input["email"])

    if user_count != 0:
        st.error("An account with this email already exists. Please log in.")
    else:
        field_input["hashed_password"] = hashpw(
            field_input["password"].encode('utf-8'), gensalt())

        create_user(conn, field_input)

        user = {
            "user_name": field_input["name"],
            "email": field_input["email"]
        }

        st.session_state.current_user = user
        st.success(f"Welcome, {user['user_name']}!")
        st.switch_page("dashboard.py")


if __name__ == "__main__":
    menu()

    st.title(body="Website Title",
             text_alignment="center")

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
        on_submit=handle_signup
    )

    conn.close()

    account_entry_redirect("Already have an account? Log in",
                           "pages/log_in.py")
