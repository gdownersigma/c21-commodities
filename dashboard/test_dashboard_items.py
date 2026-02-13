"""Tests for dashboard_items.py"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pandas as pd

from dashboard_items import (
    calculate_period_high_low,
    calculate_time_bounds,
    calculate_y_axis_defaults,
    create_multi_line_chart,
    create_single_line_chart,
    display_markdown_title,
    display_title,
    fetch_historical_data_for_multiple,
    fetch_historical_data_if_needed,
    get_period_label,
    logout_button,
    page_redirect,
    render_analysis_button,
    render_metrics_panel,
    render_price_input_css,
    render_price_inputs,
    render_time_range_buttons,
    welcome_message,
    DEFAULT_COMMODITY_IDS,
)


def test_default_commodity_ids_contains_expected():
    """Should contain default commodity IDs."""
    assert 10 in DEFAULT_COMMODITY_IDS
    assert 18 in DEFAULT_COMMODITY_IDS
    assert 40 in DEFAULT_COMMODITY_IDS


def test_calculate_time_bounds_returns_correct_range():
    """Should calculate min/max time bounds from data."""
    data_max = datetime(2026, 2, 13, 12, 0)
    data_min = datetime(2026, 2, 10, 12, 0)

    min_time, max_time, requested = calculate_time_bounds(
        data_max, data_min, 24)

    assert max_time == data_max
    assert min_time >= data_min
    assert requested == data_max - timedelta(hours=24)


def test_calculate_period_high_low_with_data():
    """Should return high and low prices from filtered data."""
    df = pd.DataFrame({
        "price": [100.0, 150.0, 120.0],
        "recorded_at": pd.to_datetime([
            "2026-02-13 10:00", "2026-02-13 11:00", "2026-02-13 12:00"
        ])
    })
    min_time = pd.Timestamp("2026-02-13 09:00")

    high, low = calculate_period_high_low(df, min_time)

    assert high == 150.0
    assert low == 100.0


def test_calculate_period_high_low_empty_filtered():
    """Should use full data when filtered is empty."""
    df = pd.DataFrame({
        "price": [100.0, 150.0],
        "recorded_at": pd.to_datetime(["2026-02-10 10:00", "2026-02-10 11:00"])
    })
    min_time = pd.Timestamp("2026-02-13 09:00")

    high, low = calculate_period_high_low(df, min_time)

    assert high == 150.0
    assert low == 100.0


def test_calculate_y_axis_defaults_adds_padding():
    """Should add padding to y-axis bounds."""
    y_min, y_max = calculate_y_axis_defaults(150.0, 100.0, 125.0)

    assert y_max > 150.0
    assert y_min < 100.0
    assert y_min >= 0


def test_calculate_y_axis_defaults_zero_range():
    """Should handle zero price range."""
    y_min, y_max = calculate_y_axis_defaults(100.0, 100.0, 100.0)

    assert y_max > 100.0
    assert y_min >= 0


def test_get_period_label_known_values():
    """Should return correct labels for known time ranges."""
    assert get_period_label(3) == "3H"
    assert get_period_label(24) == "1D"
    assert get_period_label(168) == "7D"
    assert get_period_label(720) == "30D"


def test_get_period_label_unknown():
    """Should return PERIOD for unknown time ranges."""
    assert get_period_label(999) == "PERIOD"


@patch("dashboard_items.st")
def test_render_time_range_buttons_creates_buttons(mock_st):
    """Should create four time range buttons."""
    mock_st.columns.return_value = [MagicMock() for _ in range(4)]

    render_time_range_buttons("test_key")

    assert mock_st.columns.called
    assert mock_st.button.call_count == 4


@patch("dashboard_items.st")
def test_render_price_input_css_adds_styles(mock_st):
    """Should add custom CSS for price inputs."""
    render_price_input_css()

    mock_st.markdown.assert_called_once()


@patch("dashboard_items.st")
def test_display_markdown_title_renders_html(mock_st):
    """Should render title as HTML."""
    display_markdown_title("Test Title")

    mock_st.markdown.assert_called_once()
    call_args = mock_st.markdown.call_args[0][0]
    assert "Test Title" in call_args


@patch("dashboard_items.st")
def test_display_title_renders_branding(mock_st):
    """Should render Pivot Point branding."""
    display_title()

    assert mock_st.markdown.call_count >= 2
    mock_st.divider.assert_called_once()


@patch("dashboard_items.st")
def test_page_redirect_creates_button(mock_st):
    """Should create redirect button."""
    mock_st.button.return_value = False

    page_redirect("Click here", "pages/test.py")

    mock_st.button.assert_called_once_with("Click here")
    mock_st.switch_page.assert_not_called()
@patch("dashboard_items.st")
def test_page_redirect_switches_page_on_click(mock_st):
    """Should switch page when button clicked."""
    mock_st.button.return_value = True

    page_redirect("Click here", "pages/test.py")

    mock_st.switch_page.assert_called_once_with("pages/test.py")


@patch("dashboard_items.st")
def test_render_price_inputs_returns_values(mock_st):
    """Should return min and max price values."""
    mock_st.number_input.side_effect = [150.0, 100.0]

    y_min, y_max = render_price_inputs(100.0, 150.0, 1.0, "test", 24)

    assert y_min == 100.0
    assert y_max == 150.0


@patch("dashboard_items.st")
def test_render_price_inputs_swaps_if_inverted(mock_st):
    """Should swap values if min > max."""
    mock_st.number_input.side_effect = [50.0, 200.0]

    y_min, y_max = render_price_inputs(100.0, 150.0, 1.0, "test", 24)

    assert y_min <= y_max


@patch("dashboard_items.st")
def test_render_metrics_panel_displays_price(mock_st):
    """Should display current price metric."""
    df = pd.DataFrame({
        "price": [100.0, 110.0],
        "recorded_at": pd.to_datetime(["2026-02-13 10:00", "2026-02-13 11:00"]),
        "change_percentage": [0.0, 10.0]
    })

    render_metrics_panel(df, 110.0, 100.0, "1D")

    mock_st.metric.assert_called_once()


def test_create_single_line_chart_returns_chart():
    """Should return an Altair chart."""
    df = pd.DataFrame({
        "price": [100.0, 110.0],
        "recorded_at": pd.to_datetime(["2026-02-13 10:00", "2026-02-13 11:00"]),
        "change_percentage": [0.0, 10.0]
    })
    min_time = pd.Timestamp("2026-02-13 10:00")
    max_time = pd.Timestamp("2026-02-13 11:00")

    chart = create_single_line_chart(df, min_time, max_time, 95.0, 115.0)

    assert chart is not None


def test_create_multi_line_chart_returns_chart():
    """Should return an Altair chart for multiple commodities."""
    df = pd.DataFrame({
        "price": [100.0, 110.0, 50.0, 55.0],
        "recorded_at": pd.to_datetime([
            "2026-02-13 10:00", "2026-02-13 11:00",
            "2026-02-13 10:00", "2026-02-13 11:00"
        ]),
        "change_percentage": [0.0, 10.0, 0.0, 10.0],
        "commodity_name": ["Gold", "Gold", "Silver", "Silver"]
    })
    min_time = pd.Timestamp("2026-02-13 10:00")
    max_time = pd.Timestamp("2026-02-13 11:00")

    chart = create_multi_line_chart(df, min_time, max_time, 45.0, 115.0)

    assert chart is not None


@patch("dashboard_items.st")
def test_display_markdown_title_handles_bold(mock_st):
    """Should convert **bold** to HTML strong tags."""
    display_markdown_title("**Bold** text")

    call_args = mock_st.markdown.call_args[0][0]
    assert "<strong>Bold</strong>" in call_args


@patch("dashboard_items.st")
@patch("dashboard_items.invoke_historical_lambda")
@patch("dashboard_items.get_commodity_symbol_by_id", return_value="GCUSD")
@patch("dashboard_items.get_connection")
def test_fetch_historical_data_if_needed_fetches(
    _mock_conn, _mock_symbol, mock_lambda, mock_st
):
    """Should fetch historical data for non-default commodities."""
    mock_st.session_state = {}

    fetch_historical_data_if_needed(
        comm_id=99,
        requested_min_time=datetime(2026, 2, 1),
        data_min_time=datetime(2026, 2, 10),
    )

    mock_lambda.assert_called_once_with("GCUSD")
    mock_st.toast.assert_called_once()


@patch("dashboard_items.st")
def test_fetch_historical_data_if_needed_skips_default(mock_st):
    """Should skip fetching for default commodity IDs."""
    mock_st.session_state = {}

    fetch_historical_data_if_needed(
        comm_id=10,
        requested_min_time=datetime(2026, 2, 1),
        data_min_time=datetime(2026, 2, 10),
    )

    mock_st.toast.assert_not_called()


@patch("dashboard_items.st")
@patch("dashboard_items.invoke_historical_lambda")
@patch("dashboard_items.get_commodity_symbol_by_id", return_value="GCUSD")
@patch("dashboard_items.get_connection")
def test_fetch_historical_data_for_multiple(
    mock_conn, _mock_symbol, mock_lambda, mock_st
):
    """Should fetch data for multiple non-default commodities."""
    mock_st.session_state = {}
    mock_conn.return_value = MagicMock()

    chart_df = pd.DataFrame({"commodity_id": [99]})

    fetch_historical_data_for_multiple(
        chart_df,
        requested_min_time=datetime(2026, 2, 1),
        data_min_time=datetime(2026, 2, 10),
    )

    mock_lambda.assert_called_once_with("GCUSD")


@patch("dashboard_items.st")
def test_render_analysis_button_hidden_when_not_logged_in(mock_st):
    """Should not render button when user is not logged in."""
    mock_st.session_state.user = None

    render_analysis_button(1, "test")

    mock_st.button.assert_not_called()


@patch("dashboard_items.st")
def test_render_analysis_button_shown_when_logged_in(mock_st):
    """Should render button when user is logged in."""
    mock_st.session_state.user = {"name": "test"}
    mock_st.button.return_value = False

    render_analysis_button(1, "test")

    mock_st.button.assert_called_once()


@patch("dashboard_items.st")
def test_logout_button_no_click(mock_st):
    """Should show divider even without clicking logout."""
    mock_st.sidebar.button.return_value = False

    logout_button()

    mock_st.sidebar.divider.assert_called_once()


@patch("dashboard_items.st")
def test_welcome_message_displays_name(mock_st):
    """Should display user's name in welcome message."""
    mock_st.session_state.user = {"user_name": "alice"}

    welcome_message()

    mock_st.sidebar.markdown.assert_called_once()
    call_args = mock_st.sidebar.markdown.call_args[0][0]
    assert "alice" in call_args
    mock_st.sidebar.divider.assert_called_once()
