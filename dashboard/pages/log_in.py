""""""

import streamlit as st
import pandas as pd

from menu import menu
from helper_functions import authenticate_user

menu()

st.title(body="Website Title",
         text_alignment="center")

with st.form("log_in_form"):

    st.header(body="Log in!",
              text_alignment="center")

    st.divider()

    field_input = {
        "email": st.text_input("Email", key="email"),
        "password": st.text_input("Password", type="password", key="password"),
    }
    submitted = st.form_submit_button("Log in")

    if submitted:
        if authenticate_user(field_input):
            st.success("Logged in successfully!")

            # Need to use the database details, not field_input
            st.session_state.current_user = field_input
            st.switch_page("dashboard.py")
        else:
            st.error("Please fill in all fields correctly.")

with st.container(horizontal_alignment="center"):
    if st.button("Don't have an account? Sign up"):
        st.switch_page("pages/sign_up.py")
