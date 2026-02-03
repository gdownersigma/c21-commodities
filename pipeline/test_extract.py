"""Script to test the extract module functions."""

from extract import get_commodity_data, loop_commodities

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from extract import get_commodity_data


# Sample API response matching FMP structure
SAMPLE_API_RESPONSE = [
    {
        "symbol": "GCUSD",
        "name": "Gold Futures",
        "price": 3375.3,
        "changePercentage": -0.65635,
        "change": -22.3,
        "volume": 170936,
        "dayLow": 3355.2,
        "dayHigh": 3401.1,
        "yearHigh": 3509.9,
        "yearLow": 2354.6,
        "marketCap": None,
        "priceAvg50": 3358.706,
        "priceAvg200": 3054.501,
        "exchange": "COMMODITY",
        "open": 3398.6,
        "previousClose": 3397.6,
        "timestamp": 1753372205
    }
]


class TestGetCommodityDataSuccess:
    """Tests for successful API responses."""

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_returns_dataframe_on_success(self, mock_get):
        """Should return a DataFrame when API returns 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_dataframe_contains_expected_columns(self, mock_get):
        """Should contain all expected columns from API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        expected_cols = [
            "symbol", "name", "price", "changePercentage", "change",
            "volume", "dayLow", "dayHigh", "yearHigh", "yearLow",
            "priceAvg50", "priceAvg200", "open", "previousClose", "timestamp"
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_dataframe_values_match_response(self, mock_get):
        """Should correctly parse values from API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert result.iloc[0]["symbol"] == "GCUSD"
        assert result.iloc[0]["price"] == 3375.3
        assert result.iloc[0]["volume"] == 170936
        assert result.iloc[0]["changePercentage"] == -0.65635

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_constructs_correct_url(self, mock_get):
        """Should construct URL with symbol and API key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        get_commodity_data("GCUSD")

        called_url = mock_get.call_args[0][0]
        assert "symbol=GCUSD" in called_url
        assert "apikey=test_key_123" in called_url
        assert "financialmodelingprep.com" in called_url


class TestGetCommodityDataFailures:
    """Tests for error handling."""

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_returns_empty_dataframe_on_404(self, mock_get):
        """Should return empty DataFrame when API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        result = get_commodity_data("INVALID")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_returns_empty_dataframe_on_500(self, mock_get):
        """Should return empty DataFrame when API returns 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_returns_empty_dataframe_on_401(self, mock_get):
        """Should return empty DataFrame on authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API Key"
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.dict("os.environ", {}, clear=True)
    def test_raises_error_when_api_key_missing(self):
        """Should raise ValueError when API_KEY not in environment."""
        with pytest.raises(ValueError) as exc_info:
            get_commodity_data("GCUSD")

        assert "API_KEY not found" in str(exc_info.value)

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_handles_timeout(self, mock_get):
        """Should handle request timeout gracefully."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout(
            "Connection timed out")

        with pytest.raises(requests.exceptions.Timeout):
            get_commodity_data("GCUSD")

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_returns_empty_dataframe_on_empty_response(self, mock_get):
        """Should handle empty list response from API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestGetCommodityDataEdgeCases:
    """Tests for edge cases and data quality."""

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_handles_null_values_in_response(self, mock_get):
        """Should handle null values in API response."""
        response_with_nulls = [{
            "symbol": "GCUSD",
            "name": "Gold Futures",
            "price": 3375.3,
            "changePercentage": None,
            "change": None,
            "volume": None,
            "dayLow": 3355.2,
            "dayHigh": 3401.1,
            "yearHigh": None,
            "yearLow": None,
            "marketCap": None,
            "priceAvg50": None,
            "priceAvg200": None,
            "exchange": "COMMODITY",
            "open": None,
            "previousClose": 3397.6,
            "timestamp": 1753372205
        }]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_with_nulls
        mock_get.return_value = mock_response

        result = get_commodity_data("GCUSD")

        assert len(result) == 1
        assert pd.isna(result.iloc[0]["volume"])
        assert pd.isna(result.iloc[0]["changePercentage"])

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_handles_special_characters_in_symbol(self, mock_get):
        """Should properly encode symbols in URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        get_commodity_data("ZC=F")

        called_url = mock_get.call_args[0][0]
        assert "symbol=ZC=F" in called_url or "symbol=ZC%3DF" in called_url

    @patch.dict("os.environ", {"API_KEY": "test_key_123"})
    @patch("extract.req.get")
    def test_timeout_parameter_is_set(self, mock_get):
        """Should set timeout parameter on request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_get.return_value = mock_response

        get_commodity_data("GCUSD")

        _, kwargs = mock_get.call_args
        assert "timeout" in kwargs
        assert kwargs["timeout"] == 5


# Fixture for integration testing (optional - requires real API key)
@pytest.fixture
def real_api_key():
    """Load real API key for integration tests."""
    import os
    key = os.environ.get("FMP_API_KEY")
    if not key:
        pytest.skip("FMP_API_KEY not set - skipping integration test")
    return key
