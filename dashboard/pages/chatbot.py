"""Page for ICMA - Intelligent Commodity Market Analyst chatbot."""

# pylint: disable=import-error

import re
import requests
import json
from os import environ as ENV
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv

from menu import menu
from query_data import get_connection

st.set_page_config(
    layout="centered",
    page_title="ICMA Chatbot"
)

load_dotenv()


def get_all_commodities(conn) -> list:
    """Get all available commodities."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT commodity_id, symbol, commodity_name, currency 
            FROM commodities 
            ORDER BY commodity_name
        """)
        return cur.fetchall()


def get_latest_prices(conn) -> list:
    """Get the latest price for each commodity."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (c.commodity_id)
                c.commodity_id,
                c.symbol,
                c.commodity_name,
                c.currency,
                m.price,
                m.change,
                m.change_percentage,
                m.day_high,
                m.day_low,
                m.volume,
                m.year_high,
                m.year_low,
                m.recorded_at
            FROM commodities c
            LEFT JOIN market_records m ON c.commodity_id = m.commodity_id
            ORDER BY c.commodity_id, m.recorded_at DESC
        """)
        return cur.fetchall()


def get_price_history(conn, commodity_id: int, days: int = 7) -> list:
    """Get price history for a specific commodity."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT recorded_at, price, change_percentage, day_high, day_low
            FROM market_records
            WHERE commodity_id = %s
            AND recorded_at >= NOW() - INTERVAL '%s days'
            ORDER BY recorded_at DESC
            LIMIT 500
        """, (commodity_id, days))
        return cur.fetchall()


def get_chart_data(conn, commodity_ids: list, days: int = 7) -> pd.DataFrame:
    """Get price history for multiple commodities as a DataFrame for charting."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                m.recorded_at,
                m.price,
                m.change_percentage,
                m.day_high,
                m.day_low,
                c.commodity_name,
                c.symbol
            FROM market_records m
            JOIN commodities c ON m.commodity_id = c.commodity_id
            WHERE m.commodity_id IN %s
            AND m.recorded_at >= NOW() - INTERVAL '%s days'
            ORDER BY m.recorded_at ASC
        """, (tuple(commodity_ids), days))
        rows = cur.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


