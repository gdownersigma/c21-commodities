"""File to hold helper functions for the dashboard."""

# pylint: disable=no-member

from os import _Environ

import streamlit as st
from bcrypt import hashpw, gensalt, checkpw
from cryptography.fernet import Fernet

from query_data import get_commodities_with_user_subscriptions


def add_commodity():
    """Add a new commodity slot."""
    st.session_state.num_commodities += 1


def remove_commodity():
    """Remove the last commodity slot."""
    if st.session_state.num_commodities > 1:
        st.session_state.num_commodities -= 1

        key = f"commodity_{st.session_state.num_commodities}"
        if key in st.session_state.selected_commodities:
            del st.session_state.selected_commodities[key]


def clean_input(field_input: dict) -> dict:
    """Return clean input without leading or trailing spaces."""

    for key, val in field_input.items():
        if val is not None and val != "":
            field_input[key] = val.strip()

    return field_input


def authenticate_field(field_input: str) -> bool:
    """Return True if the field is populated."""

    return not (field_input is None or field_input == "")


def authenticate_user_input(user: dict) -> bool:
    """Return True if all user fields are populated."""

    for value in user.values():
        if not authenticate_field(value):
            return False
    return True


def fill_user_commodities(conn, user_id):
    """Fill session state with user's subscribed commodities."""

    comm_data = get_commodities_with_user_subscriptions(
        conn, user_id)

    st.session_state.user_commodities = comm_data

    st.session_state.subscribed_commodities = [
        comm_id for comm_id, data in comm_data.items() if data["track"]]


def hash_and_encrypt(config: _Environ, var: str) -> bytes:
    """Hash and encrypt a variable."""

    hashed_var = hashpw(var.encode('utf-8'), gensalt())
    encryption_key = config.get("ENCRYPTION_KEY")
    cipher_suite = Fernet(encryption_key)
    encrypted_var = cipher_suite.encrypt(hashed_var)

    return encrypted_var


def decrypt_and_verify(config: _Environ, var: str, encrypted_var: bytes) -> bool:
    """Decrypt and verify a variable."""

    encryption_key = config.get("ENCRYPTION_KEY")
    cipher_suite = Fernet(encryption_key)
    decrypted_var = cipher_suite.decrypt(encrypted_var)

    return checkpw(var.encode('utf-8'), decrypted_var)
