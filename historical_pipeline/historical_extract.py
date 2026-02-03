"""This is a script that extract historical financial data from an API."""

import requests
from os import environ as ENV
import pandas as pd
from dotenv import load_dotenv

API_KEY =
API_URL = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=GCUSD&apikey={API_KEY}"
