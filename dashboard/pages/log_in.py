"""Page for user log in."""

import streamlit as st
import pandas as pd

from menu import menu
from helper_functions import (authenticate_user)
from dashboard_items import (build_form,
                             account_entry_redirect)


if __name__ == "__main__":
    menu()

    st.title(body="Website Title",
             text_alignment="center")

    build_form(field_labels={
        "email": "default",
        "password": "password",
    },
        form_name="Log in",
        form_key="log_in_form"
    )

    account_entry_redirect("Don't have an account? Sign up",
                           "pages/sign_up.py")
