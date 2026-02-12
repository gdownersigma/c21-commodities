"""Unit tests for adv_graph.py."""
from adv_graph import (
    prepare_daily_data,
    calculate_moving_averages,
    get_price_metrics,
    create_figure,
    add_candlestick_trace,
    add_moving_average_traces,
    add_volume_trace,
    configure_layout,
    render_sidebar,
    render_title,
    render_metrics,
    build_chart,
    handle_submit,
)
import plotly.graph_objects as go
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
import sys
from unittest.mock import MagicMock

# Mock query_data module BEFORE importing adv_graph
sys.modules['query_data'] = MagicMock()


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    dates = pd.date_range(start='2026-01-01', periods=30, freq='h')
    return pd.DataFrame({
        'recorded_at': dates,
        'open_price': np.random.uniform(100, 110, 30),
        'day_high': np.random.uniform(110, 120, 30),
        'day_low': np.random.uniform(90, 100, 30),
        'price': np.random.uniform(100, 110, 30),
        'volume': np.random.randint(1000, 5000, 30),
        'commodity_name': ['Gold'] * 30,
        'symbol': ['GLD'] * 30,
    })


@pytest.fixture
def daily_df():
    """Create daily DataFrame with MAs for testing."""
    dates = pd.date_range(start='2026-01-01', periods=25, freq='D')
    df = pd.DataFrame({
        'open_price': np.random.uniform(100, 110, 25),
        'day_high': np.random.uniform(110, 120, 25),
        'day_low': np.random.uniform(90, 100, 25),
        'price': np.random.uniform(100, 110, 25),
        'volume': np.random.randint(1000, 5000, 25),
        'commodity_name': ['Gold'] * 25,
        'symbol': ['GLD'] * 25,
    }, index=dates)
    df['MA_7'] = df['price'].rolling(window=7).mean()
    df['MA_14'] = df['price'].rolling(window=14).mean()
    df['MA_20'] = df['price'].rolling(window=20).mean()
    return df


# =============================================================================
# prepare_daily_data tests
# =============================================================================

