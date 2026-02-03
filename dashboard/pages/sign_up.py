""""""

import streamlit as st
import pandas as pd

from menu import menu
from helper_functions import authenticate_user

menu()

st.title(body="Website Title",
         text_alignment="center")

with st.form("sign_up_form"):

    st.header(body="Sign up!",
              text_alignment="center")

    st.divider()

    field_input = {
        "name": st.text_input("Name", key="name"),
        "email": st.text_input("Email", key="email"),
        "password": st.text_input("Password", type="password", key="password"),
    }
    submitted = st.form_submit_button("Sign up")

    if submitted:
        if authenticate_user(field_input):
            st.success("Signed up successfully!")

            st.session_state.current_user = field_input
            st.switch_page("dashboard.py")
        else:
            st.error("Please fill in all fields correctly.")

with st.container(horizontal_alignment="center"):
    if st.button("Already have an account? Log in"):
        st.switch_page("pages/log_in.py")
