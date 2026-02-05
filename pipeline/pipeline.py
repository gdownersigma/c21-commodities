"""Main ETL pipeline orchestrating extract, transform, and load steps."""
import logging
from dotenv import load_dotenv

from extract import loop_commodities
from transform import apply_transformations
from load import insert_into_db
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline() -> pd.DataFrame:
    """Run the full ETL pipeline: extract → transform → load."""
    logger.info("Starting ETL pipeline...")

    # Extract: fetch commodity data from FMP API
    logger.info("Extracting data from API...")
    raw_df = loop_commodities()
    logger.info("Extracted %d records", len(raw_df))

    if raw_df.empty:
        logger.warning("No data extracted. Exiting pipeline.")
        return

    # Transform: clean and reshape data
    logger.info("Transforming data...")
    clean_df = apply_transformations(raw_df)
    logger.info("Transformed %d records", len(clean_df))

    # Load: insert into database
    logger.info("Loading data into database...")
    insert_into_db(clean_df)
    logger.info("Loaded %d records", len(clean_df))

    logger.info("ETL pipeline complete.")
    return clean_df


def handler(event, context):
    """AWS Lambda handler function."""
    logger.info("Lambda handler invoked")
    load_dotenv()
    clean_df = run_pipeline()
    df_dict = clean_df[["commodity_id", "price"]].to_dict(orient="records")
    logger.info("Lambda handler completed successfully")
    return {"statusCode": 200, "body": df_dict}


if __name__ == "__main__":
    load_dotenv()
    logger.info("Running pipeline from main")
    run_pipeline()
    logger.info("Pipeline execution finished")
