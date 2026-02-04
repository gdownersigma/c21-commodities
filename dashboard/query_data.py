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


def load_query(filename: str) -> str:
    """Load a SQL query from a file."""
    with open(f"queries/{filename}", 'r') as f:
        return f.read().strip()


@st.cache_data(ttl=600)
def get_commodity_data_by_ids(_conn: connection, ids: list) -> pd.DataFrame:
    """Return commodity data from the database."""

    query = sql.SQL(load_query("get_commodity_data_by_ids.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (tuple(ids),))

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=600)
def get_user_count_by_email(_conn: connection, email: str) -> dict:
    """Return count of user with the given email."""

    query = sql.SQL(load_query("get_user_count_by_email.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (email,))

        return cur.fetchone()["user_count"]


@st.cache_data(ttl=600)
def get_user_by_email_password(_conn: connection, email: str, hashed_password: bytes) -> dict:
    """Return user data from the database based on email and hashed password."""

    query = sql.SQL(load_query("get_user_by_email_password.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (email, hashed_password))

        data = cur.fetchone()

        if data:
            return dict(data)
        else:
            return {}


@st.cache_data(ttl=600)
def create_user(_conn: connection, field_input: dict):
    """Insert a new user into the database."""

    query = sql.SQL(load_query("create_user.sql"))

    with _conn.cursor() as cur:
        cur.execute(
            query, (field_input["name"],
                    field_input["email"],
                    field_input["hashed_password"]))

    _conn.commit()


@st.cache_data(ttl=600)
def get_users_subscribed_commodities(_conn: connection, email: str) -> list[int]:
    """Return a user's subscribed commodities from the database."""

    query = sql.SQL(load_query("get_users_subscribed_commodities.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (email,))

        data = cur.fetchall()

    return [item["commodity_id"] for item in data]


if __name__ == "__main__":

    load_dotenv()

    conn = get_connection(ENV)

    # commodity_ids = [1, 2, 3]

    # df = get_commodity_data_by_ids(conn, commodity_ids)

    data = get_users_subscribed_commodities(conn, "bob.wilson@example.com")
    print(data)
