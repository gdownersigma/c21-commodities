"""Tests for alert.py functions"""
from alert import check_one_alert, check_all_alerts, get_latest_prices


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
