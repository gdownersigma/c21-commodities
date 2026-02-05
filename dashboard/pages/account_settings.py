"""Page for user account settings."""

# pylint: disable=import-error

import streamlit as st
import pandas as pd

from menu import menu_with_redirect
from dashboard_items import page_redirect

st.set_page_config(
    layout="wide"
)

if __name__ == "__main__":

    menu_with_redirect()

    st.title(body="Pivot Point",
             text_alignment="center")

    st.divider()

    st.header("Account Settings", text_alignment="center")

    col1, col2 = st.columns(2)

    with col1:
        page_redirect("Edit Account Details",
                      "pages/edit_account.py",
                      "left")

    with col2:
        page_redirect("Edit Subscriptions",
                      "pages/edit_subscriptions.py",
                      "right")
