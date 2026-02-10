"""Commodity News Analysis - Real-time news tracking for commodity markets."""

import streamlit as st
from datetime import datetime
import pandas as pd
import requests
from os import environ as ENV
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

FMP_API_KEY = ENV.get("FMP_API_KEY")

COMMODITIES = {
    'Gold': {
        'keywords': ['gold', 'bullion', 'precious metal', 'xau', 'gold price', 'gold futures'],
        'etf_symbols': ['GLD', 'IAU', 'SGOL'],
        'symbol': 'GCUSD',
        'emoji': '🥇'
    },
    'Silver': {
        'keywords': ['silver', 'xag', 'silver price', 'silver futures', 'precious metal'],
        'etf_symbols': ['SLV', 'SIVR'],
        'symbol': 'SIUSD',
        'emoji': '🥈'
    },
    'Copper': {
        'keywords': ['copper', 'copper price', 'copper futures', 'base metal', 'industrial metal'],
        'etf_symbols': ['CPER', 'JJC'],
        'symbol': 'HGUSD',
        'emoji': '🔶'
    },
    'Wheat': {
        'keywords': ['wheat', 'grain', 'wheat futures', 'wheat price', 'agriculture', 'crop'],
        'etf_symbols': ['WEAT'],
        'symbol': 'ZWUSD',
        'emoji': '🌾'
    },
    'Oats': {
        'keywords': ['oats', 'oat futures', 'oat price', 'grain', 'cereal'],
        'etf_symbols': [],
        'symbol': 'ZOUSD',
        'emoji': '🌾'
    }
}

TAG_KEYWORDS = {
    'Supply': ['supply', 'production', 'output', 'mine', 'mining', 'harvest', 'shortage', 'surplus'],
    'Demand': ['demand', 'consumption', 'import', 'export', 'buying', 'purchase'],
    'Policy': ['fed', 'federal reserve', 'central bank', 'interest rate', 'policy', 'regulation', 'tariff'],
    'Weather': ['weather', 'drought', 'flood', 'storm', 'frost', 'climate'],
    'Geopolitical': ['war', 'conflict', 'sanction', 'trade war', 'tension', 'geopolitical', 'ukraine', 'russia', 'china'],
    'Market': ['price', 'futures', 'rally', 'decline', 'surge', 'drop', 'market', 'trading', 'investor'],
    'Currency': ['dollar', 'usd', 'currency', 'forex', 'exchange rate'],
}

TAG_COLORS = {
    'Supply': 'tag-supply', 'Demand': 'tag-demand', 'Policy': 'tag-policy',
    'Weather': 'tag-weather', 'Geopolitical': 'tag-geopolitical',
    'Market': 'tag-market', 'Currency': 'tag-currency'
}

COMMODITY_BADGES = {
    'Gold': 'badge-gold', 'Silver': 'badge-silver', 'Copper': 'badge-copper',
    'Wheat': 'badge-wheat', 'Oats': 'badge-oats', 'General': 'badge-general'
}

CSS_STYLES = """
<style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }
    .stApp, .stApp * { color: #1e293b; }
    h1, h2, h3, .stTitle, [data-testid="stTitle"] { color: #1e293b !important; }
    p, span, label, .stMarkdown, .stCaption, [data-testid="stMarkdownContainer"] { color: #334155 !important; }
    .stRadio label, .stRadio span { color: #334155 !important; }
    .timeline-event { position: relative; padding: 15px 20px; margin: 10px 0; border-radius: 10px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .news-event { border-left: 4px solid #3b82f6; }
    .tag { display: inline-block; padding: 4px 10px; margin: 2px; border-radius: 15px; font-size: 12px; font-weight: 500; }
    .tag-supply { background: #fef3c7; color: #92400e; }
    .tag-demand { background: #dbeafe; color: #1e40af; }
    .tag-policy { background: #f3e8ff; color: #7c3aed; }
    .tag-weather { background: #dcfce7; color: #166534; }
    .tag-geopolitical { background: #fee2e2; color: #991b1b; }
    .tag-market { background: #e0e7ff; color: #3730a3; }
    .tag-currency { background: #fce7f3; color: #9d174d; }
    .tag-default { background: #f1f5f9; color: #475569; }
    .commodity-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    .badge-gold { background: #fef3c7; color: #b45309; }
    .badge-silver { background: #e5e7eb; color: #374151; }
    .badge-copper { background: #fed7aa; color: #c2410c; }
    .badge-wheat { background: #fef9c3; color: #a16207; }
    .badge-oats { background: #ecfccb; color: #4d7c0f; }
    .badge-general { background: #e0e7ff; color: #3730a3; }
</style>
"""


