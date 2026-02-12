"""Tests for alert.py functions"""
from unittest.mock import patch, MagicMock
import pytest
from psycopg2 import DatabaseError
from alert import (
    check_one_alert,
    check_all_alerts,
    get_latest_prices,
    get_generated_report_list,
    get_user_commodities,
    get_required_customer_info,
    get_all_required_customer_info,
    update_alerted_at,
    handler
)


def test_get_latest_prices():
    """Test converting event body to dictionary"""
    event = {
        "statusCode": 200,
        "body": [
            {"commodity_id": 1, "price": 100.5},
            {"commodity_id": 2, "price": 200.75}
        ]
    }
    result = get_latest_prices(event)

    assert isinstance(result, dict)
    assert result[1]['price'] == 100.5
    assert result[2]['price'] == 200.75


def test_check_one_alert_buy_triggered():
    """Test buy alert is triggered when price is below buy_price"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": None
    }
    commodity_price = {"commodity_id": 1, "price": 95.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'buy'
    assert result[1] == user_commodity


def test_check_one_alert_sell_triggered():
    """Test sell alert is triggered when price is above sell_price"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": None,
        "sell_price": 100.0
    }
    commodity_price = {"commodity_id": 1, "price": 105.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'sell'
    assert result[1] == user_commodity


def test_check_one_alert_not_triggered():
    """Test alert is not triggered when conditions are not met"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": 200.0
    }
    commodity_price = {"commodity_id": 1, "price": 150.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is None


def test_check_one_alert_none_commodity_price():
    """Test alert returns None when commodity_price is None"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": None
    }

    result = check_one_alert(user_commodity, None)

    assert result is None


def test_check_all_alerts():
    """Test checking multiple alerts"""
    user_commodities = [
        {"commodity_id": 1, "buy_price": 100.0, "sell_price": None},
        {"commodity_id": 2, "buy_price": None, "sell_price": 200.0},
        {"commodity_id": 3, "buy_price": 50.0, "sell_price": None}
    ]

    latest_prices = {
        1: {"commodity_id": 1, "price": 95.0},   # Buy alert triggered
        2: {"commodity_id": 2, "price": 205.0},  # Sell alert triggered
        3: {"commodity_id": 3, "price": 60.0}    # No alert
    }

    result = check_all_alerts(user_commodities, latest_prices)

    assert len(result) == 2
    assert result[0][0] == 'buy'
    assert result[1][0] == 'sell'


