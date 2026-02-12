"""Tests for report_generate.py"""
import pandas as pd
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from report_generate import (
    format_name,
    calculate_profit_loss,
    get_user_market_data,
    generate_price_chart,
    generate_user_html_report,
    get_logo_bytes,
    get_html_template,
    generate_ai_summary,
    generate_all_user_reports,
    handler,
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
        """Should convert underscores to spaces and title case the name."""
        assert format_name(input_name) == expected


class TestCalculateProfitLoss:
    """Tests for the calculate_profit_loss function."""

    @pytest.mark.parametrize("close,buy,expected_pl,expected_pct", [
        (120.0, 100.0, 20.0, 20.0),
        (80.0, 100.0, -20.0, -20.0),
        (100.0, 100.0, 0.0, 0.0),
    ])
    def test_profit_loss_calculation(self, close, buy, expected_pl, expected_pct):
        """Should calculate profit/loss amount and percentage correctly."""
        row = pd.Series({"close_price": close, "buy_price": buy})
        result = calculate_profit_loss(row)
        assert result["profit_loss"] == expected_pl
        assert result["profit_loss_pct"] == expected_pct

    @pytest.mark.parametrize("buy_price", [None, 0])
    def test_invalid_buy_price_returns_none(self, buy_price):
        """Should return None for profit/loss when buy price is invalid."""
        row = pd.Series({"close_price": 100.0, "buy_price": buy_price})
        result = calculate_profit_loss(row)
        assert result["profit_loss"] is None
        assert result["profit_loss_pct"] is None


class TestGetUserMarketData:
    """Tests for the get_user_market_data function."""

    def test_filters_by_user_commodities(self):
        """Should filter market data to only include user's commodities."""
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
        """Should calculate open and close prices from market data."""
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
        """Should return empty result when user has no commodities."""
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
        """Should return None when there is insufficient data for chart."""
        market_df = pd.DataFrame({
            "symbol": ["GCUSD"],
            "price": [1800.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00"])
        })
        assert generate_price_chart("GCUSD", "Gold", market_df) is None

    def test_returns_tuple_with_sufficient_data(self, sample_market_df):
        """Should return chart ID and image bytes with sufficient data."""
        result = generate_price_chart("GCUSD", "Gold", sample_market_df)

        assert result is not None
        cid, img_bytes = result
        assert cid == "chart_GCUSD"
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0

    def test_handles_symbol_with_slash(self):
        """Should replace slashes with underscores in chart ID."""
        market_df = pd.DataFrame({
            "symbol": ["GC/USD", "GC/USD"],
            "price": [1800.0, 1850.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00", "2026-02-04 16:00"])
        })

        cid, _ = generate_price_chart("GC/USD", "Gold", market_df)
        assert cid == "chart_GC_USD"


class TestGenerateUserHtmlReport:
    """Tests for the generate_user_html_report function."""

    @pytest.fixture(autouse=True)
    def mock_ai_summary(self):
        with patch("report_generate.generate_ai_summary", return_value="Mock AI summary"):
            yield

    def test_generates_html_with_user_name(self, sample_user_data, sample_market_df, report_date):
        """Should generate HTML report with formatted user name and commodity data."""
        result = generate_user_html_report(
            "alice_jones", sample_user_data, report_date, sample_market_df)

        assert "html" in result
        assert "images" in result
        assert "Alice Jones" in result["html"]
        assert "Gold" in result["html"]
        assert "GCUSD" in result["html"]

    def test_report_contains_profit_loss(self, sample_user_data, sample_market_df, report_date):
        """Should include profit/loss information in the report."""
        result = generate_user_html_report(
            "alice_jones", sample_user_data, report_date, sample_market_df)

        assert "+$70.00" in result["html"]

    def test_report_shows_commodity_count(self, sample_market_df, report_date):
        """Should display the correct count of commodities in the report."""
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


class TestGetLogoBytes:
    """Tests for the get_logo_bytes function."""

    def test_returns_bytes(self):
        """Should return logo as bytes."""
        result = get_logo_bytes()
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGetHtmlTemplate:
    """Tests for the get_html_template function."""

    def test_returns_string_with_placeholders(self):
        """Should return template string with required placeholders."""
        result = get_html_template()
        assert isinstance(result, str)
        assert "{user_name}" in result
        assert "{rows_html}" in result


class TestGenerateAiSummary:
    """Tests for the generate_ai_summary function."""

    @pytest.fixture
    def sample_data(self):
        return pd.DataFrame({
            "symbol": ["GCUSD"],
            "commodity_name": ["Gold"],
            "open_price_calc": [1800.0],
            "close_price": [1820.0],
            "buy_price": [1750.0],
        })

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": ""})
    def test_returns_empty_when_no_api_key(self, sample_data):
        """Should return empty string when API key is not configured."""
        result = generate_ai_summary(sample_data, date(2026, 2, 4))
        assert result == ""

    @patch("report_generate.requests.post")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_returns_ai_response(self, mock_post, sample_data):
        """Should return AI-generated summary when API call succeeds."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test summary"}}]
        }
        mock_post.return_value = mock_response

        result = generate_ai_summary(sample_data, date(2026, 2, 4))
        assert result == "Test summary"

    @patch("report_generate.requests.post")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_returns_empty_on_api_error(self, mock_post, sample_data):
        """Should return empty string when API call fails."""
        mock_post.side_effect = Exception("API error")

        result = generate_ai_summary(sample_data, date(2026, 2, 4))
        assert result == ""


class TestGenerateAllUserReports:
    """Tests for the generate_all_user_reports function."""

    @patch("report_generate.get_conn")
    @patch("report_generate.extract_user_commodities")
    @patch("report_generate.extract_market_records")
    @patch("report_generate.get_previous_day_date")
    @patch("report_generate.generate_ai_summary", return_value="Mock summary")
    def test_returns_empty_when_no_market_data(
        self, mock_ai, mock_date, mock_market, mock_commodities, mock_conn
    ):
        """Should return empty dict when no market data found."""
        mock_date.return_value = date(2026, 2, 4)
        mock_conn.return_value = MagicMock()
        mock_commodities.return_value = pd.DataFrame()
        mock_market.return_value = pd.DataFrame()

        result = generate_all_user_reports()
        assert result == {}

    @patch("report_generate.get_conn")
    @patch("report_generate.extract_user_commodities")
    @patch("report_generate.extract_market_records")
    @patch("report_generate.get_previous_day_date")
    @patch("report_generate.generate_ai_summary", return_value="Mock summary")
    def test_generates_reports_for_users(
        self, mock_ai, mock_date, mock_market, mock_commodities, mock_conn
    ):
        """Should generate reports for each user with data."""
        mock_date.return_value = date(2026, 2, 4)
        mock_conn.return_value = MagicMock()
        mock_commodities.return_value = pd.DataFrame({
            "user_id": [1],
            "user_name": ["alice"],
            "email": ["alice@test.com"],
            "symbol": ["GCUSD"],
            "commodity_name": ["Gold"],
            "buy_price": [1750.0],
            "sell_price": [1900.0],
        })
        mock_market.return_value = pd.DataFrame({
            "symbol": ["GCUSD", "GCUSD"],
            "price": [1800.0, 1820.0],
            "recorded_at": pd.to_datetime(["2026-02-04 09:00", "2026-02-04 16:00"]),
            "day_low": [1790.0, 1790.0],
            "day_high": [1830.0, 1830.0],
            "volume": [10000, 10000],
            "commodity_name": ["Gold", "Gold"],
        })

        result = generate_all_user_reports()
        assert "alice@test.com" in result
        assert "html" in result["alice@test.com"]


class TestHandler:
    """Tests for the Lambda handler function."""

    @patch("report_generate.generate_all_user_reports")
    def test_returns_zero_when_no_reports(self, mock_generate):
        """Should return emailsSent: 0 when no reports generated."""
        mock_generate.return_value = {}

        result = handler({}, None)

        assert result["statusCode"] == 200
        assert result["emailsSent"] == 0

    @patch("report_generate.generate_all_user_reports")
    @patch.dict("os.environ", {"SENDER_EMAIL": ""})
    def test_returns_error_when_no_sender_email(self, mock_generate):
        """Should return error when SENDER_EMAIL not configured."""
        mock_generate.return_value = {
            "test@test.com": {"html": "<html></html>", "images": {}}}

        result = handler({}, None)

        assert result["statusCode"] == 500
        assert "error" in result
