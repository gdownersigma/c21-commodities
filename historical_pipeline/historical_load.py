"""This script loads historical financial data into the PostgreSQL database."""

import pandas as pd
from psycopg2 import connect
from psycopg2.extras import execute_values
from os import environ as ENV
from dotenv import load_dotenv


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


def load_data_to_db(df: pd.DataFrame):
    """Load DataFrame into the market_records table."""
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Create a list of tuples from the DataFrame values
        tuples = [tuple(x) for x in df.to_numpy()]

        # Create the INSERT INTO SQL query
        cols = ','.join(list(df.columns))
        query = f"INSERT INTO market_records ({cols}) VALUES %s"

        # Use execute_values to insert the data
        execute_values(cursor, query, tuples)

        conn.commit()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    data = {
        'recorded_at': ['2023-01-01', '2023-01-02'],
        'open_price': [1800.0, 25.0],
        'day_high': [1820.0, 26.0],
        'day_low': [1790.0, 24.5],
        'price': [1810.0, 25.5],
        'volume': [1000, 2000],
        'change': [10.0, 0.5],
        'change_percentage': [0.55, 2.0],
        'commodity_id': [18, 1]
    }
    df = pd.DataFrame(data)
    load_data_to_db(df)
