""""""

import streamlit as st
import pandas as pd

from menu import menu

menu()

"Log in!"

# In your log_in page or wherever you want to link to sign_up:
if st.button("Don't have an account? Sign up"):
    st.switch_page("pages/sign_up.py")
