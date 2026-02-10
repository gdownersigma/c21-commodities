"""Unit tests for news.py helper functions."""

from news import (
    identify_commodity,
    auto_tag_article,
    parse_date,
    deduplicate_news,
    filter_news,
    render_tags,
)
import sys
from pathlib import Path

import pytest
from datetime import datetime

# Add the news directory to path for imports to work from any location
sys.path.insert(0, str(Path(__file__).parent))


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
        result = parse_date("invalid-date")
        # Should return today's date
        today = datetime.now().strftime("%Y-%m-%d")
        assert result[0] == today

    def test_returns_current_time_for_empty_string(self):
        """Test fallback to current time for empty string."""
        result = parse_date("")
        today = datetime.now().strftime("%Y-%m-%d")
        assert result[0] == today

    def test_returns_current_time_for_none(self):
        """Test fallback to current time for None."""
        result = parse_date(None)
        today = datetime.now().strftime("%Y-%m-%d")
        assert result[0] == today


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