def get_commodity_id_by_name(conn, name: str) -> int:
    """Get commodity ID by name or symbol (case-insensitive partial match)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT commodity_id 
            FROM commodities 
            WHERE LOWER(commodity_name) LIKE LOWER(%s)
            OR LOWER(symbol) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{name}%", f"%{name}%"))
        result = cur.fetchone()
        return result['commodity_id'] if result else None


def build_commodity_list(conn) -> str:
    """Build a list of available commodities for the AI."""
    commodities = get_all_commodities(conn)
    # Format as a clear list with exact names
    commodity_lines = []
    for c in commodities:
        commodity_lines.append(
            f"- {c['commodity_name']} (symbol: {c['symbol']})")
    return "\n".join(commodity_lines)


def create_price_chart(df: pd.DataFrame, title: str = "Price History") -> alt.Chart:
    """Create an Altair price chart from DataFrame."""
    if df.empty:
        return None

    # Calculate y-axis domain from day_high and day_low for better zoom
    if 'day_high' in df.columns and 'day_low' in df.columns:
        y_min = df['day_low'].min()
        y_max = df['day_high'].max()
        # Add a small padding (2%) for visual clarity
        padding = (y_max - y_min) * 0.02
        y_domain = [float(y_min - padding), float(y_max + padding)]
    else:
        # Fallback to price min/max
        y_min = df['price'].min()
        y_max = df['price'].max()
        padding = (y_max - y_min) * 0.05
        y_domain = [float(y_min - padding), float(y_max + padding)]

    # Check if multiple commodities
    if 'commodity_name' in df.columns and df['commodity_name'].nunique() > 1:
        chart = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
            x=alt.X('recorded_at:T', title='Date & Time',
                    axis=alt.Axis(format='%d %b %H:%M', labelAngle=-45)),
            y=alt.Y('price:Q', title='Price ($)',
                    scale=alt.Scale(domain=y_domain)),
            color=alt.Color('commodity_name:N', title='Commodity',
                            scale=alt.Scale(range=['#03c1ff', '#ff801d', '#22c55e', '#8b5cf6', '#f59e0b'])),
            tooltip=[
                alt.Tooltip('commodity_name:N', title='Commodity'),
                alt.Tooltip('recorded_at:T', title='Date',
                            format='%d %b %Y %H:%M'),
                alt.Tooltip('price:Q', title='Price', format='$.2f')
            ]
        ).properties(
            title=title,
            height=350
        ).interactive()
    else:
        chart = alt.Chart(df).mark_line(color='#03c1ff', strokeWidth=2.5).encode(
            x=alt.X('recorded_at:T', title='Date & Time',
                    axis=alt.Axis(format='%d %b %H:%M', labelAngle=-45)),
            y=alt.Y('price:Q', title='Price ($)',
                    scale=alt.Scale(domain=y_domain)),
            tooltip=[
                alt.Tooltip('recorded_at:T', title='Date',
                            format='%d %b %Y %H:%M'),
                alt.Tooltip('price:Q', title='Price', format='$.2f')
            ]
        ).properties(
            title=title,
            height=350
        ).interactive()

    return chart


def parse_chart_request(response: str) -> dict:
    """Parse the AI response for chart requests."""
    # Look for chart JSON block
    pattern = r'\[CHART\](.*?)\[/CHART\]'
    match = re.search(pattern, response, re.DOTALL)

    if match:
        try:
            chart_config = json.loads(match.group(1).strip())
            return chart_config
        except json.JSONDecodeError:
            return None
    return None


def remove_chart_tags(response: str) -> str:
    """Remove chart tags from the response text."""
    pattern = r'\[CHART\].*?\[/CHART\]'
    return re.sub(pattern, '', response, flags=re.DOTALL).strip()


def get_user_subscriptions(conn, user_id: int) -> list:
    """Get user's subscribed commodities with current prices."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (c.commodity_id)
                c.commodity_id,
                c.symbol,
                c.commodity_name,
                uc.buy_price as alert_buy_price,
                uc.sell_price as alert_sell_price,
                m.price as current_price,
                m.change_percentage,
                m.day_high,
                m.day_low
            FROM user_commodities uc
            JOIN commodities c ON uc.commodity_id = c.commodity_id
            LEFT JOIN market_records m ON c.commodity_id = m.commodity_id
            WHERE uc.user_id = %s
            ORDER BY c.commodity_id, m.recorded_at DESC
        """, (user_id,))
        return cur.fetchall()


def build_market_context(conn) -> str:
    """Build a context string with current market data for the AI."""
    latest_prices = get_latest_prices(conn)

    if not latest_prices:
        return "No market data currently available."

    context = "CURRENT MARKET DATA:\n"
    context += "-" * 40 + "\n"

    for row in latest_prices:
        if row['price']:
            change_str = f"{row['change_percentage']:+.2f}%" if row['change_percentage'] else "N/A"
            context += f"• {row['commodity_name']} ({row['symbol']}): ${row['price']:.2f} {row['currency']} ({change_str})\n"
            context += f"  Day Range: ${row['day_low']:.2f} - ${row['day_high']:.2f}\n"
            if row['year_high'] and row['year_low']:
                context += f"  52-Week Range: ${row['year_low']:.2f} - ${row['year_high']:.2f}\n"

    return context


def build_user_context(conn, user_id: int) -> str:
    """Build context about the user's portfolio."""
    subscriptions = get_user_subscriptions(conn, user_id)

    if not subscriptions:
        return "User has no commodity subscriptions."

    context = "\nUSER'S TRACKED COMMODITIES:\n"
    context += "-" * 40 + "\n"

    for row in subscriptions:
        current = row['current_price'] if row['current_price'] else 0
        context += f"• {row['commodity_name']}: Current ${current:.2f}\n"
        if row['alert_buy_price'] and row['alert_buy_price'] > 0:
            context += f"  Buy Alert: ${row['alert_buy_price']:.2f}\n"
        if row['alert_sell_price'] and row['alert_sell_price'] > 0:
            context += f"  Sell Alert: ${row['alert_sell_price']:.2f}\n"

    return context