# =============================================================================
# API FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def fetch_general_news(limit: int = 100) -> list:
    """Fetch general news from FMP API."""
    url = "https://financialmodelingprep.com/stable/news/general-latest"
    params = {"page": 0, "limit": limit, "apikey": FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_stock_news(symbols: list, limit: int = 50) -> list:
    """Fetch stock news for specific symbols (ETFs)."""
    url = "https://financialmodelingprep.com/stable/news/stock"
    params = {"symbols": ",".join(
        symbols), "limit": limit, "apikey": FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=60)
def fetch_commodity_prices() -> dict:
    """Fetch current commodity prices."""
    url = "https://financialmodelingprep.com/stable/batch-commodity-quotes"
    symbol_map = {cfg["symbol"]: name for name, cfg in COMMODITIES.items()}
    try:
        response = requests.get(
            url, params={"apikey": FMP_API_KEY}, timeout=10)
        if response.status_code != 200:
            return {}
        prices = {}
        for item in response.json():
            symbol = item.get("symbol", "")
            if symbol in symbol_map:
                prices[symbol_map[symbol]] = {
                    "price": item.get("price", 0),
                    "change": item.get("change", 0),
                    "changesPercentage": item.get("changesPercentage", 0)
                }
        return prices
    except Exception:
        return {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def identify_commodity(text: str) -> list:
    """Identify which commodities a news article relates to."""
    text_lower = text.lower()
    matched = [name for name, cfg in COMMODITIES.items() if any(
        kw in text_lower for kw in cfg["keywords"])]
    return matched if matched else ["General"]


def auto_tag_article(text: str) -> list:
    """Automatically tag an article based on keywords."""
    text_lower = text.lower()
    tags = [tag for tag, keywords in TAG_KEYWORDS.items() if any(
        kw in text_lower for kw in keywords)]
    return tags if tags else ["Market"]


def render_tags(tags: list) -> str:
    """Render tags as HTML."""
    return " ".join(f'<span class="tag {TAG_COLORS.get(tag, "tag-default")}">{tag}</span>' for tag in tags)


def parse_date(published_date: str) -> tuple:
    """Parse published date into date and time strings."""
    try:
        if published_date:
            dt = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        pass  # Invalid date format, fall back to current time
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


def process_news_data(news_items: list) -> list:
    """Process raw news data into structured format."""
    processed = []
    for idx, item in enumerate(news_items):
        title = item.get("title", "")
        text = item.get("text", item.get("content", ""))
        full_text = f"{title} {text}"
        date_str, time_str = parse_date(item.get("publishedDate", ""))
        processed.append({
            "id": idx + 1,
            "date": date_str,
            "time": time_str,
            "title": title,
            "description": text[:500] + "..." if len(text) > 500 else text,
            "commodities": identify_commodity(full_text),
            "tags": auto_tag_article(full_text),
            "source": item.get("site", item.get("source", "News")),
            "url": item.get("url", "#"),
        })
    return processed


def deduplicate_news(news_items: list) -> list:
    """Remove duplicate articles by URL and title."""
    seen_urls, seen_titles, unique = set(), set(), []
    for item in news_items:
        url = item.get("url", "")
        title = item.get("title", "").lower().strip()
        if url and url not in seen_urls and title not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(title)
            unique.append(item)
    return unique


def filter_news(processed_news: list, selected_commodity: str, selected_tags: list) -> list:
    """Filter news based on commodity and tag selections."""
    filtered = [a for a in processed_news if a["commodities"] != ["General"]]
    if selected_commodity != "All Commodities":
        filtered = [
            a for a in filtered if selected_commodity in a["commodities"]]
    if selected_tags:
        filtered = [a for a in filtered if any(
            tag in a["tags"] for tag in selected_tags)]
    return sorted(filtered, key=lambda x: (x["date"], x["time"]), reverse=True)


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_news_card(article: dict):
    """Render a single news card."""
    commodities = article.get("commodities", ["General"])
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"📅 {article['date']} • {article['time']}")
        with col2:
            badges = " ".join(
                f'<span class="commodity-badge {COMMODITY_BADGES.get(c, "badge-general")}">{c}</span>' for c in commodities[:2])
            st.markdown(
                f"<div style='text-align: right;'>{badges}</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="timeline-event news-event">
                <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">📰 {article['title']}</div>
                <div style="color: #64748b; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">{article['description']}</div>
                <div style="font-size: 12px; color: #94a3b8;">Source: {article['source']} | <a href="{article['url']}" target="_blank">Read more →</a></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(
            f"<div>🏷️ {render_tags(article['tags'])}</div>", unsafe_allow_html=True)


def render_sidebar() -> tuple:
    """Render sidebar filters and return selections."""
    st.sidebar.header("🔍 Filters")
    commodities_list = ["All Commodities"] + list(COMMODITIES.keys())
    selected_commodity = st.sidebar.selectbox(
        "Select Commodity", commodities_list)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏷️ Filter by Tag")
    selected_tags = st.sidebar.multiselect(
        "Select tags", list(TAG_KEYWORDS.keys()))
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh News", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    return selected_commodity, selected_tags


def render_news_feed_tab(filtered_news: list):
    """Render the Live News Feed tab."""
    st.subheader(f"Latest News ({len(filtered_news)} articles)")
    if not filtered_news:
        st.info("No commodity news found. Try broadening your search or refreshing.")
        st.markdown(
            "**Tip:** News is filtered for articles mentioning Gold, Silver, Copper, Wheat, or Oats.")
    else:
        for article in filtered_news[:50]:
            render_news_card(article)


def render_prices_tab():
    """Render the Commodity Prices tab."""
    st.subheader("💰 Live Commodity Prices")
    with st.spinner("Fetching prices..."):
        prices = fetch_commodity_prices()
    if prices:
        cols = st.columns(len(prices))
        for col, (name, data) in zip(cols, prices.items()):
            with col:
                emoji = COMMODITIES.get(name, {}).get("emoji", "📊")
                st.metric(
                    label=f"{emoji} {name}", value=f"${data['price']:,.2f}", delta=f"{data['changesPercentage']:+.2f}%")
    else:
        st.warning("Unable to fetch prices. Please try again later.")
    st.markdown("---")
    st.caption("Prices provided by Financial Modeling Prep API.")


def render_statistics_tab(processed_news: list, filtered_news: list):
    """Render the Statistics tab."""
    st.subheader("📊 News Statistics")
    if not filtered_news:
        st.info("No statistics available.")
        return
    commodity_counts, tag_counts = {}, {}
    for article in processed_news:
        for comm in article["commodities"]:
            if comm != "General":
                commodity_counts[comm] = commodity_counts.get(comm, 0) + 1
        for tag in article["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    if commodity_counts:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Articles by Commodity**")
            st.bar_chart(pd.DataFrame({"Count": commodity_counts}).T.T)
        with col2:
            st.markdown("**Articles by Tag**")
            st.bar_chart(pd.DataFrame({"Count": tag_counts}).T.T)
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Articles", len(processed_news))
    c2.metric("Commodity Articles", len(
        [a for a in processed_news if a["commodities"] != ["General"]]))
    c3.metric("Sources", len(set(a["source"] for a in processed_news)))
    c4.metric("Tags Used", len(
        set(t for a in processed_news for t in a["tags"])))


def render_footer():
    """Render page footer."""
    st.divider()
    st.subheader("📖 Legend")
    cols = st.columns(4)
    legends = [("🥇 Gold", "Precious metal"), ("🥈 Silver", "Precious metal"),
               ("🔶 Copper", "Industrial metal"), ("🌾 Wheat/Oats", "Agricultural")]
    for col, (title, desc) in zip(cols, legends):
        col.markdown(f"**{title}** - {desc}")
    st.caption(
        "💡 News auto-tagged based on content. Data by Financial Modeling Prep API.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application entry point."""
    st.set_page_config(page_title="Commodity News Analysis",
                       page_icon="📊", layout="wide")
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.title("📊 Commodity News Analysis")
    st.markdown(
        "Real-time news tracking for **Gold**, **Silver**, **Copper**, **Wheat**, and **Oats**.")
    st.divider()
    selected_commodity, selected_tags = render_sidebar()
    with st.spinner("Fetching news..."):
        all_etf_symbols = [s for cfg in COMMODITIES.values()
                           for s in cfg["etf_symbols"]]
        raw_news = deduplicate_news(fetch_general_news(
            100) + fetch_stock_news(all_etf_symbols, 50))
        processed_news = process_news_data(raw_news)
        filtered_news = filter_news(
            processed_news, selected_commodity, selected_tags)
    tab1, tab2, tab3 = st.tabs(
        ["📰 Live News Feed", "💰 Commodity Prices", "📊 Statistics"])
    with tab1:
        render_news_feed_tab(filtered_news)
    with tab2:
        render_prices_tab()
    with tab3:
        render_statistics_tab(processed_news, filtered_news)
    render_footer()


if __name__ == "__main__":
    main()
