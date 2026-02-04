"""Tests for historical_load.py"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from historical_load import get_conn, load_data_to_db


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        'recorded_at': ['2023-01-01', '2023-01-02'],
        'open_price': [1800.0, 25.0],
        'day_high': [1820.0, 26.0],
        'day_low': [1790.0, 24.5],
        'price': [1810.0, 25.5],
        'volume': [1000, 2000],
        'change': [10.0, 0.5],
        'change_percentage': [0.55, 2.0],
        'commodity_id': [18, 1]
    })


class TestGetConn:
    """Tests for get_conn function."""

    @patch('historical_load.connect')
    @patch.dict('os.environ', {
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_pass',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    })
    def test_get_conn_calls_connect_with_env_vars(self, mock_connect):
        """Test that get_conn calls connect with correct environment variables."""
        get_conn()

        mock_connect.assert_called_once_with(
            dbname='test_db',
            user='test_user',
            password='test_pass',
            host='localhost',
            port='5432'
        )

    @patch('historical_load.connect')
    @patch.dict('os.environ', {
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_pass',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    })
    def test_get_conn_returns_connection(self, mock_connect):
        """Test that get_conn returns a connection object."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = get_conn()

        assert result == mock_conn


class TestLoadDataToDb:
    """Tests for load_data_to_db function."""

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_creates_cursor(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db creates a cursor."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        mock_conn.cursor.assert_called_once()

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_calls_execute_values(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db calls execute_values."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        mock_execute.assert_called_once()

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_commits_transaction(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db commits the transaction."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        mock_conn.commit.assert_called_once()

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_closes_cursor(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db closes the cursor."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        mock_cursor.close.assert_called_once()

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_closes_connection(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db closes the connection."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        mock_conn.close.assert_called_once()

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_builds_correct_query(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db builds the correct SQL query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        call_args = mock_execute.call_args
        query = call_args[0][1]

        assert 'INSERT INTO market_records' in query
        assert 'VALUES %s' in query

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_passes_correct_tuples(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that load_data_to_db passes correct data tuples."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        load_data_to_db(sample_dataframe)

        call_args = mock_execute.call_args
        tuples = call_args[0][2]

        assert len(tuples) == 2
        assert tuples[0][0] == '2023-01-01'  # First row, first column
        assert tuples[1][0] == '2023-01-02'  # Second row, first column

    @patch('historical_load.execute_values')
    @patch('historical_load.get_conn')
    def test_load_data_closes_resources_on_error(self, mock_get_conn, mock_execute, sample_dataframe):
        """Test that resources are closed even when an error occurs."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        mock_execute.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            load_data_to_db(sample_dataframe)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
