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
def get_users_commodity_ids(_conn: connection, user_id: str) -> list[int]:
    """Return a user's subscribed commodities from the database."""

    query = sql.SQL(load_query("get_users_commodity_ids.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (user_id,))

        data = cur.fetchall()

    return [item["commodity_id"] for item in data]


@st.cache_data(ttl=600)
def get_commodities_with_user_subscriptions(_conn: connection, user_id: str) -> dict:
    """Return a user's subscribed commodities from the database."""

    query = sql.SQL(load_query("get_commodities_with_user_subscriptions.sql"))

    with _conn.cursor() as cur:
        cur.execute(query, (user_id,))

        data = cur.fetchall()

    new_data = {}
    for item in data:
        new_data[item["commodity_id"]] = {
            "name": item["commodity_name"],
            "track": item["user_id"] is not None,
            "buy": item["buy_price"] != 0,
            "sell": item["sell_price"] != 0,
            "buy_price": item["buy_price"],
            "sell_price": item["sell_price"]
        }

    return new_data


@st.cache_data(ttl=600)
def create_user(_conn: connection, field_input: dict) -> int:
    """Insert a new user into the database."""

    query = sql.SQL(load_query("create_user.sql"))

    with _conn.cursor() as cur:
        cur.execute(
            query, (field_input["name"],
                    field_input["email"],
                    field_input["hashed_password"]))

        user_id = cur.fetchone()["user_id"]

    _conn.commit()
    return user_id


@st.cache_data(ttl=600)
def create_commodity_connections(_conn: connection, comm_data: list[dict]):
    """Create connections between a user and multiple commodities."""

    query = sql.SQL(load_query("create_commodity_connections.sql"))

    with _conn.cursor() as cur:
        data = [(item["user_id"], item["commodity_id"],
                 item["buy_price"], item["sell_price"]) for item in comm_data]
        cur.executemany(query, data)

    _conn.commit()


if __name__ == "__main__":

    load_dotenv()

    conn = get_connection(ENV)

    data = get_commodities_with_user_subscriptions(conn, 16)
    print(data)

    conn.close()
