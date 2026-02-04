"""Script to extract previous day's data from the database for daily reporting."""
from os import environ as ENV
from datetime import datetime, timedelta, date
import pandas as pd
from psycopg2 import connect
from dotenv import load_dotenv


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    load_dotenv()
    return connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )


def get_previous_day_date() -> date:
    """Returns the date for the previous day."""
    return (datetime.now() - timedelta(days=1)).date()


def extract_market_records() -> pd.DataFrame:
    """Extract all market records from the previous day."""
    conn = get_conn()
    query = """
        SELECT c.symbol, c.commodity_name, mr.recorded_at, mr.price,
               mr.volume, mr.day_high, mr.day_low
        FROM market_records mr
        JOIN commodities c ON mr.commodity_id = c.commodity_id
        WHERE DATE(mr.recorded_at) = %s
        ORDER BY mr.recorded_at DESC;
    """
    df = pd.read_sql_query(query, conn, params=(get_previous_day_date(),))
    conn.close()
    return df


def extract_user_commodities() -> pd.DataFrame:
    """Extract all user commodities with user information."""
    conn = get_conn()
    query = """
        SELECT uc.user_id, u.user_name, u.email, c.symbol, uc.buy_price, uc.sell_price
        FROM user_commodities uc
        JOIN users u ON uc.user_id = u.user_id
        JOIN commodities c ON uc.commodity_id = c.commodity_id
        ORDER BY u.user_name, c.symbol;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
