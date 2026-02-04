"""This a script that extracts, transform and loads commodity data from the past 30 days."""

import logging
import pandas as pd

from historical_extract import fetch_historical_data
from historical_transform import change_date_column_to_timestamp, remove_vwap_column, change_column_names, get_conn, get_symbol_id_map, replace_symbol_with_id
from historical_load import load_data_to_db


def extract() -> pd.DataFrame:
    """Extract historical data for the past 30 days."""
    logging.info("Starting data extraction...")
    df = fetch_historical_data()
    logging.info("Data extraction completed.")
    return df

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform the extracted data to match the database schema."""
    logging.info("Starting data transformation...")
    df = change_date_column_to_timestamp(df)
    df = remove_vwap_column(df)
    df = change_column_names(df)

    symbol_id_map = get_symbol_id_map()
    df = replace_symbol_with_id(df, symbol_id_map)

    logging.info("Data transformation completed.")
    return df

def load(df: pd.DataFrame):
    """Load the transformed data into the PostgreSQL database."""
    logging.info("Starting data loading...")
    load_data_to_db(df)
    logging.info("Data loading completed.")

def handler(event, context):
    """AWS Lambda handler function."""
    logging.basicConfig(level=logging.INFO)
    df_extracted = extract()
    df_transformed = transform(df_extracted)
    load(df_transformed)
    return {"statusCode": 200, "body": "Historical pipeline completed successfully"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df_extracted = extract()
    df_transformed = transform(df_extracted)
    load(df_transformed)