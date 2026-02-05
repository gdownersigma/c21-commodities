"""Script to load the transformed data into the database."""
import logging
from os import environ as ENV
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    logger.debug("Establishing database connection")
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    logger.debug("Database connection established successfully")
    return conn


def load_data(file_path: str) -> pd.DataFrame:
    """Loads data from a CSV file into a DataFrame."""
    logger.info("Loading data from %s", file_path)
    df = pd.read_csv(file_path)
    logger.info("Loaded %d records from %s", len(df), file_path)
    return df


def insert_into_db(df: pd.DataFrame):
    """Inserts the DataFrame data into the specified database table."""
    logger.info("Starting database insert for %d records", len(df))
    conn = get_conn()
    cursor = conn.cursor()

    query = """
        INSERT INTO market_records (
            commodity_id, recorded_at, price, volume, day_high, day_low,
            change, change_percentage, open_price, previous_close,
            price_avg_50, price_avg_200, year_high, year_low, ingested_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    rows = [tuple(row) for row in df.itertuples(index=False)]
    logger.debug("Executing batch insert")
    execute_batch(cursor, query, rows)

    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Successfully inserted %d records into market_records", len(df))


if __name__ == "__main__":
    load_dotenv()
    logger.info("Starting load script")
    df = load_data("clean_commodity_data.csv")
    insert_into_db(df)
    logger.info("Load script completed successfully")
