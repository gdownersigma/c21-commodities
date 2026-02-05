"""Tests for generate_alert.py functions"""
import pytest
import os
from generate_alert import generate_alert_email, get_logo_bytes


def test_generate_alert_email_buy():
    """Test generating a buy alert email"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'john_doe',
        'commodity_name': 'Gold Futures',
        'symbol': 'GCUSD',
        'current_price': 2000.50,
        'target_price': 2100.00
    }

    result = generate_alert_email(alert)

    assert isinstance(result, str)
    assert 'BUY ALERT TRIGGERED' in result
    assert 'Gold Futures' in result
    assert 'GCUSD' in result
    assert 'John' in result  # First name capitalized
    assert '$2000.50' in result
    assert '$2100.00' in result
    assert '#22c55e' in result  # Green color for buy


def test_generate_alert_email_sell():
    """Test generating a sell alert email"""
    alert = {
        'alert_type': 'sell',
        'user_name': 'jane_smith',
        'commodity_name': 'Silver Futures',
        'symbol': 'SIUSD',
        'current_price': 25.75,
        'target_price': 24.00
    }

    result = generate_alert_email(alert)

    assert isinstance(result, str)
    assert 'SELL ALERT TRIGGERED' in result
    assert 'Silver Futures' in result
    assert 'SIUSD' in result
    assert 'Jane' in result  # First name capitalized
    assert '$25.75' in result
    assert '$24.00' in result
    assert '#ef4444' in result  # Red color for sell


def test_generate_alert_email_has_logo():
    """Test that email includes logo reference"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'test_user',
        'commodity_name': 'Test Commodity',
        'symbol': 'TEST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert 'cid:logo' in result


def test_generate_alert_email_first_name_only():
    """Test that only first name is shown"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'alice_wonderland',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert 'Alice' in result
    assert 'Wonderland' not in result


def test_get_logo_bytes():
    """Test loading logo returns bytes"""
    result = get_logo_bytes()

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_alert_email_buy_uses_blue_accent():
    """Test that buy alert uses blue accent color"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'test_user',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert '#03c1ff' in result  # Blue accent for buy


def test_generate_alert_email_sell_uses_orange_accent():
    """Test that sell alert uses orange accent color"""
    alert = {
        'alert_type': 'sell',
        'user_name': 'test_user',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 90.0
    }

    result = generate_alert_email(alert)

    assert '#e6530c' in result  # Orange accent for sell


def test_generate_alert_email_contains_html_structure():
    """Test that email contains proper HTML structure"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'test_user',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert '<!DOCTYPE html>' in result
    assert '<html>' in result
    assert '</html>' in result
    assert '<body' in result
    assert '</body>' in result


def test_generate_alert_email_decimal_formatting():
    """Test that prices are formatted to 2 decimal places"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'test_user',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.123456,
        'target_price': 110.987654
    }

    result = generate_alert_email(alert)

    assert '$100.12' in result
    assert '$110.99' in result


def test_generate_alert_email_single_word_username():
    """Test handling of single word username"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'john',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert 'John' in result


def test_generate_alert_email_includes_view_dashboard_button():
    """Test that email includes View Dashboard button"""
    alert = {
        'alert_type': 'buy',
        'user_name': 'test_user',
        'commodity_name': 'Test',
        'symbol': 'TST',
        'current_price': 100.0,
        'target_price': 110.0
    }

    result = generate_alert_email(alert)

    assert 'View Dashboard' in result
    assert '#03c1ff' in result  # Blue button color
