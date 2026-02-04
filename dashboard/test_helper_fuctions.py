"""Testing helper functions for the dashboard application."""

import pytest
import streamlit as st

from helper_functions import (
    clean_input,
    authenticate_field,
    authenticate_user_input
)


@pytest.mark.parametrize(
    "field_input, result",
    [
        ({
            "email": "    mark@example.com    ",
            "password": "securepassword    "
        },
            {
            "email": "mark@example.com",
            "password": "securepassword"
        }),
        ({
            "name": "Sarah   ",
            "email": "    sarah@example.com     ",
            "password": "    password234                   "
        },
            {
            "name": "Sarah",
            "email": "sarah@example.com",
            "password": "password234"
        }),
        ({
            "email": "",
            "password": "                 "
        },
            {
            "email": "",
            "password": ""
        })
    ]
)
def test_clean_input(field_input, result):
    """Test the clean_input function."""
    assert clean_input(field_input) == result


@pytest.mark.parametrize(
    "field_input, result",
    [
        ("valid_input", True),
        ("   spaced_input   ", True),
        ("", False),
        (None, False),
    ]
)
def test_authenticate_field(field_input, result):
    """Test the authenticate_field function."""
    assert authenticate_field(field_input) == result


@pytest.mark.parametrize(
    "field_input, result",
    [
        ({
            "name": "Sarah",
            "email": "sarah@example.com",
            "password": "password234"
        },
            True
        ),
        ({
            "email": "mark@example.com",
            "password": "password234"
        },
            True
        ),
        ({
            "name": "",
            "email": "sarah@example.com",
            "password": "password234"
        },
            False
        ),
        ({
            "name": "Sarah",
            "email": "",
            "password": "password234"
        },
            False
        ),
        ({
            "name": "Sarah",
            "email": "sarah@example.com",
            "password": ""
        },
            False
        ),
        ({
            "name": "",
            "email": "",
            "password": ""
        },
            False
        ),
    ]
)
def test_authenticate_user_input(field_input, result):
    """Test the authenticate_user_input function."""
    assert authenticate_user_input(field_input) == result