"""Test Dashboard."""

import streamlit as st
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Helpers reused across tests
# ---------------------------------------------------------------------------


def _make_commodity_df(ids=None):
    """Return a minimal commodity DataFrame for testing."""
    if ids is None:
        ids = [10, 18, 40]
    rows = []
    for cid, name in zip(ids, ["Brent Crude Oil", "Gold Futures", "Silver Futures"]):
        rows.append({"commodity_id": cid, "commodity_name": name})
    return pd.DataFrame(rows)


def _make_market_df(ids=None, prices=None, changes=None):
    """Return a minimal market DataFrame for testing."""
    if ids is None:
        ids = [10, 18, 40]
    if prices is None:
        prices = [75.50, 1950.00, 24.30]
    if changes is None:
        changes = [1.2, -0.5, 0.8]
    now = datetime.now()
    rows = []
    for cid, price, change in zip(ids, prices, changes):
        rows.append({
            "commodity_id": cid,
            "price": price,
            "change_percentage": change,
            "recorded_at": now
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Unit tests — initialise_session_state
# ---------------------------------------------------------------------------


class TestInitialiseSessionState:
    """Tests for initialise_session_state."""

    def test_sets_defaults(self):
        from dashboard import initialise_session_state

        for key in ["last_page", "user", "num_commodities",
                    "selected_commodities", "subscribed_commodities",
                    "user_commodities", "analysis_commodity_id"]:
            if key in st.session_state:
                del st.session_state[key]

        initialise_session_state()

        assert st.session_state.last_page == "dashboard"
        assert st.session_state.user == {}
        assert st.session_state.num_commodities == 3
        assert len(st.session_state.selected_commodities) == 3
        assert st.session_state.subscribed_commodities == [10, 18, 40]
        assert st.session_state.user_commodities == {}
        assert st.session_state.analysis_commodity_id == -1

    def test_does_not_overwrite_existing(self):
        from dashboard import initialise_session_state
        st.session_state.num_commodities = 7
        st.session_state.user = {"user_name": "Bob"}

        initialise_session_state()

        assert st.session_state.num_commodities == 7
        assert st.session_state.user == {"user_name": "Bob"}

        del st.session_state["num_commodities"]
        del st.session_state["user"]


# ---------------------------------------------------------------------------
# Unit tests — build_sidebar
# ---------------------------------------------------------------------------

class TestBuildSidebar:
    """Tests for build_sidebar."""

    def test_sidebar_hidden_for_guest(self):
        """Guest users should NOT see commodity selectors."""
        from dashboard import build_sidebar

        df = _make_commodity_df()
        st.session_state.user = {}
        st.session_state.num_commodities = 1
        st.session_state.selected_commodities = {}
        st.session_state.subscribed_commodities = [10, 18, 40]

        at = AppTest.from_function(lambda: build_sidebar(df)).run()

        button_labels = [b.label for b in at.button]
        assert "➕ Add" not in button_labels
        assert "➖ Remove" not in button_labels


# ---------------------------------------------------------------------------
# Unit tests — display_combined_graph
# ---------------------------------------------------------------------------

class TestDisplayCombinedGraph:
    """Tests for display_combined_graph."""

    @patch("dashboard.get_market_data_by_ids")
    @patch("dashboard.build_combined_graph")
    def test_calls_build_combined_graph(self, mock_build, mock_market):
        """Should pass commodity + market dataframes to build_combined_graph."""
        from dashboard import display_combined_graph

        mock_market.return_value = _make_market_df()
        df = _make_commodity_df()

        display_combined_graph(df, MagicMock())

        mock_build.assert_called_once()
        call_args = mock_build.call_args
        assert list(call_args[0][0]["commodity_id"]) == [10, 18, 40]

    @patch("dashboard.get_market_data_by_ids")
    @patch("dashboard.build_combined_graph")
    def test_passes_correct_market_data(self, mock_build, mock_market):
        """Market data returned by query should be forwarded."""
        from dashboard import display_combined_graph

        expected_market = _make_market_df([10], [99.0], [1.0])
        mock_market.return_value = expected_market
        df = _make_commodity_df([10])

        display_combined_graph(df, MagicMock())

        actual_market = mock_build.call_args[0][1]
        assert actual_market.equals(expected_market)


# ---------------------------------------------------------------------------
# Unit tests — display_individual_graphs
# ---------------------------------------------------------------------------

class TestDisplayIndividualGraphs:
    """Tests for display_individual_graphs."""

    @patch("dashboard.get_market_data_by_ids")
    @patch("dashboard.build_single_commodity_graph")
    def test_renders_graph_per_commodity(self, mock_build, mock_market):
        """Should call build_single_commodity_graph once per selected commodity."""
        from dashboard import display_individual_graphs

        st.session_state.num_commodities = 2
        st.session_state.selected_commodities = {
            "commodity_0": [10, "Brent Crude Oil"],
            "commodity_1": [18, "Gold Futures"],
        }
        mock_market.return_value = _make_market_df([10], [75.0], [0.5])

        display_individual_graphs(MagicMock())

        assert mock_build.call_count == 2

    @patch("dashboard.get_market_data_by_ids")
    @patch("dashboard.build_single_commodity_graph")
    def test_passes_graph_index(self, mock_build, mock_market):
        """Each graph should receive a unique graph_index."""
        from dashboard import display_individual_graphs

        st.session_state.num_commodities = 2
        st.session_state.selected_commodities = {
            "commodity_0": [10, "Brent Crude Oil"],
            "commodity_1": [18, "Gold Futures"],
        }
        mock_market.return_value = _make_market_df([10])

        display_individual_graphs(MagicMock())

        indices = [call.kwargs.get("graph_index")
                   for call in mock_build.call_args_list]
        assert indices == [0, 1]
