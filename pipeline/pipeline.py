"""Main ETL pipeline orchestrating extract, transform, and load steps."""
from dotenv import load_dotenv

from extract import loop_commodities
from transform import apply_transformations
from load import insert_into_db
import pandas as pd


def run_pipeline() -> pd.df:
    """Run the full ETL pipeline: extract → transform → load."""
    print("Starting ETL pipeline...")

    # Extract: fetch commodity data from FMP API
    print("Extracting data from API...")
    raw_df = loop_commodities()
    print(f"  Extracted {len(raw_df)} records")

    if raw_df.empty:
        print("No data extracted. Exiting pipeline.")
        return

    # Transform: clean and reshape data
    print("Transforming data...")
    clean_df = apply_transformations(raw_df)
    print(f"  Transformed {len(clean_df)} records")

    # Load: insert into database
    print("Loading data into database...")
    insert_into_db(clean_df)
    print(f"  Loaded {len(clean_df)} records")

    print("ETL pipeline complete.")
    return clean_df


def handler(event, context):
    """AWS Lambda handler function."""
    load_dotenv()
    clean_df = run_pipeline()
    df_dict = clean_df[["commodity_id", "price"]].to_dict(orient="records")
    return {"statusCode": 200, "body": df_dict}


if __name__ == "__main__":
    load_dotenv()
    run_pipeline()