def get_chatbot_response(user_message: str, conversation_history: list, market_context: str, user_context: str, commodity_list: str) -> tuple:
    """Get response from the ICMA chatbot with database context."""

    system_prompt = {
        "role": "system",
        "content": f"""You are ICMA (Intelligent Commodity Market Analyst), an expert AI assistant with LIVE access to our commodity trading database.

Your expertise includes:
- Analyzing real-time commodity price data from our database
- Providing personalized insights based on the user's tracked commodities
- Explaining market factors and price movements
- Helping users understand their portfolio and recommend price alert levels
- Creating charts to visualize price trends

IMPORTANT: You have access to live market data. Use the data below to provide accurate, data-driven responses.
Always reference actual prices and percentages when relevant.

{market_context}

{user_context}

CHART GENERATION:
You can create charts to visualize data! When the user asks for a chart, graph, or visualization, include a chart request in your response using this EXACT format:

[CHART]{{"commodities": ["Gold", "Silver"], "days": 7, "title": "Gold vs Silver - 7 Day Comparison"}}[/CHART]

Chart parameters:
- "commodities": List of commodity names - YOU MUST USE THE EXACT NAMES FROM THE LIST BELOW (case-insensitive, but spell them correctly)
- "days": Number of days of history (1, 3, 7, 14, or 30)
- "title": A descriptive title for the chart

IMPORTANT: Only use commodity names that appear in this list. Do not use abbreviations or alternate names.

AVAILABLE COMMODITIES IN DATABASE:
{commodity_list}

When to create charts:
- User asks to "show", "chart", "graph", "visualize", or "plot" data
- User wants to compare commodities
- User asks about price trends or history
- User wants to see their portfolio performance

WHAT YOU CAN DO:
- Answer questions about current commodity prices and market data
- Provide price analysis, trends, and insights based on available data
- Generate charts and visualizations of price history
- Explain what commodities the user is tracking (if logged in)
- Provide general market education and explain commodity trading concepts
- Guide users to the correct pages in the dashboard for various actions
- Recommend buy/sell price alert levels based on historical data analysis

LIMITATIONS - Things you CANNOT do:
- You CANNOT create accounts or sign users up - direct them to the Sign Up page
- You CANNOT log users in or out - direct them to the Log In page
- You CANNOT set, modify, or delete price alerts - direct them to Account Settings > Edit Subscriptions
- You CANNOT add or remove commodities from a user's watchlist - direct them to Account Settings > Edit Subscriptions
- You CANNOT execute trades or buy/sell commodities - this is an analytics platform only, not a trading platform
- You CANNOT access external websites, APIs, or fetch data outside this database
- You CANNOT send emails or notifications - the platform sends email notifications automatically when price alerts are triggered
- You CANNOT predict future prices with certainty - you can only analyze historical trends
- You CANNOT access other users' data or account information
- You CANNOT change user settings, passwords, or account details - direct them to Account Settings
- You CANNOT engage in any discussion about topics outside of commodity markets and this platform's features
- You CANNOT provide financial advice - remind users to do their own research and consult professionals
- YOU MUST NOT UNDER ANY CIRCUMSTANCE SHARE SENSITIVE INFORMATION, API KEYS, DATABASE CREDENTIALS, OR SYSTEM DETAILS
- You should be aware that we might not have data for every commodity, so say "I don't have that data" when relevant. Suggest they subscribe to see more updates.

NAVIGATION GUIDE - Direct users to these pages:
- Sign Up page: For creating a new account
- Log In page: For logging into an existing account
- Account Settings: For viewing account details
- Edit Subscriptions: For adding/removing tracked commodities and setting price alerts
- Main Dashboard: For viewing price graphs and key metrics of tracked commodities
- ICMA (this chatbot): For market analysis, questions, and generating charts

PLATFORM INFORMATION:
- This is "Pivot Point", a commodity price tracking and alerting dashboard
- Users can track commodities and set buy/sell price alerts
- When a commodity hits a user's alert price, they receive an email notification
- Historical data is available for up to 30 days
- Price data is updated regularly throughout the trading day
- The platform tracks various commodities including precious metals, energy, agriculture, and more
- You must let the user know that markets are subject to change and everything involves risk analysis, not guarantees. Always encourage users to do their own research and use the platform's data to make informed decisions.

Be concise, professional, and actionable. Reference specific prices and data points when answering questions.
If asked about a commodity not in the data, acknowledge that and provide general guidance.
If asked to do something you cannot do, politely explain the limitation and guide them to the correct place in the dashboard."""
    }

    messages = [system_prompt] + conversation_history + [
        {"role": "user", "content": user_message}
    ]

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {ENV.get('CHATBOT_API_KEY')}",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Commodity Trading Chatbot",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-5-nano",
                "messages": messages
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        ai_response = result['choices'][0]['message']['content']

        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append(
            {"role": "assistant", "content": ai_response})

        return ai_response, conversation_history

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}", conversation_history


