""""""

import streamlit as st
import pandas as pd

from menu import menu

menu()

"Sign up!"

# Or in sign_up page to go back to log in:
if st.button("Already have an account? Log in"):
    st.switch_page("pages/log_in.py")
