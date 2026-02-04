"""Transform script for historical financial data pipeline."""

from os import environ as ENV

from psycopg2 import connect
from dotenv import load_dotenv
import pandas as pd


def change_date_column_to_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Change date column to timestamp."""
    df['date'] = pd.to_datetime(df['date'])
    return df


def remove_vwap_column(df: pd.DataFrame) -> pd.DataFrame:
    """Remove VWAP column from the DataFrame."""
    if 'vwap' in df.columns:
        df = df.drop(columns=['vwap'])
    return df


def change_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Change column names to ones that match the database schema."""
    df = df.rename(columns={
        'symbol': 'symbol',
        'date': 'recorded_at',
        'open': 'open_price',
        'high': 'day_high',
        'low': 'day_low',
        'close': 'price',
        'volume': 'volume',
        'change': 'change',
        'changePercent': 'change_percentage'
    })
    return df


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    return conn


def get_symbol_id_map() -> dict:
    """Fetch all symbol -> commodity_id mappings."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, commodity_id FROM commodities;")
    result = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return result


def replace_symbol_with_id(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces the 'symbol' column with 'commodity_id' in the DataFrame."""
    symbol_map = get_symbol_id_map()
    df['commodity_id'] = df['symbol'].map(symbol_map)
    return df.drop(columns=['symbol'])


if __name__ == "__main__":
    load_dotenv()

    # Example usage:
    data = {
        'symbol': ['GCUSD', 'DCUSD'],
        'date': ['2023-01-01', '2023-01-02'],
        'open': [1800.0, 25.0],
        'high': [1820.0, 26.0],
        'low': [1790.0, 24.5],
        'close': [1810.0, 25.5],
        'volume': [1000, 2000],
        'change': [10.0, 0.5],
        'changePercent': [0.55, 2.0],
        'vwap': [1805.0, 25.25]
    }
    df = pd.DataFrame(data)

    df = change_date_column_to_timestamp(df)
    df = remove_vwap_column(df)
    df = change_column_names(df)
    df = replace_symbol_with_id(df)

    print(df)
