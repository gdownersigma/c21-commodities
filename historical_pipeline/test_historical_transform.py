"""Tests for historical_transform.py"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from historical_transform import (
    change_date_column_to_timestamp,
    remove_vwap_column,
    change_column_names,
    replace_symbol_with_id
)


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        'symbol': ['GCUSD', 'DCUSD'],
        'date': ['2023-01-01', '2023-01-02'],
        'open': [1800.0, 25.0],
        'high': [1820.0, 26.0],
        'low': [1790.0, 24.5],
        'close': [1810.0, 25.5],
        'volume': [1000, 2000],
        'change': [10.0, 0.5],
        'changePercent': [0.55, 2.0],
        'vwap': [1805.0, 25.25]
    })


class TestChangeDateColumnToTimestamp:
    """Tests for change_date_column_to_timestamp function."""

    def test_converts_date_string_to_timestamp(self, sample_dataframe):
        """Test that date strings are converted to timestamps."""
        result = change_date_column_to_timestamp(sample_dataframe)

        assert pd.api.types.is_datetime64_any_dtype(result['date'])

    def test_returns_dataframe(self, sample_dataframe):
        """Test that function returns a DataFrame."""
        result = change_date_column_to_timestamp(sample_dataframe)

        assert isinstance(result, pd.DataFrame)

    def test_preserves_other_columns(self, sample_dataframe):
        """Test that other columns are preserved."""
        original_columns = set(sample_dataframe.columns)
        result = change_date_column_to_timestamp(sample_dataframe)

        assert set(result.columns) == original_columns


class TestRemoveVwapColumn:
    """Tests for remove_vwap_column function."""

    def test_removes_vwap_column(self, sample_dataframe):
        """Test that VWAP column is removed."""
        result = remove_vwap_column(sample_dataframe)

        assert 'vwap' not in result.columns

    def test_returns_dataframe(self, sample_dataframe):
        """Test that function returns a DataFrame."""
        result = remove_vwap_column(sample_dataframe)

        assert isinstance(result, pd.DataFrame)

    def test_handles_missing_vwap_column(self):
        """Test that function handles DataFrame without VWAP column."""
        df = pd.DataFrame({'symbol': ['GCUSD'], 'date': ['2023-01-01']})

        result = remove_vwap_column(df)

        assert isinstance(result, pd.DataFrame)
        assert 'vwap' not in result.columns

    def test_preserves_other_columns(self, sample_dataframe):
        """Test that other columns are preserved."""
        original_columns = set(sample_dataframe.columns) - {'vwap'}
        result = remove_vwap_column(sample_dataframe)

        assert set(result.columns) == original_columns


class TestChangeColumnNames:
    """Tests for change_column_names function."""

    def test_renames_date_to_recorded_at(self, sample_dataframe):
        """Test that 'date' is renamed to 'recorded_at'."""
        result = change_column_names(sample_dataframe)

        assert 'recorded_at' in result.columns
        assert 'date' not in result.columns

    def test_renames_open_to_open_price(self, sample_dataframe):
        """Test that 'open' is renamed to 'open_price'."""
        result = change_column_names(sample_dataframe)

        assert 'open_price' in result.columns
        assert 'open' not in result.columns

    def test_renames_high_to_day_high(self, sample_dataframe):
        """Test that 'high' is renamed to 'day_high'."""
        result = change_column_names(sample_dataframe)

        assert 'day_high' in result.columns
        assert 'high' not in result.columns

    def test_renames_low_to_day_low(self, sample_dataframe):
        """Test that 'low' is renamed to 'day_low'."""
        result = change_column_names(sample_dataframe)

        assert 'day_low' in result.columns
        assert 'low' not in result.columns

    def test_renames_close_to_price(self, sample_dataframe):
        """Test that 'close' is renamed to 'price'."""
        result = change_column_names(sample_dataframe)

        assert 'price' in result.columns
        assert 'close' not in result.columns

    def test_renames_change_percent(self, sample_dataframe):
        """Test that 'changePercent' is renamed to 'change_percentage'."""
        result = change_column_names(sample_dataframe)

        assert 'change_percentage' in result.columns
        assert 'changePercent' not in result.columns

    def test_returns_dataframe(self, sample_dataframe):
        """Test that function returns a DataFrame."""
        result = change_column_names(sample_dataframe)

        assert isinstance(result, pd.DataFrame)


class TestReplaceSymbolWithId:
    """Tests for replace_symbol_with_id function."""

    @patch('historical_transform.get_symbol_id_map')
    def test_replaces_symbol_with_commodity_id(self, mock_get_map, sample_dataframe):
        """Test that symbol is replaced with commodity_id."""
        mock_get_map.return_value = {'GCUSD': 1, 'DCUSD': 2}

        result = replace_symbol_with_id(sample_dataframe)

        assert 'commodity_id' in result.columns
        assert 'symbol' not in result.columns

    @patch('historical_transform.get_symbol_id_map')
    def test_maps_symbols_correctly(self, mock_get_map, sample_dataframe):
        """Test that symbols are mapped to correct IDs."""
        mock_get_map.return_value = {'GCUSD': 1, 'DCUSD': 2}

        result = replace_symbol_with_id(sample_dataframe)

        assert result['commodity_id'].tolist() == [1, 2]

    @patch('historical_transform.get_symbol_id_map')
    def test_returns_dataframe(self, mock_get_map, sample_dataframe):
        """Test that function returns a DataFrame."""
        mock_get_map.return_value = {'GCUSD': 1, 'DCUSD': 2}

        result = replace_symbol_with_id(sample_dataframe)

        assert isinstance(result, pd.DataFrame)

    @patch('historical_transform.get_symbol_id_map')
    def test_handles_unknown_symbol(self, mock_get_map, sample_dataframe):
        """Test that unknown symbols result in NaN commodity_id."""
        mock_get_map.return_value = {'GCUSD': 1}  # Missing DCUSD

        result = replace_symbol_with_id(sample_dataframe)

        assert result['commodity_id'].iloc[0] == 1
        assert pd.isna(result['commodity_id'].iloc[1])
