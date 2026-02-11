"""Unit tests for report_extract.py"""
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
import pandas as pd

from report_extract import (
    get_conn,
    get_previous_day_date,
    extract_market_records,
    extract_user_commodities,
)


class TestGetPreviousDayDate:
    """Tests for get_previous_day_date function."""

    def test_returns_date_object(self):
        """Should return a date object."""
        result = get_previous_day_date()
        assert isinstance(result, date)

    def test_returns_yesterday(self):
        """Should return yesterday's date."""
        expected = (datetime.now() - timedelta(days=1)).date()
        result = get_previous_day_date()
        assert result == expected


class TestGetConn:
    """Tests for get_conn function."""

    @patch("report_extract.connect")
    @patch.dict("os.environ", {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    })
    def test_calls_connect_with_env_vars(self, mock_connect):
        """Should call connect with environment variables."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = get_conn()

        mock_connect.assert_called_once()
        assert result == mock_conn


class TestExtractMarketRecords:
    """Tests for extract_market_records function."""

    @patch("report_extract.get_previous_day_date")
    def test_returns_dataframe(self, mock_date):
        """Should return a DataFrame."""
        mock_date.return_value = date(2026, 2, 3)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("symbol",), ("price",)]
        mock_cursor.fetchall.return_value = [("GCUSD", 2000.0)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = extract_market_records(mock_conn)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    @patch("report_extract.get_previous_day_date")
    def test_uses_previous_day_date(self, mock_date):
        """Should filter by previous day's date."""
        test_date = date(2026, 2, 3)
        mock_date.return_value = test_date
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("symbol",)]
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        extract_market_records(mock_conn)

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (test_date,)


class TestExtractUserCommodities:
    """Tests for extract_user_commodities function."""

    def test_returns_dataframe(self):
        """Should return a DataFrame."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("user_name",), ("symbol",), ("buy_price",)]
        mock_cursor.fetchall.return_value = [("alice", "GCUSD", 2000.0)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = extract_user_commodities(mock_conn)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
