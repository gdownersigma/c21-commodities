"""Unit tests for news.py helper functions."""

from pages.news import (
    identify_commodity,
    auto_tag_article,
    parse_date,
    deduplicate_news,
    filter_news,
    render_tags,
    process_news_data,
    load_css,
    fetch_general_news,
    fetch_stock_news,
    fetch_commodity_prices,
    render_news_card,
    render_sidebar,
    render_news_feed_tab,
    render_prices_tab,
    render_statistics_tab,
    render_footer,
    main,
)
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from requests.exceptions import RequestException

import pytest


# =============================================================================
# identify_commodity tests
# =============================================================================

class TestIdentifyCommodity:
    """Tests for identify_commodity function."""

    @pytest.mark.parametrize("text, expected", [
        ("Gold prices surge amid inflation fears", ["Gold"]),
        ("Silver and gold rally together", ["Gold", "Silver"]),
        ("Copper futures hit record high", ["Copper"]),
        ("Wheat harvest delayed by drought", ["Wheat"]),
        ("Oat prices rise on cereal demand", ["Oats"]),
        ("GOLD BULLION DEMAND INCREASES", ["Gold"]),  # Case insensitive
    ])
    def test_identifies_single_and_multiple_commodities(self, text, expected):
        """Test commodity identification from text."""
        result = identify_commodity(text)
        assert result == expected

    def test_returns_general_when_no_match(self):
        """Test fallback to General when no commodities found."""
        result = identify_commodity("Stock market news today")
        assert result == ["General"]

    def test_empty_string_returns_general(self):
        """Test empty string returns General."""
        result = identify_commodity("")
        assert result == ["General"]

    def test_none_input_returns_general(self):
        """Test None input returns General."""
        result = identify_commodity(None)
        assert result == ["General"]


# =============================================================================
# auto_tag_article tests
# =============================================================================

class TestAutoTagArticle:
    """Tests for auto_tag_article function."""

    @pytest.mark.parametrize("text, expected_tags", [
        ("Supply shortage impacts market", ["Supply", "Market"]),
        ("Federal Reserve raises interest rate", ["Policy"]),
        ("Drought conditions worsen for farmers", ["Weather"]),
        ("Russia-Ukraine conflict affects exports", ["Geopolitical"]),
        ("Dollar strengthens against euro", ["Currency"]),
        ("Import demand surges in Asia", ["Demand"]),
    ])
    def test_identifies_tags_from_keywords(self, text, expected_tags):
        """Test tag identification from text."""
        result = auto_tag_article(text)
        for tag in expected_tags:
            assert tag in result

    def test_returns_market_when_no_match(self):
        """Test fallback to Market when no tags found."""
        result = auto_tag_article("Random unrelated text here")
        assert result == ["Market"]

    def test_case_insensitive(self):
        """Test that tagging is case insensitive."""
        result = auto_tag_article("FEDERAL RESERVE POLICY ANNOUNCEMENT")
        assert "Policy" in result

    def test_none_input_returns_market(self):
        """Test None input returns Market."""
        result = auto_tag_article(None)
        assert result == ["Market"]


# =============================================================================
# parse_date tests
# =============================================================================

