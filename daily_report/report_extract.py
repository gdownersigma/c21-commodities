"""Script to extract previous day's data from the database for daily reporting."""
from os import environ as ENV
from datetime import datetime, timedelta, date
import pandas as pd
from psycopg2 import connect
from dotenv import load_dotenv


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    load_dotenv()
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    return conn


def get_previous_day_date() -> date:
    """Returns the date for the previous day."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.date()


def extract_market_records() -> pd.DataFrame:
    """Extract all market records from the previous day."""
    conn = get_conn()
    previous_day = get_previous_day_date()

    query = """
        SELECT 
            mr.market_record_id,
            mr.commodity_id,
            c.symbol,
            c.commodity_name,
            c.currency,
            mr.recorded_at,
            mr.price,
            mr.volume,
            mr.day_high,
            mr.day_low,
            mr.change,
            mr.change_percentage,
            mr.open_price,
            mr.previous_close,
            mr.price_avg_50,
            mr.price_avg_200,
            mr.year_high,
            mr.year_low,
            mr.ingested_at
        FROM market_records mr
        JOIN commodities c ON mr.commodity_id = c.commodity_id
        WHERE DATE(mr.recorded_at) = %s
        ORDER BY mr.recorded_at DESC;
    """

    df = pd.read_sql_query(query, conn, params=(previous_day,))
    conn.close()
    return df


def extract_user_commodities() -> pd.DataFrame:
    """Extract all user commodities with user information."""
    conn = get_conn()

    query = """
        SELECT 
            uc.user_commodity_id,
            uc.user_id,
            u.user_name,
            u.email,
            uc.commodity_id,
            c.symbol,
            c.commodity_name,
            c.currency,
            uc.buy_price,
            uc.sell_price
        FROM user_commodities uc
        JOIN users u ON uc.user_id = u.user_id
        JOIN commodities c ON uc.commodity_id = c.commodity_id
        ORDER BY u.user_name, c.commodity_name;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def extract_all_users() -> pd.DataFrame:
    """Extract all users from the database."""
    conn = get_conn()

    query = """
        SELECT 
            user_id,
            user_name,
            email
        FROM users
        ORDER BY user_name;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def extract_all_commodities() -> pd.DataFrame:
    """Extract all commodities from the database."""
    conn = get_conn()

    query = """
        SELECT 
            commodity_id,
            symbol,
            commodity_name,
            currency
        FROM commodities
        ORDER BY commodity_name;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def extract_previous_day_summary() -> pd.DataFrame:
    """Extract summary statistics for previous day's market data."""
    conn = get_conn()
    previous_day = get_previous_day_date()

    query = """
        SELECT 
            c.symbol,
            c.commodity_name,
            COUNT(mr.market_record_id) as record_count,
            AVG(mr.price) as avg_price,
            MIN(mr.day_low) as min_price,
            MAX(mr.day_high) as max_price,
            AVG(mr.change_percentage) as avg_change_percentage,
            SUM(mr.volume) as total_volume
        FROM market_records mr
        JOIN commodities c ON mr.commodity_id = c.commodity_id
        WHERE DATE(mr.recorded_at) = %s
        GROUP BY c.symbol, c.commodity_name
        ORDER BY c.commodity_name;
    """

    df = pd.read_sql_query(query, conn, params=(previous_day,))
    conn.close()
    return df


if __name__ == "__main__":
    print(f"Extracting data for: {get_previous_day_date()}")

    print("\n--- Market Records ---")
    market_df = extract_market_records()
    print(f"Records found: {len(market_df)}")
    if not market_df.empty:
        print(market_df.head())

    print("\n--- User Commodities ---")
    user_commodities_df = extract_user_commodities()
    print(f"Records found: {len(user_commodities_df)}")
    if not user_commodities_df.empty:
        print(user_commodities_df.head())

    print("\n--- All Users ---")
    users_df = extract_all_users()
    print(f"Records found: {len(users_df)}")
    if not users_df.empty:
        print(users_df.head())

    print("\n--- All Commodities ---")
    commodities_df = extract_all_commodities()
    print(f"Records found: {len(commodities_df)}")
    if not commodities_df.empty:
        print(commodities_df.head())

    print("\n--- Previous Day Summary ---")
    summary_df = extract_previous_day_summary()
    print(f"Records found: {len(summary_df)}")
    if not summary_df.empty:
        print(summary_df)
