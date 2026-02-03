"""A script to hold utility functions for data extraction from FMP API
to be used in the pipeline."""

import requests as req
import pandas as pd
from os import environ as ENV
import dotenv

# need functions to get one piece of data when given a commodity symbol


def get_commodity_data(symbol: str, data_type: str) -> pd.DataFrame:
