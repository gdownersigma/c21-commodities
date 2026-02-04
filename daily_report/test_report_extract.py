"""Unit tests for report_extract.py"""
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
import pandas as pd

from report_extract import (
    get_conn,
    get_previous_day_date,
    extract_market_records,
    extract_user_commodities,
    extract_all_users,
    extract_all_commodities,
    extract_previous_day_summary,
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

    @patch("report_extract.load_dotenv")
    @patch("report_extract.connect")
    @patch.dict("os.environ", {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    })
    def test_calls_connect_with_env_vars(self, mock_connect, mock_load_dotenv):
        """Should call connect with environment variables."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = get_conn()

        mock_load_dotenv.assert_called_once()
        mock_connect.assert_called_once()
        assert result == mock_conn


class TestExtractMarketRecords:
    """Tests for extract_market_records function."""

    @patch("report_extract.get_conn")
    @patch("report_extract.get_previous_day_date")
    @patch("report_extract.pd.read_sql_query")
    def test_returns_dataframe(self, mock_read_sql, mock_date, mock_conn):
        """Should return a DataFrame."""
        mock_date.return_value = date(2026, 2, 3)
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_df = pd.DataFrame({"symbol": ["GCUSD"], "price": [2000.0]})
        mock_read_sql.return_value = mock_df

        result = extract_market_records()

        assert isinstance(result, pd.DataFrame)
        mock_connection.close.assert_called_once()

    @patch("report_extract.get_conn")
    @patch("report_extract.get_previous_day_date")
    @patch("report_extract.pd.read_sql_query")
    def test_uses_previous_day_date(self, mock_read_sql, mock_date, mock_conn):
        """Should filter by previous day's date."""
        test_date = date(2026, 2, 3)
        mock_date.return_value = test_date
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_read_sql.return_value = pd.DataFrame()

        extract_market_records()

        call_args = mock_read_sql.call_args
        assert call_args[1]["params"] == (test_date,)


class TestExtractUserCommodities:
    """Tests for extract_user_commodities function."""

    @patch("report_extract.get_conn")
    @patch("report_extract.pd.read_sql_query")
    def test_returns_dataframe(self, mock_read_sql, mock_conn):
        """Should return a DataFrame."""
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_df = pd.DataFrame({
            "user_name": ["alice"],
            "symbol": ["GCUSD"],
            "buy_price": [2000.0]
        })
        mock_read_sql.return_value = mock_df

        result = extract_user_commodities()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_connection.close.assert_called_once()


class TestExtractAllUsers:
    """Tests for extract_all_users function."""

    @patch("report_extract.get_conn")
    @patch("report_extract.pd.read_sql_query")
    def test_returns_dataframe(self, mock_read_sql, mock_conn):
        """Should return a DataFrame."""
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_df = pd.DataFrame({
            "user_id": [1, 2],
            "user_name": ["alice", "bob"],
            "email": ["alice@test.com", "bob@test.com"]
        })
        mock_read_sql.return_value = mock_df

        result = extract_all_users()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_connection.close.assert_called_once()


class TestExtractAllCommodities:
    """Tests for extract_all_commodities function."""

    @patch("report_extract.get_conn")
    @patch("report_extract.pd.read_sql_query")
    def test_returns_dataframe(self, mock_read_sql, mock_conn):
        """Should return a DataFrame."""
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_df = pd.DataFrame({
            "commodity_id": [1, 2, 3],
            "symbol": ["GCUSD", "SIUSD", "BZUSD"],
            "commodity_name": ["Gold", "Silver", "Brent Crude"],
            "currency": ["USD", "USD", "USD"]
        })
        mock_read_sql.return_value = mock_df

        result = extract_all_commodities()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        mock_connection.close.assert_called_once()


class TestExtractPreviousDaySummary:
    """Tests for extract_previous_day_summary function."""

    @patch("report_extract.get_conn")
    @patch("report_extract.get_previous_day_date")
    @patch("report_extract.pd.read_sql_query")
    def test_returns_dataframe(self, mock_read_sql, mock_date, mock_conn):
        """Should return a DataFrame with summary statistics."""
        mock_date.return_value = date(2026, 2, 3)
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_df = pd.DataFrame({
            "symbol": ["GCUSD"],
            "commodity_name": ["Gold"],
            "record_count": [57],
            "avg_price": [2000.0],
            "min_price": [1950.0],
            "max_price": [2050.0],
            "avg_change_percentage": [0.5],
            "total_volume": [1000000]
        })
        mock_read_sql.return_value = mock_df

        result = extract_previous_day_summary()

        assert isinstance(result, pd.DataFrame)
        assert "record_count" in result.columns
        assert "avg_price" in result.columns
        mock_connection.close.assert_called_once()

    @patch("report_extract.get_conn")
    @patch("report_extract.get_previous_day_date")
    @patch("report_extract.pd.read_sql_query")
    def test_empty_when_no_data(self, mock_read_sql, mock_date, mock_conn):
        """Should return empty DataFrame when no data for date."""
        mock_date.return_value = date(2020, 1, 1)
        mock_connection = MagicMock()
        mock_conn.return_value = mock_connection
        mock_read_sql.return_value = pd.DataFrame()

        result = extract_previous_day_summary()

        assert isinstance(result, pd.DataFrame)
        assert result.empty
