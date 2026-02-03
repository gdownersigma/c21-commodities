"""A script to hold utility functions for data extraction from FMP API
to be used in the pipeline."""
from os import environ as ENV
import requests as req
import pandas as pd
from dotenv import load_dotenv

DEFAULT_SYMBOLS = symbols = [
    "BZUSD",  # Brent Crude Oil
    "SIUSD",  # Silver
    "GCUSD",  # Gold
]


def get_commodity_data(symbol: str) -> pd.DataFrame:
    """Fetches commodity data from FMP API for a given symbol."""
    base_url = "https://financialmodelingprep.com/stable/quote"
    api_key = ENV.get("API_KEY")
    if not api_key:
        raise ValueError(
            "API_KEY not found in environment. Did you load .env?")
    url = f"{base_url}?symbol={symbol}&apikey={api_key}"
    response = req.get(url, timeout=5)
    if response.status_code != 200:
        print(f"Error for {symbol}: {response.text}")
        return pd.DataFrame()
    data = response.json()
    return pd.DataFrame(data)


def loop_commodities() -> pd.DataFrame:
    """Loops through a list of commodity symbols and fetches their data."""
    all_data = pd.DataFrame()
    for symbol in DEFAULT_SYMBOLS:
        df = get_commodity_data(symbol)
        all_data = pd.concat([all_data, df], ignore_index=True)
    return all_data


if __name__ == "__main__":
    load_dotenv()
    df = loop_commodities()
    print(df)
