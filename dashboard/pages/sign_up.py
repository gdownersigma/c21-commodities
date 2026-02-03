"""Page for user sign up."""

import streamlit as st
import pandas as pd

from menu import menu
from helper_functions import authenticate_user
from dashboard_items import (build_form,
                             account_entry_redirect)


if __name__ == "__main__":
    menu()

    st.title(body="Website Title",
             text_alignment="center")

    build_form(field_labels={
        "name": "default",
        "email": "default",
        "password": "password",
    },
        form_name="Sign up",
        form_key="sign_up_form"
    )

    account_entry_redirect("Already have an account? Log in",
                           "pages/log_in.py")
