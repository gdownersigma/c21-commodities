"""File to hold functions to create items in the dashboard."""

import html
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from psycopg2.extensions import connection

from helper_functions import (clean_input,
                              authenticate_user_input,
                              invoke_historical_lambda)

from query_data import (get_market_data_by_ids,
                        get_commodity_symbol_by_id)

# Default commodities that have continuous data (don't need historical fetch)
DEFAULT_COMMODITY_IDS = {10, 18, 40}


def add_commodity_selector(commodity_options: list, i: int):
    """Add dynamic commodity selector to the sidebar."""

    st.session_state.selected_commodities[f"commodity_{i}"] = st.sidebar.selectbox(
        label=f"Select Commodity {i + 1}",
        options=commodity_options,
        format_func=lambda x: x[1],
        key=f"commodity_select_{i}"
    )


def build_single_commodity_graph(df: pd.DataFrame, market_df: pd.DataFrame, graph_index: int = 0):
    """Build display for a single commodity.
    """
    # Create columns: zoom slider | graph | metrics
    slider_col, graph_col, metrics_col = st.columns([0.8, 4, 1.5])

    if market_df.empty:
        with graph_col:
            st.warning("No market data available.")
    else:
        # Get unique key from commodity_id and graph_index
        comm_id = market_df['commodity_id'].iloc[0]
        unique_key = f"{comm_id}_{graph_index}"

        # Get absolute time bounds from data
        data_max_time = market_df['recorded_at'].max()
        data_min_time = market_df['recorded_at'].min()

        # Time range buttons
        with graph_col:
            time_col1, time_col2, time_col3, time_col4 = st.columns(4)
            with time_col1:
                if st.button("3H", key=f"time_3h_{unique_key}", use_container_width=True):
                    st.session_state[f"time_range_{unique_key}"] = 3
            with time_col2:
                if st.button("1D", key=f"time_1d_{unique_key}", use_container_width=True):
                    st.session_state[f"time_range_{unique_key}"] = 24
            with time_col3:
                if st.button("7D", key=f"time_7d_{unique_key}", use_container_width=True):
                    st.session_state[f"time_range_{unique_key}"] = 168
            with time_col4:
                if st.button("30D", key=f"time_30d_{unique_key}", use_container_width=True):
                    st.session_state[f"time_range_{unique_key}"] = 720

        # Get selected time range (default to 3 hours)
        time_range_hours = st.session_state.get(f"time_range_{unique_key}", 3)
        max_time = data_max_time
        requested_min_time = data_max_time - timedelta(hours=time_range_hours)
        min_time = max(data_min_time, requested_min_time)

        # Fetch historical data if needed (only for non-default commodities)
        if requested_min_time < data_min_time and int(comm_id) not in DEFAULT_COMMODITY_IDS:
            if f"fetching_{comm_id}" not in st.session_state:
                from query_data import get_connection
                from os import environ as ENV
                conn = get_connection(ENV)
                symbol = get_commodity_symbol_by_id(conn, int(comm_id))
                conn.close()
                if symbol:
                    invoke_historical_lambda(symbol)
                    st.session_state[f"fetching_{comm_id}"] = True
            st.toast("Bear with us while we fetch the data...", icon="⏳")

        # Get price range for slider
        price_min = float(market_df['price'].min())
        price_max = float(market_df['price'].max())
        price_padding = (price_max - price_min) * 0.1  # 10% padding

        # Filter data to selected time range for high/low calculation
        filtered_df = market_df[market_df['recorded_at'] >= min_time]
        if not filtered_df.empty:
            period_high = float(filtered_df['price'].max())
            period_low = float(filtered_df['price'].min())
        else:
            period_high = float(market_df['price'].max())
            period_low = float(market_df['price'].min())

        # Get current price for step calculation
        sorted_df = market_df.sort_values('recorded_at', ascending=True)
        latest = sorted_df.iloc[-1]
        current_price = float(latest['price'])

        # Step size is 2% of current price
        price_step = round(current_price * 0.02, 2)

        # Add padding to high/low for better graph visibility
        price_range = period_high - period_low
        padding = price_range * 0.05 if price_range > 0 else current_price * 0.01
        default_y_max = period_high + padding
        default_y_min = max(0, period_low - padding)

        with slider_col:
            # Custom CSS for orange styling
            st.markdown("""
                <style>
                    div[data-testid="stNumberInput"] input {
                        border-color: #e6530c !important;
                    }
                    div[data-testid="stNumberInput"] button {
                        background-color: #ff801d !important;
                        color: white !important;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("**Price**")

            # Use number inputs for max/min with direct value entry
            # Include time_range in key so values reset when period changes
            y_max_val = st.number_input(
                "Max $",
                min_value=0.0,
                value=default_y_max,
                step=price_step,
                format="%.2f",
                key=f"price_max_{unique_key}_{time_range_hours}"
            )
            y_min_val = st.number_input(
                "Min $",
                min_value=0.0,
                value=default_y_min,
                step=price_step,
                format="%.2f",
                key=f"price_min_{unique_key}_{time_range_hours}"
            )

            # Analysis Mode button
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📊 Analysis", key=f"analysis_{unique_key}", use_container_width=True):
                st.session_state.analysis_mode = True
                st.session_state.analysis_commodity_id = comm_id

            # Ensure min is always less than max
            y_min = min(y_min_val, y_max_val)
            y_max = max(y_min_val, y_max_val)

        with graph_col:
            # Create interactive line chart
            chart = alt.Chart(market_df).mark_line(
                color='#03c1ff',
                strokeWidth=2.5
            ).encode(
                x=alt.X('recorded_at:T', title='Date & Time',
                        axis=alt.Axis(format='%d %b %H:%M', labelAngle=-45),
                        scale=alt.Scale(domain=[min_time.isoformat(), max_time.isoformat()])),
                y=alt.Y('price:Q', title='Price ($)',
                        scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=[
                    alt.Tooltip('recorded_at:T', title='Date',
                                format='%d %b %Y %H:%M'),
                    alt.Tooltip('price:Q', title='Price', format='$.2f'),
                    alt.Tooltip('change_percentage:Q',
                                title='Change %', format='.2f')
                ]
            ).properties(
                height=350
            ).interactive(bind_y=False)

            st.altair_chart(chart, use_container_width=True)

        # Determine period label for high/low display
        period_labels = {3: "3H", 24: "1D", 168: "7D", 720: "30D"}
        period_label = period_labels.get(time_range_hours, "PERIOD")

    with metrics_col:
        if not market_df.empty:
            # Sort by date and get the most recent record
            sorted_df = market_df.sort_values('recorded_at', ascending=True)
            latest = sorted_df.iloc[-1]
            st.metric("Current Price", f"${latest['price']:.2f}",
                      f"{latest['change_percentage']:.2f}%")

            # Fancy high/low display
            st.markdown("---")
            st.markdown(f"""
                <div style="background-color: #ff801d40; 
                            border-radius: 10px; padding: 15px; text-align: center;
                            border: 3px solid #ff801d;">
                    <p style="color: #64748b; margin: 0; font-size: 12px;">{period_label} HIGH</p>
                    <p style="color: #22c55e; font-size: 24px; font-weight: 700; margin: 5px 0;">
                        ${period_high:.2f}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color: #ff801d40; 
                            border-radius: 10px; padding: 15px; text-align: center; margin-top: 10px;
                            border: 3px solid #ff801d;">
                    <p style="color: #64748b; margin: 0; font-size: 12px;">{period_label} LOW</p>
                    <p style="color: #ef4444; font-size: 24px; font-weight: 700; margin: 5px 0;">
                        ${period_low:.2f}
                    </p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()


def build_combined_graph(df: pd.DataFrame, market_df: pd.DataFrame):
    """Build display for multiple commodities combined."""
    slider_col, graph_col, metrics_col = st.columns([0.8, 4, 1.5])

    if market_df.empty:
        with graph_col:
            st.warning("No market data available.")
    else:
        # Merge to get commodity names
        chart_df = market_df.merge(
            df[['commodity_id', 'commodity_name']].drop_duplicates(),
            on='commodity_id',
            how='left'
        )

        # Get absolute time bounds from data
        data_max_time = chart_df['recorded_at'].max()
        data_min_time = chart_df['recorded_at'].min()

        # Time range buttons
        with graph_col:
            time_col1, time_col2, time_col3, time_col4 = st.columns(4)
            with time_col1:
                if st.button("3H", key="time_3h_combined", use_container_width=True):
                    st.session_state["time_range_combined"] = 3
            with time_col2:
                if st.button("1D", key="time_1d_combined", use_container_width=True):
                    st.session_state["time_range_combined"] = 24
            with time_col3:
                if st.button("7D", key="time_7d_combined", use_container_width=True):
                    st.session_state["time_range_combined"] = 168
            with time_col4:
                if st.button("30D", key="time_30d_combined", use_container_width=True):
                    st.session_state["time_range_combined"] = 720

        # Get selected time range (default to 3 hours)
        time_range_hours = st.session_state.get("time_range_combined", 3)
        max_time = data_max_time
        requested_min_time = data_max_time - timedelta(hours=time_range_hours)
        min_time = max(data_min_time, requested_min_time)

        # Fetch historical data if needed (only for non-default commodities)
        if requested_min_time < data_min_time:
            from query_data import get_connection
            from os import environ as ENV
            needs_fetch = False
            for comm_id in chart_df['commodity_id'].unique():
                if int(comm_id) not in DEFAULT_COMMODITY_IDS:
                    if f"fetching_{comm_id}" not in st.session_state:
                        conn = get_connection(ENV)
                        symbol = get_commodity_symbol_by_id(conn, int(comm_id))
                        conn.close()
                        if symbol:
                            invoke_historical_lambda(symbol)
                            st.session_state[f"fetching_{comm_id}"] = True
                            needs_fetch = True
            if needs_fetch:
                st.toast("Bear with us while we fetch the data...", icon="⏳")

        # Get price range for slider (across all commodities)
        price_min = float(chart_df['price'].min())
        price_max = float(chart_df['price'].max())
        price_padding = (price_max - price_min) * 0.1  # 10% padding

        # Filter data to selected time range for high/low calculation
        filtered_df = chart_df[chart_df['recorded_at'] >= min_time]
        if not filtered_df.empty:
            period_high = float(filtered_df['price'].max())
            period_low = float(filtered_df['price'].min())
        else:
            period_high = float(chart_df['price'].max())
            period_low = float(chart_df['price'].min())

        # Step size is 2% of average current price across commodities
        avg_price = float(chart_df.groupby(
            'commodity_id')['price'].last().mean())
        price_step = round(avg_price * 0.02, 2)

        # Add padding to high/low for better graph visibility
        price_range = period_high - period_low
        padding = price_range * 0.05 if price_range > 0 else avg_price * 0.01
        default_y_max = period_high + padding
        default_y_min = max(0, period_low - padding)

        with slider_col:
            # Custom CSS for orange styling
            st.markdown("""
                <style>
                    div[data-testid="stNumberInput"] input {
                        border-color: #e6530c !important;
                    }
                    div[data-testid="stNumberInput"] button {
                        background-color: #ff801d !important;
                        color: white !important;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("**Price**")

            # Use number inputs for max/min with direct value entry
            # Include time_range in key so values reset when period changes
            y_max_val = st.number_input(
                "Max $",
                min_value=0.0,
                value=default_y_max,
                step=price_step,
                format="%.2f",
                key=f"combined_price_max_{time_range_hours}"
            )
            y_min_val = st.number_input(
                "Min $",
                min_value=0.0,
                value=default_y_min,
                step=price_step,
                format="%.2f",
                key=f"combined_price_min_{time_range_hours}"
            )

            # Analysis Mode button
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📊 Analysis", key="analysis_combined", use_container_width=True):
                st.session_state.analysis_mode = True
                st.session_state.analysis_commodity_ids = list(
                    market_df['commodity_id'].unique())

            # Ensure min is always less than max
            y_min = min(y_min_val, y_max_val)
            y_max = max(y_min_val, y_max_val)

        with graph_col:
            # Create interactive multi-line chart
            chart = alt.Chart(chart_df).mark_line(
                strokeWidth=2.5
            ).encode(
                x=alt.X('recorded_at:T', title='Date & Time',
                        axis=alt.Axis(format='%d %b %H:%M', labelAngle=-45),
                        scale=alt.Scale(domain=[min_time.isoformat(), max_time.isoformat()])),
                y=alt.Y('price:Q', title='Price ($)',
                        scale=alt.Scale(domain=[y_min, y_max])),
                color=alt.Color('commodity_name:N', title='Commodity',
                                scale=alt.Scale(range=['#03c1ff', '#e6530c', '#22c55e', '#8b5cf6', '#f59e0b'])),
                tooltip=[
                    alt.Tooltip('commodity_name:N', title='Commodity'),
                    alt.Tooltip('recorded_at:T', title='Date',
                                format='%d %b %Y %H:%M'),
                    alt.Tooltip('price:Q', title='Price', format='$.2f'),
                    alt.Tooltip('change_percentage:Q',
                                title='Change %', format='.2f')
                ]
            ).properties(
                height=400
            ).interactive(bind_y=False)

            st.altair_chart(chart, use_container_width=True)

    with metrics_col:
        if not market_df.empty:
            # Show stats for each commodity
            for comm_id in market_df['commodity_id'].unique():
                comm_data = market_df[market_df['commodity_id'] == comm_id]
                # Sort by date and get the most recent record
                comm_data = comm_data.sort_values(
                    'recorded_at', ascending=True)
                comm_name = df[df['commodity_id'] ==
                               comm_id]['commodity_name'].iloc[0]
                latest = comm_data.iloc[-1]

                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #03c1ff15 0%, #e2e8f030 100%); 
                                border-left: 3px solid #03c1ff;
                                border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <p style="color: #1e293b; font-weight: 600; margin: 0 0 5px 0;">{comm_name}</p>
                        <p style="color: #03c1ff; font-size: 20px; font-weight: 700; margin: 0;">
                            ${latest['price']:.2f}
                            <span style="font-size: 14px; color: {'#22c55e' if latest['change_percentage'] >= 0 else '#ef4444'};">
                                {'+' if latest['change_percentage'] >= 0 else ''}{latest['change_percentage']:.2f}%
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

    st.divider()


def build_form(conn: connection,
               field_labels: dict,
               form_name: str,
               form_key: str,
               cancel_name: str,
               on_submit,
               on_cancel,
               field_values: dict = None):
    """Build a form for log in and sign up pages."""

    with st.form(key=form_key):
        field_input = {}
        for label, input_type in field_labels.items():
            field_input[label] = st.text_input(label.capitalize(),
                                               value=field_values.get(
                                                   label, "") if field_values else "",
                                               type=input_type,
                                               key=label)

        col1, col2 = st.columns(2)
        with col1:
            with st.container(horizontal_alignment="center"):
                submitted = st.form_submit_button(form_name)
        with col2:
            with st.container(horizontal_alignment="center"):
                cancelled = st.form_submit_button(cancel_name)

        if submitted:
            field_input = clean_input(field_input)

            if not authenticate_user_input(field_input):
                st.error("Please fill in all fields correctly.")
            else:
                on_submit(conn, field_input)

        if cancelled:
            on_cancel()


def page_redirect(msg: str, page: str, alignment: str = "center"):
    """Create a redirect button for account entry pages."""

    with st.container(horizontal_alignment=alignment):
        if st.button(msg):
            st.switch_page(page)


def display_markdown_title(title: str, alignment: str = "center", size: int = 21, weight: int = 600):
    """Display page title."""
    st.markdown(f"""
            <div style='text-align: {alignment}; font-size: {size}px; font-weight: {weight};'>
                {title}
            </div>
        """, unsafe_allow_html=True)


def build_single_commodity_edit(comm: dict) -> dict:
    """Build display for a single commodity."""

    col1, col2, col3, col4, col5, col6 = st.columns(
        [3, 2, 2, 2, 3, 3],
        vertical_alignment="center")

    commodity_data = {"name": comm["name"]}

    with col1:
        display_markdown_title(
            comm['name'], alignment="left", size=18, weight=600)

    with col2:
        with st.container(horizontal_alignment="center"):
            commodity_data["track"] = st.checkbox(
                "Track",
                value=comm.get("track", False),
                key=f"track_{comm["id"]}")

    with col3:
        with st.container(horizontal_alignment="center"):
            commodity_data["buy"] = st.checkbox(
                "Buy",
                value=comm["buy"],
                key=f"buy_{comm["id"]}_alert",
                disabled=not commodity_data["track"])

    with col4:
        with st.container(horizontal_alignment="center"):
            commodity_data["sell"] = st.checkbox(
                "Sell",
                value=comm["sell"],
                key=f"sell_{comm["id"]}_alert",
                disabled=not commodity_data["track"])

    with col5:
        with st.container(horizontal_alignment="center"):
            commodity_data["buy_price"] = st.number_input(
                "Buy Price",
                value=comm["buy_price"],
                min_value=0.0,
                max_value=1000000.0,
                step=0.01,
                format="%.2f",
                key=f"buy_price_{comm["id"]}",
                disabled=not commodity_data["buy"])

    with col6:
        with st.container(horizontal_alignment="center"):
            commodity_data["sell_price"] = st.number_input(
                "Sell Price",
                value=float(comm["sell_price"]),
                min_value=0.0,
                max_value=1000000.0,
                step=0.01,
                format="%.2f",
                key=f"sell_price_{comm["id"]}",
                disabled=not commodity_data["sell"])

    return commodity_data


def logout_button():
    """Build log out button in sidebar."""

    if st.sidebar.button("Log out",
                         key="logout_btn"):
        st.session_state.user = {}
        st.session_state.subscribed_commodities = [10, 18, 40]
        st.session_state.selected_commodities = {
            "commodity_0": [10, "Brent Crude Oil"],
            "commodity_1": [18, "Gold Futures"],
            "commodity_2": [40, "Silver Futures"]
        }
        st.session_state.num_commodities = 3
        st.rerun()

    st.sidebar.divider()


def welcome_message():
    """Display welcome message on dashboard."""

    safe_name = html.escape(st.session_state.user['user_name'])
    st.sidebar.markdown(f"""
            <div style='text-align: left; font-size: 20px; font-weight: 500;'>
                Welcome back, <span style="color: #ff801d; font-weight: 700;">{safe_name}</span>!
            </div>
        """, unsafe_allow_html=True)

    st.sidebar.divider()
