import streamlit as st


def authenticated_menu():
    """Show a navigation menu for authenticated users."""

    st.sidebar.page_link("dashboard.py", label="Home")
    st.sidebar.page_link("pages/account_settings.py", label="Account Settings")


def unauthenticated_menu():
    """Show a navigation menu for unauthenticated users."""

    st.sidebar.page_link("dashboard.py", label="Home")
    st.sidebar.page_link("pages/log_in.py", label="Log in")


def menu():
    """Determine if a user is logged in or not and show the correct navigation menu."""

    if "current_user" not in st.session_state or not st.session_state.current_user:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    """Redirect users to the main page if not logged in, then show menu."""

    if "current_user" not in st.session_state or not st.session_state.current_user:
        st.switch_page("dashboard.py")
    menu()
