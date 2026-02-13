"""Tests for menu.py"""

from unittest.mock import patch

from menu import (
    authenticated_menu,
    menu,
    menu_with_redirect,
    unauthenticated_menu,
)


@patch("menu.st")
@patch("menu.welcome_message")
def test_authenticated_menu_calls_welcome(mock_welcome, mock_st):
    """Should call welcome_message for authenticated users."""
    authenticated_menu()
    mock_welcome.assert_called_once()


@patch("menu.st")
def test_unauthenticated_menu_shows_divider(mock_st):
    """Should show divider for unauthenticated users."""
    unauthenticated_menu()
    mock_st.sidebar.divider.assert_called_once()


@patch("menu.unauthenticated_menu")
@patch("menu.st")
def test_menu_unauthenticated_when_no_user(mock_st, mock_unauth):
    """Should show unauthenticated menu when no user."""
    mock_st.session_state = {}
    menu()
    mock_unauth.assert_called_once()


@patch("menu.st")
def test_menu_with_redirect_redirects(mock_st):
    """Should redirect when not logged in."""
    mock_st.session_state = {}
    menu_with_redirect()
    mock_st.switch_page.assert_called_once_with("dashboard.py")
