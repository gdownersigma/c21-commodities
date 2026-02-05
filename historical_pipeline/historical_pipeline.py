"""This a script that extracts, transforms, and loads commodity data from the past 30 days."""

import logging
import pandas as pd
from dotenv import load_dotenv

from historical_extract import fetch_historical_data
from historical_transform import change_date_column_to_timestamp, remove_vwap_column, change_column_names, replace_symbol_with_id
from historical_load import load_data_to_db


def extract(symbol: str) -> pd.DataFrame:
    """Extract historical data for the past 30 days for a specific symbol."""
    logging.info(f"Starting data extraction for {symbol}...")
    df = fetch_historical_data(symbol)
    logging.info("Data extraction completed.")
    return df

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform the extracted data to match the database schema."""
    logging.info("Starting data transformation...")
    df = change_date_column_to_timestamp(df)
    df = remove_vwap_column(df)
    df = change_column_names(df)
    df = replace_symbol_with_id(df)

    logging.info("Data transformation completed.")
    return df

def load(df: pd.DataFrame):
    """Load the transformed data into the PostgreSQL database."""
    logging.info("Starting data loading...")
    load_data_to_db(df)
    logging.info("Data loading completed.")

def handler(event, context):
    """AWS Lambda handler function."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    
    symbol = event.get("symbol")
    if not symbol:
        return {"statusCode": 400, "body": "Missing required parameter: symbol"}
    
    df_extracted = extract(symbol)
    df_transformed = transform(df_extracted)
    load(df_transformed)
    return {"statusCode": 200, "body": f"Historical pipeline completed successfully for {symbol}"}

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    # For local testing, provide a symbol
    test_symbol = "GCUSD"
    df_extracted = extract(test_symbol)
    df_transformed = transform(df_extracted)
    load(df_transformed)