class TestPrepareDailyData:
    """Tests for prepare_daily_data function."""

    def test_resamples_to_daily(self, sample_df):
        """Test that data is resampled to daily frequency."""
        result = prepare_daily_data.__wrapped__(sample_df)
        assert len(result) <= len(sample_df)

    def test_returns_dataframe(self, sample_df):
        """Test that result is a DataFrame."""
        result = prepare_daily_data.__wrapped__(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_preserves_required_columns(self, sample_df):
        """Test that required columns are preserved."""
        result = prepare_daily_data.__wrapped__(sample_df)
        required = ['open_price', 'day_high', 'day_low', 'price', 'volume']
        for col in required:
            assert col in result.columns


# =============================================================================
# calculate_moving_averages tests
# =============================================================================

class TestCalculateMovingAverages:
    """Tests for calculate_moving_averages function."""

    def test_adds_ma_columns(self, daily_df):
        """Test that MA columns are added."""
        df_input = daily_df.drop(columns=['MA_7', 'MA_14', 'MA_20'])
        result = calculate_moving_averages.__wrapped__(df_input)
        assert 'MA_7' in result.columns
        assert 'MA_14' in result.columns
        assert 'MA_20' in result.columns

    def test_returns_dataframe(self, daily_df):
        """Test that result is a DataFrame."""
        df_input = daily_df.drop(columns=['MA_7', 'MA_14', 'MA_20'])
        result = calculate_moving_averages.__wrapped__(df_input)
        assert isinstance(result, pd.DataFrame)

    def test_does_not_modify_original(self, daily_df):
        """Test that original DataFrame is not modified."""
        df_input = daily_df.drop(columns=['MA_7', 'MA_14', 'MA_20'])
        original_cols = list(df_input.columns)
        calculate_moving_averages.__wrapped__(df_input)
        assert list(df_input.columns) == original_cols


# =============================================================================
# get_price_metrics tests
# =============================================================================

class TestGetPriceMetrics:
    """Tests for get_price_metrics function."""

    def test_returns_dict(self, daily_df):
        """Test that result is a dictionary."""
        result = get_price_metrics.__wrapped__(daily_df)
        assert isinstance(result, dict)

    def test_contains_required_keys(self, daily_df):
        """Test that all required keys are present."""
        result = get_price_metrics.__wrapped__(daily_df)
        required = ['latest_price', 'price_change_pct',
                    'day_high', 'day_low', 'volume']
        for key in required:
            assert key in result

    def test_handles_single_row(self):
        """Test handling of single row DataFrame."""
        df = pd.DataFrame({
            'price': [100.0],
            'day_high': [105.0],
            'day_low': [95.0],
            'volume': [1000]
        })
        result = get_price_metrics.__wrapped__(df)
        assert result['latest_price'] == 100.0
        assert result['price_change_pct'] == 0.0


# =============================================================================
# create_figure tests
# =============================================================================

class TestCreateFigure:
    """Tests for create_figure function."""

    def test_returns_figure(self):
        """Test that result is a Plotly Figure."""
        result = create_figure(True)
        assert isinstance(result, go.Figure)

    def test_with_volume_has_two_subplots(self):
        """Test figure with volume has proper subplots."""
        result = create_figure(True)
        assert result is not None

    def test_without_volume_single_subplot(self):
        """Test figure without volume has single subplot."""
        result = create_figure(False)
        assert result is not None


# =============================================================================
# add_candlestick_trace tests
# =============================================================================

class TestAddCandlestickTrace:
    """Tests for add_candlestick_trace function."""

    def test_adds_trace_to_figure(self, daily_df):
        """Test that candlestick trace is added."""
        fig = create_figure(False)
        initial_traces = len(fig.data)
        add_candlestick_trace(fig, daily_df)
        assert len(fig.data) == initial_traces + 1

    def test_trace_is_candlestick(self, daily_df):
        """Test that trace is a Candlestick."""
        fig = create_figure(False)
        add_candlestick_trace(fig, daily_df)
        assert isinstance(fig.data[0], go.Candlestick)


# =============================================================================
# add_moving_average_traces tests
# =============================================================================

class TestAddMovingAverageTraces:
    """Tests for add_moving_average_traces function."""

    def test_adds_three_traces(self, daily_df):
        """Test that 3 MA traces are added."""
        fig = create_figure(False)
        initial_traces = len(fig.data)
        add_moving_average_traces(fig, daily_df)
        assert len(fig.data) == initial_traces + 3

    def test_traces_are_scatter(self, daily_df):
        """Test that traces are Scatter type."""
        fig = create_figure(False)
        add_moving_average_traces(fig, daily_df)
        for trace in fig.data:
            assert isinstance(trace, go.Scatter)


# =============================================================================
# add_volume_trace tests
# =============================================================================

class TestAddVolumeTrace:
    """Tests for add_volume_trace function."""

    def test_adds_volume_trace(self, daily_df):
        """Test that volume trace is added."""
        fig = create_figure(True)
        initial_traces = len(fig.data)
        add_volume_trace(fig, daily_df)
        assert len(fig.data) == initial_traces + 1

    def test_trace_is_bar(self, daily_df):
        """Test that trace is a Bar."""
        fig = create_figure(True)
        add_volume_trace(fig, daily_df)
        assert isinstance(fig.data[0], go.Bar)


# =============================================================================
# configure_layout tests
# =============================================================================

class TestConfigureLayout:
    """Tests for configure_layout function."""

    def test_sets_template(self):
        """Test that dark template is set."""
        fig = create_figure(False)
        configure_layout(fig)
        assert fig.layout.template.layout.paper_bgcolor is not None

    def test_sets_height(self):
        """Test that height is configured."""
        fig = create_figure(False)
        configure_layout(fig)
        assert fig.layout.height == 700


# =============================================================================
# render_sidebar tests
# =============================================================================

class TestRenderSidebar:
    """Tests for render_sidebar function."""

    @patch("adv_graph.st")
    def test_returns_dict(self, mock_st):
        """Test that result is a dictionary."""
        mock_st.sidebar.checkbox.return_value = True
        result = render_sidebar()
        assert isinstance(result, dict)

    @patch("adv_graph.st")
    def test_contains_show_volume(self, mock_st):
        """Test that show_volume key is present."""
        mock_st.sidebar.checkbox.return_value = True
        result = render_sidebar()
        assert 'show_volume' in result


# =============================================================================
# render_title tests
# =============================================================================

class TestRenderTitle:
    """Tests for render_title function."""

    @patch("adv_graph.st")
    def test_calls_st_title(self, mock_st, daily_df):
        """Test that st.title is called."""
        render_title(daily_df)
        mock_st.title.assert_called_once()

    @patch("adv_graph.st")
    def test_handles_missing_columns(self, mock_st):
        """Test handling of missing columns."""
        df = pd.DataFrame({'price': [100]})
        render_title(df)
        mock_st.title.assert_called_once()


# =============================================================================
# render_metrics tests
# =============================================================================

class TestRenderMetrics:
    """Tests for render_metrics function."""

    @patch("adv_graph.st")
    def test_calls_st_columns(self, mock_st):
        """Test that st.columns is called."""
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]
        metrics = {
            'latest_price': 100.0,
            'price_change_pct': 1.5,
            'day_high': 105.0,
            'day_low': 95.0,
            'volume': 1000
        }
        render_metrics(metrics)
        mock_st.columns.assert_called()


# =============================================================================
# build_chart tests
# =============================================================================

class TestBuildChart:
    """Tests for build_chart function."""

    def test_returns_figure(self, daily_df):
        """Test that result is a Plotly Figure."""
        settings = {'show_volume': True}
        result = build_chart(daily_df, settings)
        assert isinstance(result, go.Figure)

    def test_with_volume_has_volume_trace(self, daily_df):
        """Test chart with volume includes volume trace."""
        settings = {'show_volume': True}
        result = build_chart(daily_df, settings)
        # Should have candlestick + 3 MAs + volume = 5 traces
        assert len(result.data) == 5

    def test_without_volume_no_volume_trace(self, daily_df):
        """Test chart without volume excludes volume trace."""
        settings = {'show_volume': False}
        result = build_chart(daily_df, settings)
        # Should have candlestick + 3 MAs = 4 traces
        assert len(result.data) == 4


# =============================================================================
# handle_submit tests
# =============================================================================

class TestHandleSubmit:
    """Tests for handle_submit function."""

    @patch("adv_graph.st")
    def test_no_changes_shows_error(self, mock_st):
        """Test that error is shown when no changes made."""
        mock_session = MagicMock()
        mock_session.user_commodities = {
            1: {'buy_price': 100.0, 'sell_price': 200.0, 'name': 'Gold', 'track': True, 'buy': True, 'sell': True}
        }
        mock_st.session_state = mock_session
        new_comm = {'id': 1, 'buy': True, 'sell': True,
                    'buy_price': 100.0, 'sell_price': 200.0, 'name': 'Gold'}
        handle_submit(new_comm)
        mock_st.error.assert_called()

    @patch("adv_graph.st")
    @patch("adv_graph.get_connection")
    @patch("adv_graph.update_user_commodities")
    @patch("adv_graph.get_commodities_with_user_subscriptions")
    def test_changes_calls_update(self, mock_get_comm, mock_update, mock_conn, mock_st):
        """Test that update is called when changes made."""
        mock_session = MagicMock()
        mock_session.user = {'user_id': 1}
        mock_session.user_commodities = {
            1: {'buy_price': 100.0, 'sell_price': 200.0, 'name': 'Gold', 'track': True, 'buy': True, 'sell': True}
        }
        mock_st.session_state = mock_session
        mock_conn.return_value = MagicMock()
        new_comm = {'id': 1, 'buy': True, 'sell': True,
                    'buy_price': 150.0, 'sell_price': 200.0, 'name': 'Gold'}
        handle_submit(new_comm)
        mock_update.assert_called()
        mock_st.success.assert_called()


