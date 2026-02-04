"""This is a script that extracts historical financial data from an API."""

import requests
from os import environ as ENV
import pandas as pd
from dotenv import load_dotenv


def fetch_historical_data(symbol: str) -> pd.DataFrame:
    """Fetches historical financial data for specified symbol from the given API URL from the last 30 days from today."""
    API_KEY = ENV.get("API_KEY")
    from_date = (pd.Timestamp.today() -
                 pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    to_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    API_URL = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}&apikey={API_KEY}&from={from_date}&to={to_date}"
    response = requests.get(API_URL)
    data = response.json()
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    load_dotenv()
    df = fetch_historical_data("DCUSD")
    print(df)