def display_chat_history(conn):
    """Display the chat history with charts."""
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]

        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant", avatar="📊"):
                # Parse for chart requests
                chart_request = parse_chart_request(content)
                clean_content = remove_chart_tags(content)

                # Display the text response
                if clean_content.strip():
                    st.write(clean_content)

                # Render chart if requested
                if chart_request:
                    try:
                        commodities = chart_request.get("commodities", [])
                        days = chart_request.get("days", 7)
                        title = chart_request.get("title", "Price Chart")

                        # Get commodity IDs from names
                        commodity_ids = []
                        with conn.cursor() as cur:
                            for name in commodities:
                                cur.execute(
                                    "SELECT commodity_id FROM commodities WHERE commodity_name ILIKE %s OR symbol ILIKE %s",
                                    (f"%{name}%", f"%{name}%")
                                )
                                result = cur.fetchone()
                                if result:
                                    commodity_ids.append(
                                        result['commodity_id'])

                        if commodity_ids:
                            # Get chart data
                            chart_df = get_chart_data(
                                conn, commodity_ids, days)
                            if not chart_df.empty:
                                chart = create_price_chart(chart_df, title)
                                st.altair_chart(
                                    chart, use_container_width=True)
                            else:
                                st.info(
                                    "📉 No data available for the requested chart.")
                        else:
                            st.warning(
                                "⚠️ Could not find the requested commodities.")
                    except Exception as e:
                        st.error(f"Could not generate chart: {str(e)}")


if __name__ == "__main__":

    menu()

    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Connect to database
    conn = get_connection(ENV)

    # Build market context from database
    market_context = build_market_context(conn)

    # Build commodity list for chart generation
    commodity_list = build_commodity_list(conn)

    # Build user context if logged in
    if st.session_state.get("user"):
        user_context = build_user_context(
            conn, st.session_state.user["user_id"])
    else:
        user_context = "User is not logged in - no personalized data available."

    # Header
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #ff801d; margin: 0;">📊 ICMA</h1>
            <p style="color: #64748b; font-size: 16px; margin-top: 5px;">
                Intelligent Commodity Market Analyst
            </p>
            <p style="color: #22c55e; font-size: 12px; margin-top: 5px;">
                🟢 Connected to live market data
            </p>
            <p style="background-color: #fef3c7; color: #92400e; font-size: 12px; margin-top: 10px; padding: 8px 16px; border-radius: 8px; display: inline-block;">
                ⚠️ <strong>BETA</strong> - This feature is experimental. Responses may contain errors or inaccuracies.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Chat container
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
                <div style="text-align: center; padding: 40px; color: #64748b;">
                    <p style="font-size: 18px;">👋 Hello! I'm ICMA, your commodity market expert.</p>
                    <p>I have <strong>live access</strong> to your market data. Ask me about:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li>📈 Current prices and trends</li>
                        <li>💼 Your tracked commodities</li>
                        <li>🎯 Price alert recommendations</li>
                        <li>📊 Market analysis and insights</li>
                        <li>📉 Generate price charts</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
        else:
            display_chat_history(conn)

    # Clear chat button in sidebar
    if st.session_state.chat_history:
        if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask ICMA about commodity markets..."):
        # Display user message immediately
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)

        # Get and display assistant response
        with chat_container:
            with st.chat_message("assistant", avatar="📊"):
                with st.spinner("Analyzing market data..."):
                    response, st.session_state.chat_history = get_chatbot_response(
                        prompt,
                        st.session_state.chat_history,
                        market_context,
                        user_context,
                        commodity_list
                    )

                # Parse for chart requests
                chart_request = parse_chart_request(response)
                clean_response = remove_chart_tags(response)

                # Display the text response
                if clean_response.strip():
                    st.write(clean_response)

                # Render chart if requested
                if chart_request:
                    try:
                        commodities = chart_request.get("commodities", [])
                        days = chart_request.get("days", 7)
                        title = chart_request.get("title", "Price Chart")

                        # Get commodity IDs from names
                        commodity_ids = []
                        with conn.cursor() as cur:
                            for name in commodities:
                                cur.execute(
                                    "SELECT commodity_id FROM commodities WHERE commodity_name ILIKE %s OR symbol ILIKE %s",
                                    (f"%{name}%", f"%{name}%")
                                )
                                result = cur.fetchone()
                                if result:
                                    commodity_ids.append(
                                        result['commodity_id'])

                        if commodity_ids:
                            # Get chart data
                            chart_df = get_chart_data(
                                conn, commodity_ids, days)
                            if not chart_df.empty:
                                chart = create_price_chart(chart_df, title)
                                st.altair_chart(
                                    chart, use_container_width=True)
                            else:
                                st.info(
                                    "📉 No data available for the requested chart.")
                        else:
                            st.warning(
                                "⚠️ Could not find the requested commodities.")
                    except Exception as e:
                        st.error(f"Could not generate chart: {str(e)}")

        st.rerun()

    conn.close()