def test_check_one_alert_buy_at_exact_price():
    """Test buy alert is triggered when price equals buy_price"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": None
    }
    commodity_price = {"commodity_id": 1, "price": 100.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'buy'


def test_check_one_alert_sell_at_exact_price():
    """Test sell alert is triggered when price equals sell_price"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": None,
        "sell_price": 100.0
    }
    commodity_price = {"commodity_id": 1, "price": 100.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'sell'


def test_check_one_alert_both_prices_set_buy_triggered():
    """Test buy alert when both buy and sell prices are set"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": 200.0
    }
    commodity_price = {"commodity_id": 1, "price": 95.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'buy'


def test_check_one_alert_both_prices_set_sell_triggered():
    """Test sell alert when both buy and sell prices are set"""
    user_commodity = {
        "commodity_id": 1,
        "buy_price": 100.0,
        "sell_price": 200.0
    }
    commodity_price = {"commodity_id": 1, "price": 205.0}

    result = check_one_alert(user_commodity, commodity_price)

    assert result is not None
    assert result[0] == 'sell'


def test_check_all_alerts_empty_user_commodities():
    """Test checking alerts with empty user commodities list"""
    result = check_all_alerts([], {})

    assert result == []


def test_check_all_alerts_missing_commodity_prices():
    """Test checking alerts when some commodity prices are missing"""
    user_commodities = [
        {"commodity_id": 1, "buy_price": 100.0, "sell_price": None},
        {"commodity_id": 2, "buy_price": None, "sell_price": 200.0},
    ]

    latest_prices = {
        1: {"commodity_id": 1, "price": 95.0},  # Buy alert triggered
        # Commodity 2 missing - should return None for that check
    }

    result = check_all_alerts(user_commodities, latest_prices)

    assert len(result) == 1
    assert result[0][0] == 'buy'


def test_get_latest_prices_empty_body():
    """Test getting latest prices with empty body"""
    event = {"statusCode": 200, "body": []}
    result = get_latest_prices(event)

    assert isinstance(result, dict)
    assert len(result) == 0


# Tests for get_generated_report_list
def test_get_generated_report_list():
    """Test generating report list from customer info"""
    customer_info = [
        {
            "alert_type": "buy",
            "user_name": "test_user",
            "commodity_name": "Gold",
            "symbol": "XAU",
            "current_price": 1800.00,
            "target_price": 1850.00
        }
    ]

    result = get_generated_report_list(customer_info)

    assert len(result) == 1
    assert "Gold" in result[0]
    assert "BUY" in result[0]


def test_get_generated_report_list_empty():
    """Test generating report list with empty input"""
    result = get_generated_report_list([])
    assert result == []


# Tests for get_user_commodities with mocked database
@patch('alert.get_conn')
def test_get_user_commodities_success(mock_get_conn):
    """Test fetching user commodities from database"""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (1, 1, 100.0, None, None),
        (2, 2, None, 200.0, None)
    ]
    mock_cursor.description = [
        ('user_id',), ('commodity_id',), ('buy_price',
                                          ), ('sell_price',), ('alerted_at',)
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    result = get_user_commodities()

    assert len(result) == 2
    assert result[0]['user_id'] == 1
    mock_conn.close.assert_called_once()


@patch('alert.get_conn')
def test_get_user_commodities_database_error(mock_get_conn):
    """Test get_user_commodities raises on database error"""
    mock_get_conn.side_effect = DatabaseError("Connection failed")

    with pytest.raises(DatabaseError):
        get_user_commodities()


# Tests for get_required_customer_info
@patch('alert.get_conn')
def test_get_required_customer_info_success(mock_get_conn):
    """Test getting customer info for an alert"""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (
        "test@email.com", "test_user", "XAU", "Gold")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    action = ('buy', {'user_id': 1, 'commodity_id': 1, 'buy_price': 100.0})
    latest_prices = {1: {'price': 95.0}}

    result = get_required_customer_info(action, latest_prices)

    assert result['email'] == "test@email.com"
    assert result['alert_type'] == 'buy'
    assert result['current_price'] == 95.0


@patch('alert.get_conn')
def test_get_required_customer_info_not_found(mock_get_conn):
    """Test get_required_customer_info raises ValueError when not found"""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    action = ('buy', {'user_id': 999, 'commodity_id': 999, 'buy_price': 100.0})
    latest_prices = {999: {'price': 95.0}}

    with pytest.raises(ValueError):
        get_required_customer_info(action, latest_prices)


# Tests for get_all_required_customer_info
@patch('alert.get_required_customer_info')
def test_get_all_required_customer_info_success(mock_get_info):
    """Test getting all customer info for alerts"""
    mock_get_info.return_value = {
        "email": "test@email.com", "alert_type": "buy"}

    actions = [
        ('buy', {'user_id': 1, 'commodity_id': 1}),
        ('sell', {'user_id': 2, 'commodity_id': 2})
    ]
    latest_prices = {1: {'price': 95.0}, 2: {'price': 205.0}}

    result = get_all_required_customer_info(actions, latest_prices)

    assert len(result) == 2


@patch('alert.get_required_customer_info')
def test_get_all_required_customer_info_skips_errors(mock_get_info):
    """Test that errors are skipped when getting customer info"""
    mock_get_info.side_effect = [
        {"email": "test@email.com"},
        ValueError("Not found")
    ]

    actions = [
        ('buy', {'user_id': 1, 'commodity_id': 1}),
        ('sell', {'user_id': 2, 'commodity_id': 2})
    ]
    latest_prices = {}

    result = get_all_required_customer_info(actions, latest_prices)

    assert len(result) == 1


# Tests for update_alerted_at
@patch('alert.get_conn')
def test_update_alerted_at_success(mock_get_conn):
    """Test updating alerted_at timestamp"""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user_commodity = {'user_id': 1, 'commodity_id': 1}

    update_alerted_at(user_commodity)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


# Tests for handler
@patch('alert.send_emails')
@patch('alert.get_generated_report_list')
@patch('alert.get_all_required_customer_info')
@patch('alert.get_user_commodities')
def test_handler_success(mock_get_user, mock_get_all_info, mock_get_reports, mock_send):
    """Test handler processes alerts successfully"""
    mock_get_user.return_value = [
        {'commodity_id': 1, 'buy_price': 100.0, 'sell_price': None}
    ]
    mock_get_all_info.return_value = [{'email': 'test@email.com'}]
    mock_get_reports.return_value = ['<html>report</html>']

    event = {'body': [{'commodity_id': 1, 'price': 95.0}]}

    result = handler(event, None)

    assert result['statusCode'] == 200
    mock_send.assert_called_once()


@patch('alert.get_user_commodities')
def test_handler_no_user_commodities(mock_get_user):
    """Test handler when no user commodities found"""
    mock_get_user.return_value = []

    event = {'body': []}

    result = handler(event, None)

    assert result['statusCode'] == 200
    assert "No alerts to process" in result['message']


@patch('alert.get_user_commodities')
def test_handler_no_alerts_triggered(mock_get_user):
    """Test handler when no alert conditions are met"""
    mock_get_user.return_value = [
        {'commodity_id': 1, 'buy_price': 100.0, 'sell_price': None}
    ]

    event = {'body': [{'commodity_id': 1, 'price': 150.0}]}

    result = handler(event, None)

    assert result['statusCode'] == 200
    assert "No alerts triggered" in result['message']


@patch('alert.get_user_commodities')
def test_handler_database_error(mock_get_user):
    """Test handler handles database errors"""
    mock_get_user.side_effect = DatabaseError("Connection failed")

    event = {'body': []}

    result = handler(event, None)

    assert result['statusCode'] == 500
    assert "Database error" in result['error']
