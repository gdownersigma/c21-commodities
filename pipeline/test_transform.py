"""
Tests for transform.py functions
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from transform import (
    rename_columns,
    unix_to_datetime,
    remove_dead_columns,
    create_ingested_column,
    get_symbol_id_map,
    replace_symbol_with_id,
    reorder_columns,
)


@pytest.fixture
def sample_raw_df():
    """Sample DataFrame mimicking raw API response."""
    return pd.DataFrame([{
        "symbol": "GCUSD",
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
    }])


class TestRenameColumns:
    def test_renames_columns_correctly(self, sample_raw_df):
        result = rename_columns(sample_raw_df)

        assert "recorded_at" in result.columns
        assert "timestamp" not in result.columns
        assert "day_high" in result.columns
        assert "dayHigh" not in result.columns
        assert result["day_high"].iloc[0] == 3401.1


class TestUnixToDatetime:
    def test_converts_and_preserves_precision(self):
        df = pd.DataFrame([{"timestamp": 0}])

        result = unix_to_datetime(df, "timestamp")

        assert result["timestamp"].iloc[0] == pd.Timestamp("1970-01-01")
        assert result["timestamp"].dtype == "datetime64[s]"


class TestRemoveDeadColumns:
    def test_removes_dead_columns(self, sample_raw_df):
        result = remove_dead_columns(sample_raw_df)

        assert "marketCap" not in result.columns
        assert "exchange" not in result.columns
        assert "symbol" in result.columns

    def test_handles_missing_columns(self):
        df = pd.DataFrame([{"symbol": "GCUSD"}])
        result = remove_dead_columns(df)
        assert "symbol" in result.columns


class TestCreateIngestedColumn:
    def test_adds_datetime_column(self):
        df = pd.DataFrame([{"symbol": "GCUSD"}, {"symbol": "CLUSD"}])

        result = create_ingested_column(df)

        assert "ingested_at" in result.columns
        assert result["ingested_at"].dtype == "datetime64[s]"
        assert result["ingested_at"].nunique() == 1


class TestGetSymbolIdMap:
    @patch("transform.get_conn")
    def test_returns_symbol_to_id_mapping(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("GCUSD", 1), ("CLUSD", 2), ("SIUSD", 3)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = get_symbol_id_map()

        assert result == {"GCUSD": 1, "CLUSD": 2, "SIUSD": 3}
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestReplaceSymbolWithId:
    @patch("transform.get_symbol_id_map")
    def test_replaces_symbol_with_id(self, mock_map):
        mock_map.return_value = {"GCUSD": 1, "CLUSD": 2}
        df = pd.DataFrame([{"symbol": "GCUSD", "price": 100}, {
                          "symbol": "CLUSD", "price": 80}])

        result = replace_symbol_with_id(df)

        assert "commodity_id" in result.columns
        assert "symbol" not in result.columns
        assert list(result["commodity_id"]) == [1, 2]


class TestReorderColumns:
    def test_reorders_to_schema(self):
        df = pd.DataFrame([{
            "price": 100, "commodity_id": 1, "volume": 500,
            "recorded_at": pd.Timestamp.now(), "day_high": 105, "day_low": 95,
            "change": 2, "change_percentage": 0.02, "open_price": 98,
            "previous_close": 98, "price_avg_50": 99, "price_avg_200": 97,
            "year_high": 110, "year_low": 85, "ingested_at": pd.Timestamp.now(),
        }])

        result = reorder_columns(df)

        assert result.columns[0] == "commodity_id"
        assert result.columns[-1] == "ingested_at"
        assert len(result.columns) == 15


class TestFullTransformation:
    @patch("transform.get_symbol_id_map")
    def test_transforms_raw_to_final(self, mock_map, sample_raw_df):
        mock_map.return_value = {"GCUSD": 42}

        df = rename_columns(sample_raw_df)
        df = unix_to_datetime(df, "recorded_at")
        df = remove_dead_columns(df)
        df = create_ingested_column(df)
        df = replace_symbol_with_id(df)
        df = reorder_columns(df)

        assert len(df.columns) == 15
        assert df["commodity_id"].iloc[0] == 42
        assert "symbol" not in df.columns
        assert "marketCap" not in df.columns