class TestParseDate:
    """Tests for parse_date function."""

    def test_parses_iso_format_with_z(self):
        """Test parsing ISO format with Z timezone."""
        result = parse_date("2026-02-10T14:30:00Z")
        assert result == ("2026-02-10", "14:30")

    def test_parses_iso_format_with_offset(self):
        """Test parsing ISO format with timezone offset."""
        result = parse_date("2026-02-10T14:30:00+00:00")
        assert result == ("2026-02-10", "14:30")

    def test_returns_current_time_for_invalid_date(self):
        """Test fallback to current time for invalid date."""
        mock_now = datetime(2026, 6, 15, 10, 30, 0)
        with patch('pages.news.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            result = parse_date("invalid-date")
        assert result == ("2026-06-15", "10:30")

    def test_returns_current_time_for_empty_string(self):
        """Test fallback to current time for empty string."""
        mock_now = datetime(2026, 6, 15, 10, 30, 0)
        with patch('pages.news.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = parse_date("")
        assert result == ("2026-06-15", "10:30")

    def test_returns_current_time_for_none(self):
        """Test fallback to current time for None."""
        mock_now = datetime(2026, 6, 15, 10, 30, 0)
        with patch('pages.news.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = parse_date(None)
        assert result == ("2026-06-15", "10:30")


# =============================================================================
# deduplicate_news tests
# =============================================================================

class TestDeduplicateNews:
    """Tests for deduplicate_news function."""

    def test_removes_duplicate_urls(self):
        """Test removal of items with duplicate URLs."""
        news = [
            {"url": "http://example.com/1", "title": "Article One"},
            {"url": "http://example.com/1", "title": "Article Two"},
            {"url": "http://example.com/2", "title": "Article Three"},
        ]
        result = deduplicate_news(news)
        assert len(result) == 2

    def test_removes_duplicate_titles(self):
        """Test removal of items with duplicate titles."""
        news = [
            {"url": "http://example.com/1", "title": "Same Title"},
            {"url": "http://example.com/2", "title": "Same Title"},
            {"url": "http://example.com/3", "title": "Different Title"},
        ]
        result = deduplicate_news(news)
        assert len(result) == 2

    def test_title_comparison_case_insensitive(self):
        """Test that title comparison is case insensitive."""
        news = [
            {"url": "http://example.com/1", "title": "Gold Prices Rise"},
            {"url": "http://example.com/2", "title": "gold prices rise"},
        ]
        result = deduplicate_news(news)
        assert len(result) == 1

    def test_empty_list_returns_empty(self):
        """Test empty input returns empty list."""
        result = deduplicate_news([])
        assert result == []

    def test_preserves_order(self):
        """Test that first occurrence is preserved."""
        news = [
            {"url": "http://example.com/1", "title": "First"},
            {"url": "http://example.com/2", "title": "Second"},
        ]
        result = deduplicate_news(news)
        assert result[0]["title"] == "First"


# =============================================================================
# filter_news tests
# =============================================================================

class TestFilterNews:
    """Tests for filter_news function."""

    @pytest.fixture
    def sample_news(self):
        """Sample processed news for testing."""
        return [
            {"date": "2026-02-10", "time": "14:00",
                "commodities": ["Gold"], "tags": ["Market", "Policy"]},
            {"date": "2026-02-10", "time": "13:00",
                "commodities": ["Silver"], "tags": ["Supply"]},
            {"date": "2026-02-09", "time": "12:00",
                "commodities": ["Copper"], "tags": ["Demand"]},
            {"date": "2026-02-10", "time": "15:00",
                "commodities": ["General"], "tags": ["Market"]},
        ]

    def test_filters_out_general_commodities(self, sample_news):
        """Test that General commodities are filtered out."""
        result = filter_news(sample_news, "All Commodities", [])
        assert all(a["commodities"] != ["General"] for a in result)

    def test_filters_by_commodity(self, sample_news):
        """Test filtering by specific commodity."""
        result = filter_news(sample_news, "Gold", [])
        assert len(result) == 1
        assert result[0]["commodities"] == ["Gold"]

    def test_filters_by_tags(self, sample_news):
        """Test filtering by tags."""
        result = filter_news(sample_news, "All Commodities", ["Supply"])
        assert len(result) == 1
        assert "Supply" in result[0]["tags"]

    def test_sorts_by_date_descending(self, sample_news):
        """Test that results are sorted by date/time descending."""
        result = filter_news(sample_news, "All Commodities", [])
        dates = [(a["date"], a["time"]) for a in result]
        assert dates == sorted(dates, reverse=True)

    def test_empty_input_returns_empty(self):
        """Test empty input returns empty list."""
        result = filter_news([], "All Commodities", [])
        assert result == []


# =============================================================================
# render_tags tests
# =============================================================================

class TestRenderTags:
    """Tests for render_tags function."""

    def test_renders_known_tags_with_colors(self):
        """Test that known tags get proper CSS classes."""
        result = render_tags(["Supply", "Demand"])
        assert "tag-supply" in result
        assert "tag-demand" in result

    def test_renders_unknown_tags_with_default(self):
        """Test that unknown tags get default CSS class."""
        result = render_tags(["UnknownTag"])
        assert "tag-default" in result

    def test_empty_list_returns_empty_string(self):
        """Test empty list returns empty string."""
        result = render_tags([])
        assert result == ""


# =============================================================================
# process_news_data tests
# =============================================================================

class TestProcessNewsData:
    """Tests for process_news_data function."""

    def test_processes_single_item(self):
        """Test processing a single news item."""
        raw = [{"title": "Gold prices rise", "text": "Gold is up",
                "publishedDate": "2026-02-10T10:00:00Z", "site": "News Site", "url": "http://example.com"}]
        result = process_news_data(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Gold prices rise"
        assert result[0]["source"] == "News Site"
        assert "Gold" in result[0]["commodities"]

    def test_handles_missing_fields(self):
        """Test handling items with missing fields."""
        raw = [{}]
        result = process_news_data(raw)
        assert len(result) == 1
        assert result[0]["title"] == ""
        assert result[0]["url"] == "#"

    def test_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        long_text = "x" * 600
        raw = [{"text": long_text}]
        result = process_news_data(raw)
        assert len(result[0]["description"]) == 503  # 500 + "..."

    def test_empty_list_returns_empty(self):
        """Test empty input returns empty list."""
        result = process_news_data([])
        assert result == []

    def test_uses_content_if_text_missing(self):
        """Test that content field is used when text is missing."""
        raw = [{"content": "Article content"}]
        result = process_news_data(raw)
        assert result[0]["description"] == "Article content"


# =============================================================================
# load_css tests
# =============================================================================

class TestLoadCss:
    """Tests for load_css function."""

    def test_returns_style_tags(self):
        """Test that CSS is wrapped in style tags."""
        with patch("builtins.open", mock_open(read_data=".test { color: red; }")):
            result = load_css()
        assert "<style>" in result
        assert "</style>" in result
        assert ".test { color: red; }" in result


# =============================================================================
# fetch_general_news tests
# =============================================================================

class TestFetchGeneralNews:
    """Tests for fetch_general_news function."""

    @patch("pages.news.requests.get")
    def test_returns_list_on_success(self, mock_get):
        """Test successful response returns list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"title": "News"}]
        result = fetch_general_news.__wrapped__("api_key")
        assert result == [{"title": "News"}]

    @patch("pages.news.requests.get")
    def test_returns_empty_on_non_200(self, mock_get):
        """Test non-200 status returns empty list."""
        mock_get.return_value.status_code = 500
        result = fetch_general_news.__wrapped__("api_key")
        assert result == []

    @patch("pages.news.requests.get")
    def test_returns_empty_on_request_exception(self, mock_get):
        """Test request exception returns empty list."""
        mock_get.side_effect = RequestException()
        result = fetch_general_news.__wrapped__("api_key")
        assert result == []

    @patch("pages.news.requests.get")
    def test_returns_empty_on_non_list_response(self, mock_get):
        """Test non-list JSON returns empty list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"error": "invalid"}
        result = fetch_general_news.__wrapped__("api_key")
        assert result == []


# =============================================================================
# fetch_stock_news tests
# =============================================================================

class TestFetchStockNews:
    """Tests for fetch_stock_news function."""

    @patch("pages.news.requests.get")
    def test_returns_list_on_success(self, mock_get):
        """Test successful response returns list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"title": "Stock News"}]
        result = fetch_stock_news.__wrapped__("api_key", ["GLD"])
        assert result == [{"title": "Stock News"}]

    @patch("pages.news.requests.get")
    def test_returns_empty_on_non_200(self, mock_get):
        """Test non-200 status returns empty list."""
        mock_get.return_value.status_code = 404
        result = fetch_stock_news.__wrapped__("api_key", ["GLD"])
        assert result == []

    @patch("pages.news.requests.get")
    def test_returns_empty_on_exception(self, mock_get):
        """Test exception returns empty list."""
        mock_get.side_effect = ValueError()
        result = fetch_stock_news.__wrapped__("api_key", ["GLD"])
        assert result == []


# =============================================================================
# fetch_commodity_prices tests
# =============================================================================

class TestFetchCommodityPrices:
    """Tests for fetch_commodity_prices function."""

    @patch("pages.news.requests.get")
    def test_returns_prices_on_success(self, mock_get):
        """Test successful response returns prices dict."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"symbol": "GCUSD", "price": 2000,
                "change": 10, "changesPercentage": 0.5}
        ]
        result = fetch_commodity_prices.__wrapped__("api_key")
        assert "Gold" in result
        assert result["Gold"]["price"] == 2000

    @patch("pages.news.requests.get")
    def test_returns_empty_on_non_200(self, mock_get):
        """Test non-200 status returns empty dict."""
        mock_get.return_value.status_code = 500
        result = fetch_commodity_prices.__wrapped__("api_key")
        assert result == {}

    @patch("pages.news.requests.get")
    def test_returns_empty_on_exception(self, mock_get):
        """Test exception returns empty dict."""
        mock_get.side_effect = RequestException()
        result = fetch_commodity_prices.__wrapped__("api_key")
        assert result == {}

    @patch("pages.news.requests.get")
    def test_returns_empty_on_non_list_response(self, mock_get):
        """Test non-list JSON returns empty dict."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"error": "bad"}
        result = fetch_commodity_prices.__wrapped__("api_key")
        assert result == {}


# =============================================================================
# render_news_card tests
# =============================================================================

class TestRenderNewsCard:
    """Tests for render_news_card function."""

    @patch("pages.news.st")
    def test_renders_without_error(self, mock_st):
        """Test that render_news_card runs without error."""
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        article = {
            "date": "2026-02-10",
            "time": "14:00",
            "title": "Test Article",
            "description": "Description",
            "commodities": ["Gold"],
            "tags": ["Market"],
            "source": "Test",
            "url": "http://example.com",
        }
        render_news_card(article)
        mock_st.container.assert_called()

    @patch("pages.news.st")
    def test_handles_unsafe_url(self, mock_st):
        """Test that unsafe URLs are replaced with #."""
        mock_st.container.return_value.__enter__ = MagicMock()
        mock_st.container.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        article = {
            "date": "2026-02-10",
            "time": "14:00",
            "title": "Test",
            "description": "Desc",
            "commodities": ["Gold"],
            "tags": ["Market"],
            "source": "Test",
            "url": "javascript:alert(1)",
        }
        render_news_card(article)
        # Check that markdown was called with safe link
        calls = [str(c) for c in mock_st.markdown.call_args_list]
        assert any("#" in c for c in calls)


# =============================================================================
# render_sidebar tests
# =============================================================================

class TestRenderSidebar:
    """Tests for render_sidebar function."""

    @patch("pages.news.st")
    def test_returns_selections(self, mock_st):
        """Test that render_sidebar returns commodity and tag selections."""
        mock_st.sidebar.selectbox.return_value = "Gold"
        mock_st.sidebar.multiselect.return_value = ["Supply"]
        mock_st.sidebar.button.return_value = False
        commodity, tags = render_sidebar()
        assert commodity == "Gold"
        assert tags == ["Supply"]

    @patch("pages.news.st")
    def test_refresh_button_clears_cache(self, mock_st):
        """Test refresh button triggers cache clear."""
        mock_st.sidebar.selectbox.return_value = "All Commodities"
        mock_st.sidebar.multiselect.return_value = []
        mock_st.sidebar.button.return_value = True
        with patch("pages.news.fetch_general_news") as mock_fetch_general, \
                patch("pages.news.fetch_stock_news") as mock_fetch_stock, \
                patch("pages.news.fetch_commodity_prices") as mock_fetch_prices:
            render_sidebar()
            mock_fetch_general.clear.assert_called()
            mock_fetch_stock.clear.assert_called()
            mock_fetch_prices.clear.assert_called()


# =============================================================================
# render_news_feed_tab tests
# =============================================================================

class TestRenderNewsFeedTab:
    """Tests for render_news_feed_tab function."""

    @patch("pages.news.st")
    @patch("pages.news.render_news_card")
    def test_renders_articles(self, mock_render_card, mock_st):
        """Test that articles are rendered."""
        news = [{"title": "Article 1"}, {"title": "Article 2"}]
        render_news_feed_tab(news)
        assert mock_render_card.call_count == 2

    @patch("pages.news.st")
    def test_shows_info_when_empty(self, mock_st):
        """Test info message shown when no news."""
        render_news_feed_tab([])
        mock_st.info.assert_called()


# =============================================================================
# render_prices_tab tests
# =============================================================================

class TestRenderPricesTab:
    """Tests for render_prices_tab function."""

    @patch("pages.news.st")
    @patch("pages.news.fetch_commodity_prices")
    def test_displays_prices(self, mock_fetch, mock_st):
        """Test prices are displayed."""
        mock_fetch.return_value = {
            "Gold": {"price": 2000, "changesPercentage": 0.5}}
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()
        mock_st.columns.return_value = [MagicMock()]
        render_prices_tab("api_key")
        mock_st.subheader.assert_called()

    @patch("pages.news.st")
    @patch("pages.news.fetch_commodity_prices")
    def test_shows_warning_when_no_prices(self, mock_fetch, mock_st):
        """Test warning shown when prices unavailable."""
        mock_fetch.return_value = {}
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()
        render_prices_tab("api_key")
        mock_st.warning.assert_called()


# =============================================================================
# render_statistics_tab tests
# =============================================================================

class TestRenderStatisticsTab:
    """Tests for render_statistics_tab function."""

    @patch("pages.news.st")
    def test_shows_info_when_empty(self, mock_st):
        """Test info shown when no news."""
        render_statistics_tab([])
        mock_st.info.assert_called()

    @patch("pages.news.st")
    @patch("pages.news.pd")
    def test_displays_statistics(self, mock_pd, mock_st):
        """Test statistics are displayed."""
        mock_st.columns.side_effect = [
            [MagicMock(), MagicMock()],  # First call for charts
            # Second call for metrics
            [MagicMock(), MagicMock(), MagicMock(), MagicMock()],
        ]
        news = [
            {"commodities": ["Gold"], "tags": ["Market"], "source": "Test"},
            {"commodities": ["Silver"], "tags": ["Supply"], "source": "Test2"},
        ]
        render_statistics_tab(news)
        mock_st.subheader.assert_called()


# =============================================================================
# render_footer tests
# =============================================================================

class TestRenderFooter:
    """Tests for render_footer function."""

    @patch("pages.news.st")
    def test_renders_footer(self, mock_st):
        """Test footer renders without error."""
        mock_st.columns.return_value = [
            MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        render_footer()
        mock_st.divider.assert_called()
        mock_st.subheader.assert_called()


# =============================================================================
# main tests
# =============================================================================

class TestMain:
    """Tests for main function."""

    @patch("pages.news.st")
    @patch("pages.news.load_dotenv")
    @patch("pages.news.ENV", {"API_KEY": None})
    def test_stops_without_api_key(self, mock_dotenv, mock_st):
        """Test that main stops if no API key."""
        mock_st.stop.side_effect = SystemExit()
        with pytest.raises(SystemExit):
            main()
        mock_st.error.assert_called()

    @patch("pages.news.st")
    @patch("pages.news.load_dotenv")
    @patch("pages.news.ENV", {"API_KEY": "test_key"})
    @patch("pages.news.render_sidebar")
    @patch("pages.news.fetch_general_news")
    @patch("pages.news.fetch_stock_news")
    @patch("pages.news.render_news_feed_tab")
    @patch("pages.news.render_prices_tab")
    @patch("pages.news.render_statistics_tab")
    @patch("pages.news.render_footer")
    def test_runs_with_api_key(self, mock_footer, mock_stats, mock_prices, mock_feed, mock_stock, mock_general, mock_sidebar, mock_dotenv, mock_st):
        """Test that main runs when API key present."""
        mock_sidebar.return_value = ("All Commodities", [])
        mock_general.return_value = []
        mock_stock.return_value = []
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]
        main()
        mock_st.title.assert_called()
