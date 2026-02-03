"""This is a script that extract historical financial data from an API."""

import requests
from os import environ as ENV
import pandas as pd
from dotenv import load_dotenv


def fetch_historical_data(symbol: str) -> pd.DataFrame:
    """Fetches historical financial data for specified symbol from the given API URL from the last 30 days from today."""
    API_KEY = ENV.get("API_KEY")
    API_URL = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(API_URL, timeout=5)
    data = response.json()
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    last_30_days = pd.Timestamp.now() - pd.Timedelta(days=30)
    df = df[df['date'] >= last_30_days]
    return df
