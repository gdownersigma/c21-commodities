"""File to query the PostgreSQL database for data."""

from os import _Environ, environ as ENV
from dotenv import load_dotenv

import streamlit as st
import pandas as pd
from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection


def get_connection(config: _Environ) -> connection:
    """Return a connection to the PostgreSQL database."""
    return connect(
        dbname=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        cursor_factory=RealDictCursor
    )


def query_database(conn: connection, query: str, parameters: tuple = None) -> pd.DataFrame:
    """Returns a query result."""

    with conn.cursor() as cur:
        if parameters:
            cur.execute(query, parameters)
        else:
            cur.execute(query)

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=600)
def get_commodity_data_by_ids(_conn: connection, ids: list) -> pd.DataFrame:
    """Return commodity data from the database."""

    query = sql.SQL("""
        SELECT *
        FROM commodities
        WHERE commodity_id IN %s;
    """)

    return query_database(_conn, query, (tuple(ids),))


if __name__ == "__main__":

    load_dotenv()

    conn = get_connection(ENV)

    commodity_ids = [1, 2, 3]

    df = get_commodity_data_by_ids(conn, commodity_ids)
    print(df.head())
