"""Page for user account settings."""

# pylint: disable=import-error

import streamlit as st
# import pandas as pd

from menu import menu_with_redirect


if __name__ == "__main__":

    menu_with_redirect()

    st.title(body="Account Settings",
             text_alignment="center")

    st.info("Account settings functionality is coming soon!")
