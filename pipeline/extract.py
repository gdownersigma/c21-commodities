"""A script to hold utility functions for data extraction from FMP API
to be used in the pipeline."""
import logging
from os import environ as ENV
import requests as req
import pandas as pd
from dotenv import load_dotenv
from psycopg2 import connect

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = symbols = [
    "BZUSD",  # Brent Crude Oil
    "SIUSD",  # Silver
    "GCUSD",  # Gold
]


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


def fetch_commodity_ids():
    """Fetch distinct commodity IDs from user_commodities table."""
    logger.info("Fetching commodity IDs from user_commodities table")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT commodity_id FROM user_commodities;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info("Fetched %d commodity IDs", len(rows))
    return [row[0] for row in rows]


def fetch_symbols_by_ids(ids: list) -> list:
    """Fetch commodity symbols for given IDs."""
    logger.info("Fetching symbols for %d commodity IDs", len(ids))
    symbols = []
    conn = get_conn()
    for commodity_id in ids:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT symbol FROM commodities WHERE commodity_id = %s;", (commodity_id,))
        symbol = cursor.fetchone()[0]
        symbols.append(symbol)
        logger.debug("Fetched symbol %s for commodity_id %s",
                     symbol, commodity_id)
        cursor.close()
    conn.close()
    logger.info("Fetched %d symbols", len(symbols))
    return symbols


def combine_symbols(user_symbols: list) -> set:
    """Combine user symbols with defaults and return unique set."""
    return set(user_symbols + DEFAULT_SYMBOLS)


def get_tracked_symbols() -> list:
    """Returns the list of commodity symbols tracked by users."""
    logger.info("Getting tracked symbols")
    ids = fetch_commodity_ids()
    user_symbols = fetch_symbols_by_ids(ids)
    combined = combine_symbols(user_symbols)
    logger.info("Total tracked symbols: %d", len(combined))
    return combined


def get_commodity_data(symbol: str) -> pd.DataFrame:
    """Fetches commodity data from FMP API for a given symbol."""
    logger.info("Fetching data for symbol: %s", symbol)
    base_url = "https://financialmodelingprep.com/stable/quote"
    api_key = ENV.get("API_KEY")
    if not api_key:
        logger.error("API_KEY not found in environment")
        raise ValueError(
            "API_KEY not found in environment. Did you load .env?")
    url = f"{base_url}?symbol={symbol}&apikey={api_key}"
    response = req.get(url, timeout=5)
    if response.status_code != 200:
        logger.error("Error fetching data for %s: %s", symbol, response.text)
        return pd.DataFrame()
    data = response.json()
    logger.debug("Successfully fetched data for %s", symbol)
    return pd.DataFrame(data)


def loop_commodities() -> pd.DataFrame:
    """Loops through a list of commodity symbols and fetches their data."""
    logger.info("Starting to loop through commodities")
    all_data = pd.DataFrame()
    symbols = get_tracked_symbols()
    for symbol in symbols:
        df = get_commodity_data(symbol)
        all_data = pd.concat([all_data, df], ignore_index=True)
    logger.info("Completed fetching data for %d commodities, total records: %d", len(
        symbols), len(all_data))
    return all_data


if __name__ == "__main__":
    load_dotenv()
    logger.info("Starting extraction script")
    df = loop_commodities()
    logger.info("Extraction complete. DataFrame shape: %s", df.shape)
    df.to_csv("dirty_commodity_data.csv", index=False)
    logger.info("Data saved to dirty_commodity_data.csv")
