"""Script to transform record data ready for upload."""
# pylint: disable=redefined-outer-name
import logging
from os import environ as ENV
import pandas as pd
import numpy as np
from psycopg2 import connect
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from a CSV file into a DataFrame."""
    logger.info("Loading data from %s", file_path)
    df = pd.read_csv(file_path)
    logger.info("Loaded %d records from %s", len(df), file_path)
    return df


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    logger.debug("Establishing database connection")
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    logger.debug("Database connection established successfully")
    return conn


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renames columns in the DataFrame based on the provided mapping."""
    logger.debug("Renaming columns")
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
        "priceAvg200": "price_avg_200"

    }
    return df.rename(columns=columns_map)


def unix_to_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Converts a UNIX timestamp column to datetime format."""
    logger.debug(
        "Converting %s column from UNIX timestamp to datetime", column)
    # convert from seconds since epoch and cast to seconds precision
    df[column] = pd.to_datetime(df[column], unit='s').astype('datetime64[s]')
    return df


def remove_dead_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Removes specified dead columns from the DataFrame."""
    dead_columns = ["marketCap", "exchange", "name"]
    logger.debug("Removing dead columns: %s", dead_columns)
    return df.drop(columns=dead_columns, errors='ignore')


def create_ingested_column(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an 'ingested_at' column with the current timestamp."""
    logger.debug("Creating ingested_at column")
    # set ingestion time with seconds precision to match `recorded_at`
    ts = np.datetime64('now', 's')
    df['ingested_at'] = pd.Series(ts, index=df.index, dtype='datetime64[s]')
    return df


def get_symbol_id_map() -> dict:
    """Fetch all symbol -> commodity_id mappings."""
    logger.info("Fetching symbol to commodity_id mappings")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, commodity_id FROM commodities;")
    result = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    logger.info("Fetched %d symbol mappings", len(result))
    return result


def replace_symbol_with_id(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces the 'symbol' column with 'commodity_id' in the DataFrame."""
    logger.debug("Replacing symbol column with commodity_id")
    symbol_map = get_symbol_id_map()
    df['commodity_id'] = df['symbol'].map(symbol_map)
    return df.drop(columns=['symbol'])


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorders DataFrame columns to match the target schema."""
    logger.debug("Reordering columns to match target schema")
    column_order = [
        "commodity_id",
        "recorded_at",
        "price",
        "volume",
        "day_high",
        "day_low",
        "change",
        "change_percentage",
        "open_price",
        "previous_close",
        "price_avg_50",
        "price_avg_200",
        "year_high",
        "year_low",
        "ingested_at",
    ]
    return df[column_order]


def apply_transformations(df: pd.DataFrame) -> pd.DataFrame:
    """Applies all transformation functions to the DataFrame."""
    logger.info("Starting data transformations on %d records", len(df))
    df = rename_columns(df)
    df = unix_to_datetime(df, "recorded_at")
    df = remove_dead_columns(df)
    df = create_ingested_column(df)
    df = replace_symbol_with_id(df)
    df = reorder_columns(df)
    logger.info("Completed all transformations, %d records processed", len(df))
    return df


if __name__ == "__main__":
    load_dotenv()
    logger.info("Starting transformation script")
    df = load_data("dirty_commodity_data.csv")
    df = apply_transformations(df)
    df.to_csv("clean_commodity_data.csv", index=False)
    logger.info(
        "Transformation complete. Data saved to clean_commodity_data.csv")
