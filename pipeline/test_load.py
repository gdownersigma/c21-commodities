"""
Tests for load.py functions
"""

from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

from load import insert_into_db


@pytest.fixture
def sample_df():
    """Sample DataFrame matching market_records schema."""
    return pd.DataFrame([{
        "commodity_id": 1,
        "recorded_at": pd.Timestamp("2026-02-03 14:57:16"),
        "price": 88.19,
        "volume": 68605,
        "day_high": 90.50,
        "day_low": 87.00,
        "change": 1.25,
        "change_percentage": 0.014,
        "open_price": 87.50,
        "previous_close": 86.94,
        "price_avg_50": 85.50,
        "price_avg_200": 48.65,
        "year_high": 121.30,
        "year_low": 28.31,
        "ingested_at": pd.Timestamp("2026-02-03 15:07:34"),
    }])


class TestInsertIntoDb:
    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_executes_insert_query(self, mock_get_conn, mock_execute_batch, sample_df):
        """Should execute INSERT query with execute_batch."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        insert_into_db(sample_df)

        mock_execute_batch.assert_called_once()
        call_args = mock_execute_batch.call_args
        assert "INSERT INTO market_records" in call_args[0][1]

    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_passes_correct_rows(self, mock_get_conn, mock_execute_batch, sample_df):
        """Should pass DataFrame rows as tuples."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        insert_into_db(sample_df)

        call_args = mock_execute_batch.call_args
        rows = call_args[0][2]
        assert len(rows) == 1
        assert rows[0][0] == 1  # commodity_id
        assert rows[0][2] == 88.19  # price

    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_commits_transaction(self, mock_get_conn, mock_execute_batch, sample_df):
        """Should commit after inserting."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        insert_into_db(sample_df)

        mock_conn.commit.assert_called_once()

    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_closes_cursor_and_connection(self, mock_get_conn, mock_execute_batch, sample_df):
        """Should close cursor and connection."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        insert_into_db(sample_df)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_handles_multiple_rows(self, mock_get_conn, mock_execute_batch):
        """Should handle DataFrame with multiple rows."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        df = pd.DataFrame([
            {"commodity_id": 1, "recorded_at": pd.Timestamp.now(), "price": 100,
             "volume": 1000, "day_high": 105, "day_low": 95, "change": 2,
             "change_percentage": 0.02, "open_price": 98, "previous_close": 98,
             "price_avg_50": 99, "price_avg_200": 97, "year_high": 110,
             "year_low": 85, "ingested_at": pd.Timestamp.now()},
            {"commodity_id": 2, "recorded_at": pd.Timestamp.now(), "price": 200,
             "volume": 2000, "day_high": 205, "day_low": 195, "change": 3,
             "change_percentage": 0.015, "open_price": 198, "previous_close": 197,
             "price_avg_50": 199, "price_avg_200": 190, "year_high": 220,
             "year_low": 180, "ingested_at": pd.Timestamp.now()},
        ])

        insert_into_db(df)

        call_args = mock_execute_batch.call_args
        rows = call_args[0][2]
        assert len(rows) == 2

    @patch("load.execute_batch")
    @patch("load.get_conn")
    def test_handles_empty_dataframe(self, mock_get_conn, mock_execute_batch):
        """Should handle empty DataFrame without error."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        df = pd.DataFrame(columns=[
            "commodity_id", "recorded_at", "price", "volume", "day_high",
            "day_low", "change", "change_percentage", "open_price",
            "previous_close", "price_avg_50", "price_avg_200", "year_high",
            "year_low", "ingested_at"
        ])

        insert_into_db(df)

        call_args = mock_execute_batch.call_args
        rows = call_args[0][2]
        assert len(rows) == 0
