"""Navigation menu for the dashboard."""

import streamlit as st

from dashboard_items import (welcome_message)


def authenticated_menu():
    """Show a navigation menu for authenticated users."""

    st.sidebar.page_link("dashboard.py", label="Home")
    st.sidebar.page_link("pages/edit_subscriptions.py",
                         label="Account Settings")


def unauthenticated_menu():
    """Show a navigation menu for unauthenticated users."""

    st.sidebar.page_link("dashboard.py", label="Home")
    st.sidebar.page_link("pages/log_in.py", label="Log in")


def menu():
    """Determine if a user is logged in or not and show the correct navigation menu."""

    welcome_message()

    if "user" not in st.session_state or not st.session_state.user:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    """Redirect users to the main page if not logged in, then show menu."""

    if "user" not in st.session_state or not st.session_state.user:
        st.switch_page("dashboard.py")
    menu()
