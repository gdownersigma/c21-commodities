"""Tests for historical_extract.py"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from historical_extract import fetch_historical_data


@pytest.fixture
def mock_api_response():
    """Sample API response data."""
    return [
        {"date": "2026-02-01", "open": 100.0, "high": 105.0,
            "low": 99.0, "close": 103.0, "volume": 1000},
        {"date": "2026-01-31", "open": 98.0, "high": 101.0,
            "low": 97.0, "close": 100.0, "volume": 1200},
    ]


class TestFetchHistoricalData:
    """Tests for fetch_historical_data function."""

    @patch("historical_extract.requests.get")
    @patch.dict("os.environ", {"API_KEY": "test_api_key"})
    def test_fetch_historical_data_returns_dataframe(self, mock_get, mock_api_response):
        """Test that the function returns a DataFrame."""
        mock_get.return_value.json.return_value = mock_api_response

        result = fetch_historical_data("AAPL")

        assert isinstance(result, pd.DataFrame)

    @patch("historical_extract.requests.get")
    @patch.dict("os.environ", {"API_KEY": "test_api_key"})
    def test_fetch_historical_data_contains_expected_columns(self, mock_get, mock_api_response):
        """Test that the DataFrame contains expected columns."""
        mock_get.return_value.json.return_value = mock_api_response

        result = fetch_historical_data("AAPL")

        expected_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in expected_columns:
            assert col in result.columns

    @patch("historical_extract.requests.get")
    @patch.dict("os.environ", {"API_KEY": "test_api_key"})
    def test_fetch_historical_data_correct_row_count(self, mock_get, mock_api_response):
        """Test that the DataFrame has the correct number of rows."""
        mock_get.return_value.json.return_value = mock_api_response

        result = fetch_historical_data("AAPL")

        assert len(result) == 2

    @patch("historical_extract.requests.get")
    @patch.dict("os.environ", {"API_KEY": "test_api_key"})
    def test_fetch_historical_data_calls_correct_url(self, mock_get):
        """Test that the API is called with correct URL parameters."""
        mock_get.return_value.json.return_value = []

        fetch_historical_data("AAPL")

        called_url = mock_get.call_args[0][0]
        assert "symbol=AAPL" in called_url
        assert "apikey=test_api_key" in called_url
        assert "from=" in called_url
        assert "to=" in called_url

    @patch("historical_extract.requests.get")
    @patch.dict("os.environ", {"API_KEY": "test_api_key"})
    def test_fetch_historical_data_empty_response(self, mock_get):
        """Test handling of empty API response."""
        mock_get.return_value.json.return_value = []

        result = fetch_historical_data("INVALID")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