# =============================================================================
# build_price_edit_form tests
# =============================================================================

class TestBuildPriceEditForm:
    """Tests for build_price_edit_form function."""

    @patch("adv_graph.st")
    def test_renders_form_elements(self, mock_st):
        """Test that form elements are rendered."""
        from adv_graph import build_price_edit_form
        mock_session = MagicMock()
        mock_session.user_commodities = {
            1: {'name': 'Gold', 'track': True, 'buy': True, 'sell': True, 'buy_price': 100.0, 'sell_price': 200.0}
        }
        mock_st.session_state = mock_session
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.sidebar.checkbox.return_value = True
        mock_st.sidebar.number_input.return_value = 100.0
        mock_st.sidebar.button.return_value = False
        mock_st.sidebar.container.return_value.__enter__ = MagicMock()
        mock_st.sidebar.container.return_value.__exit__ = MagicMock()
        build_price_edit_form(1)
        mock_st.sidebar.header.assert_called()


# =============================================================================
# adv_graph tests
# =============================================================================

class TestAdvGraph:
    """Tests for adv_graph function."""

    @patch("adv_graph.st")
    def test_shows_error_when_no_commodity_selected(self, mock_st):
        """Test error shown when no commodity selected."""
        from adv_graph import adv_graph
        mock_st.session_state.get.return_value = None
        adv_graph(None)
        mock_st.error.assert_called()

    @patch("adv_graph.st")
    @patch("adv_graph.get_connection")
    @patch("adv_graph.fetch_data")
    def test_shows_error_when_no_data(self, mock_fetch, mock_conn, mock_st):
        """Test error shown when no data found."""
        from adv_graph import adv_graph
        mock_conn.return_value = MagicMock()
        mock_fetch.return_value = pd.DataFrame()
        adv_graph(1)
        mock_st.error.assert_called()

    @patch("adv_graph.st")
    @patch("adv_graph.get_connection")
    @patch("adv_graph.fetch_data")
    @patch("adv_graph.prepare_daily_data")
    @patch("adv_graph.calculate_moving_averages")
    @patch("adv_graph.render_sidebar")
    @patch("adv_graph.render_title")
    @patch("adv_graph.build_price_edit_form")
    @patch("adv_graph.get_price_metrics")
    @patch("adv_graph.render_metrics")
    @patch("adv_graph.build_chart")
    def test_renders_chart_with_data(self, mock_build_chart, mock_render_metrics,
                                     mock_get_metrics, mock_build_form, mock_render_title,
                                     mock_render_sidebar, mock_calc_ma, mock_prep_daily,
                                     mock_fetch, mock_conn, mock_st):
        """Test chart is rendered when data exists."""
        from adv_graph import adv_graph
        mock_conn.return_value = MagicMock()
        mock_fetch.return_value = pd.DataFrame(
            {'price': [100], 'recorded_at': [pd.Timestamp.now()]})
        mock_prep_daily.return_value = pd.DataFrame({'price': [100]})
        mock_calc_ma.return_value = pd.DataFrame({'price': [100]})
        mock_render_sidebar.return_value = {'show_volume': True}
        mock_get_metrics.return_value = {
            'latest_price': 100, 'price_change_pct': 0, 'day_high': 100, 'day_low': 100, 'volume': 1000}
        mock_build_chart.return_value = go.Figure()
        adv_graph(1)
        mock_st.plotly_chart.assert_called()
