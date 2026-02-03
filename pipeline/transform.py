"""Script to transform record data ready for upload."""
from os import environ as ENV
import pandas as pd
import numpy as np
from psycopg2 import connect
from dotenv import load_dotenv


def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from a CSV file into a DataFrame."""
    return pd.read_csv(file_path)


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


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renames columns in the DataFrame based on the provided mapping."""
    columns_map = {
        "timestamp": "recorded_at",
        "dayHigh": "day_high",
        "dayLow": "day_low",
        "yearHigh": "year_high",
        "yearLow": "year_low",
        "changePercentage": "change_percentage",
        "open": "open_price",
        "previousClose": "previous_close",
        "priceAvg50": "price_avg_50",
        "priceAvg200": "price_avg_200",

    }
    return df.rename(columns=columns_map)


def unix_to_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Converts a UNIX timestamp column to datetime format."""
    # convert from seconds since epoch and cast to seconds precision
    df[column] = pd.to_datetime(df[column], unit='s').astype('datetime64[s]')
    return df


def remove_dead_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Removes specified dead columns from the DataFrame."""
    dead_columns = ["marketCap", "exchange"]
    return df.drop(columns=dead_columns, errors='ignore')


def create_ingested_column(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an 'ingested_at' column with the current timestamp."""
    # set ingestion time with seconds precision to match `recorded_at`
    ts = np.datetime64('now', 's')
    df['ingested_at'] = pd.Series(ts, index=df.index, dtype='datetime64[s]')
    return df


def comm_id_lookup(symbol: str) -> int:
    """Looks up the commodity ID for a given symbol."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM commodities WHERE symbol = %s;", (symbol,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return result[0]
    else:
        raise ValueError(f"Symbol {symbol} not found in database.")


if __name__ == "__main__":
    df = load_data("commodity_data.csv")
    df = rename_columns(df)
    df = unix_to_datetime(df, "recorded_at")
    df = remove_dead_columns(df)
    df = create_ingested_column(df)
    print(df.dtypes)
