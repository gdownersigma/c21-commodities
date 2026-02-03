"""Main ETL pipeline orchestrating extract, transform, and load steps."""
from dotenv import load_dotenv

from extract import loop_commodities
from transform import apply_transformations
from load import insert_into_db


def run_pipeline() -> None:
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


def handler(event, context):
    """AWS Lambda handler function."""
    load_dotenv()
    run_pipeline()


if __name__ == "__main__":
    load_dotenv()
    run_pipeline()
