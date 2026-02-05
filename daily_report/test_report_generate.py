"""Tests for report_generate.py"""
import pandas as pd
import pytest
from datetime import date
from report_generate import (
    format_name,
    calculate_profit_loss,
    get_user_market_data,
    generate_price_chart,
    generate_user_html_report,
)


@pytest.fixture
def report_date():
    return date(2026, 2, 4)


@pytest.fixture
def sample_user_data():
    return pd.DataFrame({
        "symbol": ["GCUSD"],
        "commodity_name": ["Gold"],
        "open_price_calc": [1800.0],
        "close_price": [1820.0],
        "day_low": [1790.0],
        "day_high": [1830.0],
        "volume": [10000],
        "buy_price": [1750.0],
        "sell_price": [1900.0]
    })


@pytest.fixture
def sample_market_df():
    return pd.DataFrame({
        "symbol": ["GCUSD", "GCUSD", "GCUSD"],
        "price": [1800.0, 1850.0, 1820.0],
        "recorded_at": pd.to_datetime([
            "2026-02-04 09:00", "2026-02-04 12:00", "2026-02-04 16:00"
        ])
    })


class TestFormatName:
    """Tests for the format_name function."""

    @pytest.mark.parametrize("input_name,expected", [
        ("alice_jones", "Alice Jones"),
        ("alice", "Alice"),
        ("john_paul_jones", "John Paul Jones"),
        ("Alice", "Alice"),
        ("", ""),
    ])
    def test_format_name(self, input_name, expected):
        assert format_name(input_name) == expected


class TestCalculateProfitLoss:
    """Tests for the calculate_profit_loss function."""

    @pytest.mark.parametrize("close,buy,expected_pl,expected_pct", [
        (120.0, 100.0, 20.0, 20.0),
        (80.0, 100.0, -20.0, -20.0),
        (100.0, 100.0, 0.0, 0.0),
    ])
    def test_profit_loss_calculation(self, close, buy, expected_pl, expected_pct):
        row = pd.Series({"close_price": close, "buy_price": buy})
        result = calculate_profit_loss(row)
        assert result["profit_loss"] == expected_pl
        assert result["profit_loss_pct"] == expected_pct

    @pytest.mark.parametrize("buy_price", [None, 0])
    def test_invalid_buy_price_returns_none(self, buy_price):
        row = pd.Series({"close_price": 100.0, "buy_price": buy_price})
        result = calculate_profit_loss(row)
        assert result["profit_loss"] is None
        assert result["profit_loss_pct"] is None


class TestGetUserMarketData:
    """Tests for the get_user_market_data function."""

    def test_filters_by_user_commodities(self):
        user_commodities_df = pd.DataFrame({
            "user_id": [1, 1, 2],
            "symbol": ["GCUSD", "SIUSD", "GCUSD"],
            "buy_price": [1800.0, 25.0, 1750.0],
            "sell_price": [1900.0, 30.0, 1850.0]
        })
        market_df = pd.DataFrame({
            "symbol": ["GCUSD", "GCUSD", "SIUSD", "SIUSD", "CLUSD"],
            "price": [1810.0, 1820.0, 25.5, 26.0, 75.0],
            "recorded_at": pd.to_datetime([
                "2026-02-04 09:00", "2026-02-04 16:00",
                "2026-02-04 09:00", "2026-02-04 16:00",
                "2026-02-04 09:00"
            ])
        })

        result = get_user_market_data(1, market_df, user_commodities_df)

        assert len(result) == 2
        assert set(result["symbol"].tolist()) == {"GCUSD", "SIUSD"}

    def test_calculates_open_and_close_prices(self, sample_market_df):
        user_commodities_df = pd.DataFrame({
            "user_id": [1],
            "symbol": ["GCUSD"],
            "buy_price": [1800.0],
            "sell_price": [1900.0]
        })

        result = get_user_market_data(1, sample_market_df, user_commodities_df)

        assert result.iloc[0]["open_price_calc"] == 1800.0
        assert result.iloc[0]["close_price"] == 1820.0

    def test_empty_result_for_user_with_no_commodities(self):
        user_commodities_df = pd.DataFrame({
            "user_id": [2],
            "symbol": ["GCUSD"],
            "buy_price": [1800.0],
            "sell_price": [1900.0]
        })
        market_df = pd.DataFrame({
            "symbol": ["GCUSD"],
            "price": [1810.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00"])
        })

        result = get_user_market_data(1, market_df, user_commodities_df)

        assert len(result) == 0


class TestGeneratePriceChart:
    """Tests for the generate_price_chart function."""

    def test_returns_none_with_insufficient_data(self):
        market_df = pd.DataFrame({
            "symbol": ["GCUSD"],
            "price": [1800.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00"])
        })
        assert generate_price_chart("GCUSD", "Gold", market_df) is None

    def test_returns_tuple_with_sufficient_data(self, sample_market_df):
        result = generate_price_chart("GCUSD", "Gold", sample_market_df)

        assert result is not None
        cid, img_bytes = result
        assert cid == "chart_GCUSD"
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0

    def test_handles_symbol_with_slash(self):
        market_df = pd.DataFrame({
            "symbol": ["GC/USD", "GC/USD"],
            "price": [1800.0, 1850.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00", "2026-02-04 16:00"])
        })

        cid, _ = generate_price_chart("GC/USD", "Gold", market_df)
        assert cid == "chart_GC_USD"


class TestGenerateUserHtmlReport:
    """Tests for the generate_user_html_report function."""

    def test_generates_html_with_user_name(self, sample_user_data, sample_market_df, report_date):
        result = generate_user_html_report(
            "alice_jones", sample_user_data, report_date, sample_market_df)

        assert "html" in result
        assert "images" in result
        assert "Alice Jones" in result["html"]
        assert "Gold" in result["html"]
        assert "GCUSD" in result["html"]

    def test_report_contains_profit_loss(self, sample_user_data, sample_market_df, report_date):
        result = generate_user_html_report(
            "alice_jones", sample_user_data, report_date, sample_market_df)

        assert "+$70.00" in result["html"]

    def test_report_shows_commodity_count(self, sample_market_df, report_date):
        user_data = pd.DataFrame({
            "symbol": ["GCUSD", "SIUSD"],
            "commodity_name": ["Gold", "Silver"],
            "open_price_calc": [1800.0, 25.0],
            "close_price": [1820.0, 26.0],
            "day_low": [1790.0, 24.0],
            "day_high": [1830.0, 27.0],
            "volume": [10000, 5000],
            "buy_price": [1750.0, 24.0],
            "sell_price": [1900.0, 30.0]
        })

        result = generate_user_html_report(
            "alice_jones", user_data, report_date, sample_market_df)

        assert "<strong>2</strong> commodities" in result["html"]
