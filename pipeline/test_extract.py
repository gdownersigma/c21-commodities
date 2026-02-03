"""Script to test the extract module functions."""
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
from extract import (
    get_commodity_data,
    fetch_commodity_ids,
    fetch_symbols_by_ids,
    combine_symbols,
    get_tracked_symbols,
)


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


class TestFetchCommodityIds:
    """Tests for fetch_commodity_ids function."""

    @patch("extract.get_conn")
    def test_returns_list_of_ids(self, mock_get_conn):
        """Should return list of commodity IDs from database."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_commodity_ids()

        assert result == [1, 2, 3]

    @patch("extract.get_conn")
    def test_returns_empty_list_when_no_data(self, mock_get_conn):
        """Should return empty list when no user commodities exist."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_commodity_ids()

        assert result == []

    @patch("extract.get_conn")
    def test_executes_correct_query(self, mock_get_conn):
        """Should execute SELECT DISTINCT query."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        fetch_commodity_ids()

        mock_cursor.execute.assert_called_once_with(
            "SELECT DISTINCT commodity_id FROM user_commodities;"
        )

    @patch("extract.get_conn")
    def test_closes_cursor_and_connection(self, mock_get_conn):
        """Should properly close cursor and connection."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        fetch_commodity_ids()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestFetchSymbolsByIds:
    """Tests for fetch_symbols_by_ids function."""

    @patch("extract.get_conn")
    def test_returns_symbols_for_ids(self, mock_get_conn):
        """Should return list of symbols for given IDs."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [("GCUSD",), ("CLUSD",), ("SIUSD",)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_symbols_by_ids([1, 2, 3])

        assert result == ["GCUSD", "CLUSD", "SIUSD"]

    @patch("extract.get_conn")
    def test_returns_empty_list_for_empty_input(self, mock_get_conn):
        """Should return empty list when given no IDs."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        result = fetch_symbols_by_ids([])

        assert result == []

    @patch("extract.get_conn")
    def test_executes_query_for_each_id(self, mock_get_conn):
        """Should execute one query per ID."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [("GCUSD",), ("CLUSD",)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        fetch_symbols_by_ids([1, 2])

        assert mock_cursor.execute.call_count == 2
        mock_cursor.execute.assert_any_call(
            "SELECT symbol FROM commodities WHERE commodity_id = %s;", (1,)
        )
        mock_cursor.execute.assert_any_call(
            "SELECT symbol FROM commodities WHERE commodity_id = %s;", (2,)
        )

    @patch("extract.get_conn")
    def test_closes_connection_after_all_queries(self, mock_get_conn):
        """Should close connection after processing all IDs."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("GCUSD",)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        fetch_symbols_by_ids([1, 2, 3])

        mock_conn.close.assert_called_once()


class TestCombineSymbols:
    """Tests for combine_symbols function."""

    @patch("extract.DEFAULT_SYMBOLS", ["GCUSD", "CLUSD"])
    def test_combines_user_and_default_symbols(self):
        """Should combine user symbols with defaults."""
        result = combine_symbols(["SIUSD", "NGUSD"])

        assert result == {"GCUSD", "CLUSD", "SIUSD", "NGUSD"}

    @patch("extract.DEFAULT_SYMBOLS", ["GCUSD", "CLUSD"])
    def test_removes_duplicates(self):
        """Should return unique symbols only."""
        result = combine_symbols(
            ["GCUSD", "SIUSD"])  # GCUSD is also in defaults

        assert result == {"GCUSD", "CLUSD", "SIUSD"}
        assert len(result) == 3

    @patch("extract.DEFAULT_SYMBOLS", ["GCUSD", "CLUSD"])
    def test_returns_defaults_when_user_list_empty(self):
        """Should return defaults when no user symbols."""
        result = combine_symbols([])

        assert result == {"GCUSD", "CLUSD"}

    @patch("extract.DEFAULT_SYMBOLS", [])
    def test_returns_user_symbols_when_no_defaults(self):
        """Should return user symbols when defaults empty."""
        result = combine_symbols(["SIUSD", "NGUSD"])

        assert result == {"SIUSD", "NGUSD"}

    @patch("extract.DEFAULT_SYMBOLS", [])
    def test_returns_empty_set_when_both_empty(self):
        """Should return empty set when both lists empty."""
        result = combine_symbols([])

        assert result == set()


class TestGetTrackedSymbols:
    """Tests for get_tracked_symbols function."""

    @patch("extract.combine_symbols")
    @patch("extract.fetch_symbols_by_ids")
    @patch("extract.fetch_commodity_ids")
    def test_orchestrates_all_functions(self, mock_fetch_ids, mock_fetch_symbols, mock_combine):
        """Should call all helper functions in correct order."""
        mock_fetch_ids.return_value = [1, 2]
        mock_fetch_symbols.return_value = ["GCUSD", "CLUSD"]
        mock_combine.return_value = {"GCUSD", "CLUSD", "SIUSD"}

        result = get_tracked_symbols()

        mock_fetch_ids.assert_called_once()
        mock_fetch_symbols.assert_called_once_with([1, 2])
        mock_combine.assert_called_once_with(["GCUSD", "CLUSD"])
        assert result == {"GCUSD", "CLUSD", "SIUSD"}

    @patch("extract.combine_symbols")
    @patch("extract.fetch_symbols_by_ids")
    @patch("extract.fetch_commodity_ids")
    def test_handles_no_user_commodities(self, mock_fetch_ids, mock_fetch_symbols, mock_combine):
        """Should handle case where no users have commodities."""
        mock_fetch_ids.return_value = []
        mock_fetch_symbols.return_value = []
        mock_combine.return_value = {"GCUSD"}  # Just defaults

        result = get_tracked_symbols()

        mock_fetch_symbols.assert_called_once_with([])
        assert result == {"GCUSD"}
